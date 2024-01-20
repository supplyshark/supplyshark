from . import github, search
from pathlib import Path
import asyncio
import aiofiles
import tomllib
import json

async def find_cargo_toml(directory: Path) -> list:
    packages = []

    async def process_file(file_path: Path) -> None:
        async with aiofiles.open(file_path, "r") as f:
            data = tomllib.loads(await f.read())
            for k, v in data["dependencies"].items():
                if "git" in v:
                    packages.append((k, v['git']))
    
    directory = Path(directory).resolve()
    tasks = [asyncio.create_task(process_file(file)) for file in directory.rglob('Cargo.toml')]
    await asyncio.gather(*tasks)
    return list(set(packages))

async def process_results_git(path, git_results):
        json_data = [await search.cargo_toml_results(path, value['value']) for _, value in git_results.items()]

        new_json_data = []
        for item in json_data:
            item_dict = json.loads(item)
            for entry in item_dict:
                matching_key = list(filter(lambda x: x[1]['value'] == entry['value'], git_results.items()))[0][0]

                entry['package'] = matching_key
                entry['user'] = git_results[matching_key]['user']
                entry['vulnerability'] = "cargo package pulling from GitHub source where the username is available to be registered."
                entry['type'] = "cargo github"

            new_json_data.append(entry)

        return new_json_data

async def scan_cargo(path: Path):
    check_list = await find_cargo_toml(path)
    git_values = [value for _, value in check_list]

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
        for k, v in check_list:
            if user == github.return_user_regular(v) and result:
                results_dict[k] = {"value": v, "user": user}
    
    json_results = await process_results_git(path, results_dict)
    return json_results