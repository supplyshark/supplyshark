from pathlib import Path
from sys import exit
import asyncio
import shark
import json

async def npm(copy_dir, sem, super_sem):
    async with sem:
        newlist = await shark.npm.find_package_json(copy_dir)

    package_list = list(set(newlist + shark.npm.read_npm_search_json(copy_dir)))

    async with super_sem:
        package_results = await asyncio.gather(*[
            shark.npm.scan_packages(copy_dir, package)
            for package in package_list
            if not package.startswith("@")
        ])
        package_results = [result for result in package_results if result is not None and result]

    scope_list = list(set(scope.split("/")[0] for scope in package_list if scope.startswith("@")))

    async with super_sem:
        scope_results = await asyncio.gather(*[
            shark.npm.scope_available(copy_dir, scope)
            for scope in scope_list
        ])
        scope_results = [result for result in scope_results if result is not None and result]

    async with sem:
        git_results = await shark.npm.scan_package_values(copy_dir)
        git_results = [result for result in git_results if result is not None and result]

    combined_results = json.dumps({
        "package_results": package_results,
        "scope_results": scope_results,
        "git_results": git_results
    })

    print(combined_results)


async def gem(copy_dir, super_sem):
    gem_list = list(set(shark.gem.read_gem_search_json(copy_dir)))

    async with super_sem:
        package_results = await asyncio.gather(*[
            shark.gem.scan_gems(copy_dir, gem)
            for gem in gem_list
        ])
        package_results = [result for result in package_results if result is not None and result]
    
    results = json.dumps({
        "package_results": package_results
    })

    print(results)

async def pip(copy_dir, sem, super_sem):
    async with sem:
        piplist = await shark.pip.find_requirements_txt(copy_dir)

    pip_list = list(set(piplist + shark.pip.read_pip_search_json(copy_dir)))

    async with super_sem:
        package_results = await asyncio.gather(*[
            shark.pip.scan_packages(copy_dir, package)
            for package in pip_list
        ])
        package_results = [result for result in package_results if result is not None and result]
    
    results = json.dumps({
        "package_results": package_results
    })

    print(results)

async def cargo(copy_dir, sem):
    async with sem:
        git_results = await shark.cargo.scan_cargo(copy_dir)
        git_results = [result for result in git_results if result is not None and result]
    
    results = json.dumps({
        "git_results": git_results
    })

    print(results)

async def go(copy_dir, sem):
    async with sem:
        git_results = await shark.go.scan_go(copy_dir)
        git_results = [result for result in git_results if result is not None and result]
    
    results = json.dumps({
        "git_results": git_results
    })

    print(results)

async def start(subscription, settings):
    id = settings['installation_id']
    token = await shark.github.get_access_token(id)

    account = settings['account_name']
    repos = settings['repositories']
    forked = settings['forked']
    archived = settings['archived']

    tmp = f"/tmp/.supplyshark/{account}"
    copy_dir = f"/tmp/.supplyshark/_output/{account}"
    Path(tmp, copy_dir).mkdir(parents=True, exist_ok=True)

    sem = asyncio.Semaphore(10)
    super_sem = asyncio.Semaphore(50)
    repo_queue = []
    paths = []

    async with sem:
        gh_check = await asyncio.gather(*[
            shark.github.check_github_repo(token, account, repo)
            for repo in repos
        ])

    for repo, _is in zip(repos, gh_check):
        if subscription != "premium":
            if not _is['repo_private'] and not _is['repo_archived'] and not _is['repo_forked']:
                repo_queue.append(repo)
        else:
            if forked and archived:
                repo_queue.append(repo)
            elif not forked and not archived:
                if not _is['repo_forked'] and not _is['repo_archived']:
                    repo_queue.append(repo)
            elif forked and not archived:
                if not _is['repo_archived']:
                    repo_queue.append(repo)
            elif not forked and archived:
                if not _is['repo_forked']:
                    repo_queue.append(repo)

    async with sem:
        gh_download = await asyncio.gather(*[
            shark.github.gh_clone_repo(account, repo, token)
            for repo in repo_queue
        ])
        paths.extend(gh_download)

    await asyncio.gather(
        npm(copy_dir, sem, super_sem),
        gem(copy_dir, super_sem),
        pip(copy_dir, sem, super_sem),
        cargo(copy_dir, sem),
        go(copy_dir, sem)
    )
    

if __name__ == "__main__":
    runs = shark.db.get_scheduled_runs()
    if not runs:
        print("No scheduled runs today.")
        exit(0)

    for uid in runs:
        if shark.db.is_active(uid):
            settings = shark.db.fetch_user_app_settings(uid)
            subscription = shark.db.get_subscription_name(uid)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                asyncio.run(start(subscription, settings))
            except KeyboardInterrupt:
                pass