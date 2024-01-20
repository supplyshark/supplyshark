from . import github, search
from pathlib import Path
import asyncio
import aiofiles
import json

async def find_go_mod(directory: Path) -> list:
    packages = []

    async def process_file(file_path: Path) -> None:
        async with aiofiles.open(file_path, "r") as f:
            data = await f.readlines()
            for l in data:
                line = l.strip()
                if line.startswith("github.com"):
                    packages.append(line)
    
    directory = Path(directory).resolve()
    tasks = [asyncio.create_task(process_file(file)) for file in directory.rglob('go.mod')]
    await asyncio.gather(*tasks)
    return list(set(packages))

async def process_results_git(path, git_results):
        json_data = [await search.go_mod_results(path, k) for k, _ in git_results.items()]

        new_json_data = []
        for item in json_data:
            item_dict = json.loads(item)
            for entry in item_dict:
                matching_key = list(filter(lambda x: x[0] == entry['value'], git_results.items()))[0][0]

                entry['package'] = matching_key
                entry['user'] = git_results[matching_key]['user']

            new_json_data.append(entry)

        return new_json_data

async def scan_go(path: Path):
    git_values = await find_go_mod(path)

    unique_values = set()

    for value in git_values:
        user = github.return_user_regular(value)
        if user:
            unique_values.add(user)
    
    gh_users = list(unique_values)

    tasks = [github.check_github_user(user) for user in gh_users]
    results = await asyncio.gather(*tasks)

    results_dict = {}

    for user, result in zip(gh_users, results):
        for v in git_values:
            if user == github.return_user_regular(v) and result:
                results_dict[v] = {"user": user}
    
    json_results = await process_results_git(path, results_dict)
    return json_results