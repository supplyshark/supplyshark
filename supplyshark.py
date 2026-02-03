from colorama import Fore
from dateutil.relativedelta import relativedelta
from pathlib import Path
from shutil import rmtree
from sys import exit
import argparse
import asyncio
import datetime
import shark
import json

info_msg = f"[{Fore.LIGHTBLUE_EX}*{Fore.RESET}]"
found_msg = f"[{Fore.LIGHTGREEN_EX}+{Fore.RESET}]"
no_msg = f"[{Fore.LIGHTRED_EX}-{Fore.RESET}]"

def found_fmt(total):
    return f"{Fore.LIGHTGREEN_EX}{total}{Fore.RESET}"

async def npm(copy_dir, sem, super_sem):
    async with sem:
        newlist = await shark.npm.find_package_json(copy_dir)

    package_list = list(set(newlist + shark.npm.read_npm_search_json(copy_dir)))

    if len(package_list) == 1:
        package_msg = "package."
    else:
        package_msg = "packages."

    print(f"{info_msg} Scanning {len(package_list)} npm {package_msg}")
    
    async with super_sem:
        package_results = await asyncio.gather(*[
            shark.npm.scan_packages(copy_dir, package)
            for package in package_list
            if not package.startswith("@")
        ])
        package_results = [result for result in package_results if result is not None and result]

    total_package_results = len(package_results)

    if total_package_results == 0:
        print(f"{no_msg} Found no available npm packages.")
    else:
        total_package_results_fmt = found_fmt(total_package_results)

        if total_package_results == 1:
            package_msg = "package."
        else:
            package_msg = "packages."

        print(f"{found_msg} Found {total_package_results_fmt} available npm {package_msg}")

    scope_list = list(set(scope.split("/")[0] for scope in package_list if scope.startswith("@") and '/' in scope and not "@@" in scope and not "@json-rpc-tools" in scope))

    if len(scope_list) == 1:
        scope_msg = "scope."
    else:
        scope_msg = "scopes."

    print(f"{info_msg} Scanning {len(scope_list)} npm {scope_msg}")

    async with super_sem:
        scope_results = await asyncio.gather(*[
            shark.npm.scope_available(copy_dir, scope)
            for scope in scope_list
        ])
        scope_results = [result for result in scope_results if result is not None and result]

    total_scope_results = len(scope_results)

    if total_scope_results == 0:
        print(f"{no_msg} Found no available npm packages via available scope.")
    else:
        total_scope_results_fmt = found_fmt(total_scope_results)

        if total_scope_results == 1:
            scope_msg = "scope."
        else:
            scope_msg = "scopes."

        print(f"{found_msg} Found {total_scope_results_fmt} available {scope_msg}")
    
    print(f"{info_msg} npm scan complete.")
    
    results = {
        "package_results": package_results,
        "scope_results": scope_results
    }

    return {"npm_results": results}


async def gem(copy_dir, super_sem):
    gem_list = list(set(shark.gem.read_gem_search_json(copy_dir)))

    if len(gem_list) == 1:
        gem_msg = "gem."
    else:
        gem_msg = "gems."

    print(f"{info_msg} Scanning {len(gem_list)} {gem_msg}")

    async with super_sem:
        package_results = await asyncio.gather(*[
            shark.gem.scan_gems(copy_dir, gem)
            for gem in gem_list
        ])
        if package_results:
            package_results = [result for result in package_results if result is not None and result]
    
    total_gem_results = len(package_results)

    if total_gem_results == 0:
        print(f"{no_msg} Found no available gems.")
    else:
        total_gem_results_fmt = found_fmt(total_gem_results)

        if total_gem_results == 1:
            gem_msg = "gem."
        else:
            gem_msg = "gems."

        print(f"{found_msg} Found {total_gem_results_fmt} available {gem_msg}")

    print(f"{info_msg} gem scan complete.")

    results = {
        "package_results": package_results
    }

    return {"gem_results": results}

async def pip(copy_dir, sem, super_sem):
    async with sem:
        piplist = await shark.pip.find_requirements_txt(copy_dir)

    pip_list = list(set(piplist + shark.pip.read_pip_search_json(copy_dir)))

    if len(pip_list) == 1:
        pip_msg = "package."
    else:
        pip_msg = "packages."

    print(f"{info_msg} Scanning {len(pip_list)} python {pip_msg}")

    async with super_sem:
        package_results = await asyncio.gather(*[
            shark.pip.scan_packages(copy_dir, package)
            for package in pip_list
        ])
        package_results = [result for result in package_results if result is not None and result]
    
    total_pip_results = len(package_results)

    if total_pip_results == 0:
        print(f"{no_msg} Found no available python packages.")
    else:
        total_pip_results_fmt = found_fmt(total_pip_results)
        
        if total_pip_results == 1:
            pip_msg = "package."
        else:
            pip_msg = "packages."

        print(f"{found_msg} Found {total_pip_results_fmt} available python {pip_msg}")

    print(f"{info_msg} pip scan complete.")

    results = {
        "package_results": package_results
    }

    return {"pip_results": results}

def cleanup(copy_dir, tmp):
    rmtree(copy_dir)
    rmtree(tmp)

def create_dir(account):
    tmp = f"/tmp/.supplyshark/{account}"
    copy_dir = f"/tmp/.supplyshark/_output/{account}"
    Path(tmp).mkdir(parents=True, exist_ok=True)
    Path(copy_dir).mkdir(parents=True, exist_ok=True)
    return tmp, copy_dir

async def start_app(subscription, settings):
    id = settings['installation_id']
    token = await shark.github.get_access_token(id)

    account = settings['account_name']
    repos = settings['repositories']
    forked = settings['forked']
    archived = settings['archived']

    print(f"{info_msg} Scanning account {account}")

    tmp, copy_dir = create_dir(account)

    sem = asyncio.Semaphore(10)
    super_sem = asyncio.Semaphore(50)
    mini_sem = asyncio.Semaphore(2)
    repo_queue = []

    async with mini_sem:
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
    
    if not repo_queue:
        cleanup(copy_dir, tmp)
        return

    async with sem:
        await asyncio.gather(*[
            asyncio.to_thread(shark.github.gh_clone_repo, account, repo, token)
            for repo in repo_queue
        ])

    data = await asyncio.gather(
        npm(copy_dir, sem, super_sem),
        gem(copy_dir, super_sem)
    )

    cleanup(copy_dir, tmp)

    return json.dumps(data, indent=2), gh_check

async def start_cli(account, repo):
    tmp, copy_dir = create_dir(account)

    sem = asyncio.Semaphore(10)
    super_sem = asyncio.Semaphore(50)

    if repo:
        repo_queue = [repo]
        gh_check = []
    else:
        repo_queue, gh_check = shark.github.gh_get_repos(account)
    
    if not repo_queue:
        print(f"{no_msg} No repositories found.")
        cleanup(copy_dir, tmp)
        return None, None
    
    if len(repo_queue) == 1:
        repo_msg = "repository."
    else:
        repo_msg = "repositories."

    print(f"{info_msg} Scanning {len(repo_queue)} {repo_msg}")

    async with sem:
        await asyncio.gather(*[
            asyncio.to_thread(shark.github.cli_gh_clone_repo, account, repo)
            for repo in repo_queue
        ])

    data = await asyncio.gather(
        npm(copy_dir, sem, super_sem),
        gem(copy_dir, super_sem)
    )

    cleanup(copy_dir, tmp)

    return json.dumps(data, indent=2), gh_check

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
    recursive_lookup(data, "package")
    recursive_lookup(data, 'scope')
    return count
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", type=bool, action=argparse.BooleanOptionalAction)
    parser.add_argument("--cli", type=bool, action=argparse.BooleanOptionalAction)
    parser.add_argument("-u", type=str)
    parser.add_argument("-l", type=str)
    parser.add_argument('-r', type=str)
    args = parser.parse_args()

    if args.app:
        runs = shark.db.get_scheduled_runs()
        if not runs:
            print(f"{no_msg} No scheduled runs today.")
            exit(0)

        for uid in runs:
            if shark.db.is_active(uid):
                settings = shark.db.fetch_user_app_settings(uid)
                subscription = shark.db.get_subscription_name(uid)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    results, gh_check = asyncio.run(start_app(subscription, settings))
                except KeyboardInterrupt:
                    pass
                
                if results:
                    set_next_scan(uid)
                    new_count = shark.results.process_results(uid, results, args.app, gh_check)
                    count = get_result_count(results)
                    shark.db.insert_scan_stats(uid, count, new_count)

                    if new_count:
                        shark.integration.slack_write_alert_cust(uid, count, new_count, settings['account_name'])
                        shark.integration.slack_write_alert_home(count, new_count, settings['account_name'])
                        shark.email.send_email(uid, count, settings["account_name"])
    elif args.cli:
        if args.u is not None:
            print(f"{info_msg} Scanning account {args.u}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                results, gh_check = asyncio.run(start_cli(args.u, args.r))
            except KeyboardInterrupt:
                pass
            
            if results:
                shark.results.process_results(None, results, False, gh_check)
        else:
            with open(args.l, 'r') as f:
                for u in f.readlines():
                    print(f"{info_msg} Scanning account {u.strip()}")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        results, gh_check = asyncio.run(start_cli(u.strip(), None))
                    except KeyboardInterrupt:
                        pass
                    
                    if results:
                        shark.results.process_results(None, results, False, gh_check)
    else:
        print(f"{no_msg} Please specify --app or --cli")
        exit(0)
