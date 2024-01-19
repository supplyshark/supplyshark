from pathlib import Path
from sys import exit
import asyncio
import shark
import csv

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
    repo_queue = []
    paths = []

    async with sem:
        gh_check = [await shark.github.check_github_repo(token, account, repo) for repo in repos]

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
        gh_download = [paths.append(await shark.github.gh_clone_repo(account, repo, token)) for repo in repo_queue]

    with open(f"{copy_dir}/npm_search.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(['file', 'line', 'match'])

    async with sem:
        newlist = await shark.npm.find_package_json(copy_dir)
    
    package_list = list(set(newlist + shark.npm.read_npm_search_csv(copy_dir)))
    print(package_list)

if __name__ == "__main__":
    runs = shark.db.get_scheduled_runs()
    if len(runs) == 0:
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