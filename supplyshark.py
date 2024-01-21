from dateutil.relativedelta import relativedelta
from pathlib import Path
from shutil import rmtree
from sys import exit
import argparse
import asyncio
import datetime
import shark
import json

async def npm(copy_dir, sem, super_sem):
    async with sem:
        newlist = await shark.npm.find_package_json(copy_dir)

    package_list = list(set(newlist + shark.npm.read_npm_search_json(copy_dir)))
    print(f"[+] Analyzing {len(package_list)} npm packages")
    async with super_sem:
        package_results = asyncio.gather(*[
            shark.npm.scan_packages(copy_dir, package)
            for package in package_list
            if not package.startswith("@")
        ])
        package_results = [result for result in package_results if result is not None and result]

    scope_list = list(set(scope.split("/")[0] for scope in package_list if scope.startswith("@")))
    print(f"[+] Analyzing {len(scope_list)} scopes")

    async with super_sem:
        scope_results = await asyncio.gather(*[
            shark.npm.scope_available(copy_dir, scope)
            for scope in scope_list
        ])
        scope_results = [result for result in scope_results if result is not None and result]

    async with sem:
        git_results = await shark.npm.scan_package_values(copy_dir)
        git_results = [result for result in git_results if result is not None and result]

    results = {
        "package_results": package_results,
        "scope_results": scope_results,
        "git_results": git_results
    }

    return {"npm_results": results}


async def gem(copy_dir, super_sem):
    gem_list = list(set(shark.gem.read_gem_search_json(copy_dir)))
    print(f"[+] Analyzing {len(gem_list)} gems")

    async with super_sem:
        package_results = await asyncio.gather(*[
            shark.gem.scan_gems(copy_dir, gem)
            for gem in gem_list
        ])
        if package_results:
            package_results = [result for result in package_results if result is not None and result]
    
    results = {
        "package_results": package_results
    }

    return {"gem_results": results}

async def pip(copy_dir, sem, super_sem):
    async with sem:
        piplist = await shark.pip.find_requirements_txt(copy_dir)

    pip_list = list(set(piplist + shark.pip.read_pip_search_json(copy_dir)))
    print(f"[+] Analyzing {len(pip_list)} python packages")

    async with super_sem:
        package_results = await asyncio.gather(*[
            shark.pip.scan_packages(copy_dir, package)
            for package in pip_list
        ])
        package_results = [result for result in package_results if result is not None and result]
    
    results = {
        "package_results": package_results
    }

    return {"pip_results": results}

async def cargo(copy_dir, sem):
    async with sem:
        git_results = await shark.cargo.scan_cargo(copy_dir)
        git_results = [result for result in git_results if result is not None and result]
    
    results = {
        "git_results": git_results
    }

    return {"cargo_results": results}

async def go(copy_dir, sem):
    async with sem:
        git_results = await shark.go.scan_go(copy_dir)
        git_results = [result for result in git_results if result is not None and result]
    
    results = {
        "git_results": git_results
    }

    return {"go_results": results}

async def start_app(subscription, settings):
    id = settings['installation_id']
    token = await shark.github.get_access_token(id)

    account = settings['account_name']
    repos = settings['repositories']
    forked = settings['forked']
    archived = settings['archived']

    tmp = f"/tmp/.supplyshark/{account}"
    copy_dir = f"/tmp/.supplyshark/_output/{account}"
    Path(tmp, copy_dir).mkdir(parents=True, exist_ok=True)
    Path(f"{copy_dir}/npm_search.json").touch()
    Path(f"{copy_dir}/pip_search.json").touch()
    Path(f"{copy_dir}/gem_search.json").touch()

    sem = asyncio.Semaphore(10)
    super_sem = asyncio.Semaphore(50)
    repo_queue = []

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

    async with super_sem:
        await asyncio.gather(*[
            shark.github.gh_clone_repo(account, repo, token)
            for repo in repo_queue
        ])
    
    async with sem:
        await asyncio.gather(*[
            shark.search.get_packages(f"{tmp}/{repo}", account, repo)
            for repo in repo_queue
        ])

    data = await asyncio.gather(
        npm(copy_dir, sem, super_sem),
        gem(copy_dir, super_sem),
        pip(copy_dir, sem, super_sem),
        cargo(copy_dir, sem),
        go(copy_dir, sem)
    )

    rmtree(copy_dir)
    rmtree(tmp)

    return json.dumps(data, indent=2)

async def start_cli(account):
    print(f"[+] Starting analysis of {account}")
    tmp = f"/tmp/.supplyshark/{account}"
    copy_dir = f"/tmp/.supplyshark/_output/{account}"
    Path(tmp, copy_dir).mkdir(parents=True, exist_ok=True)
    Path(f"{copy_dir}/npm_search.json").touch()
    Path(f"{copy_dir}/pip_search.json").touch()
    Path(f"{copy_dir}/gem_search.json").touch()

    sem = asyncio.Semaphore(10)
    super_sem = asyncio.Semaphore(50)

    repo_queue = shark.github.gh_get_repos(account)
    print(f"[+] Fetched {len(repo_queue)} repos")
    
    async with super_sem:
        await asyncio.gather(*[
            shark.github.cli_gh_clone_repo(account, repo)
            for repo in repo_queue
        ])
    
    async with super_sem:
        await asyncio.gather(*[
            shark.search.get_packages(f"{tmp}/{repo}", account, repo)
            for repo in repo_queue
        ])
    
    rmtree(tmp)
    print(f"[-] /tmp/.supplyshark/{account} removed.")
    print("[+] Starting scanning.")

    data = await asyncio.gather(
        npm(copy_dir, sem, super_sem),
        gem(copy_dir, super_sem),
        pip(copy_dir, sem, super_sem),
        cargo(copy_dir, sem),
        go(copy_dir, sem)
    )

    rmtree(copy_dir)

    return json.dumps(data, indent=2)

def set_next_scan(uid):
    frequency = shark.db.get_frequency(uid)
    today = datetime.date.today()

    if frequency == "daily":
        next_scan = today + datetime.timedelta(days=1)
    elif frequency == "monthly":
        next_scan = today + relativedelta(months=1)
    elif frequency == "weekly":
        next_scan = today + datetime.timedelta(weeks=1)
    
    shark.db.update_next_scan(uid, today, next_scan)

def get_result_count(results):
    count = 0
    data = json.loads(results)

    def recursive_lookup(data, key):
        nonlocal count
        if isinstance(data, dict):
            if key in data:
                count += 1
            for value in data.values():
                recursive_lookup(value, key)
        elif isinstance(data, list):
            for item in data:
                recursive_lookup(item, key)
    recursive_lookup(data, "line_number")
    return count

def set_scan_stats(uid, results):
    count = get_result_count(results)
    shark.db.insert_scan_stats(uid, count)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=bool, action=argparse.BooleanOptionalAction)
    parser.add_argument("--cli", type=bool, action=argparse.BooleanOptionalAction)
    parser.add_argument("-u", type=str)
    parser.add_argument("-o", type=str)
    parser.add_argument("-rl", type=str)
    args = parser.parse_args()

    if args.app:
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
                    results = asyncio.run(start_app(subscription, settings))
                except KeyboardInterrupt:
                    pass

                set_next_scan(uid)
                set_scan_stats(uid, results)
                shark.results.process_results(uid, results, args.app, '')


    elif args.cli:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if args.u:
            try:
                results = asyncio.run(start_cli(args.u))
            except KeyboardInterrupt:
                pass
            shark.results.process_results('', results, False, args.o)
        elif args.rl:
            with open(args.rl, 'r') as f:
                for ff in f.readlines():
                    try:
                        results = asyncio.run(start_cli(ff.strip()))
                    except KeyboardInterrupt:
                        pass
                    shark.results.process_results('', results, False, args.o)