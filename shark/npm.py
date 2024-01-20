from . import github, search, clean
from collections import defaultdict
from pathlib import Path
import json
import aiofiles
import aiohttp
import asyncio
import shlex

async def process_results_git(path, git_results):
    json_data = [await search.package_json_results(path, value['value']) for _, value in git_results.items()]

    new_json_data = []
    for item in json_data:
        item_dict = json.loads(item)
        for entry in item_dict:
            matching_key = list(filter(lambda x: x[1]['value'] == entry['value'], git_results.items()))[0][0]

            entry['package'] = matching_key
            entry['user'] = git_results[matching_key]['user']
            entry['vulnerability'] = "npm package pulling from GitHub source where the username is available to be registered."
            entry['type'] = "npm github"

            new_json_data.append(entry)

    return new_json_data

async def find_package_json(directory: str) -> list:
    packages = defaultdict(set)
    badvalues = ["workspace:",
                "file:",
                "npm:",
                "git+",
                "github:",
                "https://github",
                "./",
                "git://",
                "/",
                "link:"]
    
    async def process_file(file_path: Path) -> None:
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
            for key in ('dependencies', 'devDependencies'):
                dependencies = data.get(key, {})
                for k, v in dependencies.items():
                    if not any(badvalue in v for badvalue in badvalues):
                        packages[key].add(k)
    
    directory = Path(directory).resolve()
    tasks = [asyncio.create_task(process_file(file)) for file in directory.rglob('package.json')]
    await asyncio.gather(*tasks)
    return list(packages['dependencies'].union(packages['devDependencies']))

async def find_package_json_git(directory: str) -> list:
    packages = []
    goodvalues = ["git",
                  "/",
                  "github"]
    
    async def process_file(file_path: Path) -> None:
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
            for key in ('dependencies', 'devDependencies'):
                dependencies = data.get(key, {})
                for k, v in dependencies.items():
                    if any(goodvalue in v for goodvalue in goodvalues):
                        packages.append((k, v))
    
    directory = Path(directory).resolve()
    tasks = [asyncio.create_task(process_file(file)) for file in directory.rglob('package.json')]
    await asyncio.gather(*tasks)
    return list(set(packages))

async def scan_package_values(directory: str) -> dict:
    check_list = await find_package_json_git(directory)
    git_values = [value for _, value in check_list]
    
    unique_values = set()

    for value in git_values:
        user = github.return_user(value)
        if user:
            unique_values.add(user)

    gh_users = list(unique_values)

    tasks = [github.check_github_user(user) for user in gh_users]
    results = await asyncio.gather(*tasks)

    results_dict = {}

    for user, result in zip(gh_users, results):
        for k, v in check_list:
            if user == github.return_user(v) and result:
                results_dict[k] = {"value": v, "user": user}

    json_results = await process_results_git(directory, results_dict)
    return json_results

def read_npm_search_json(path: str) -> list:
    matches = defaultdict(set)

    with open(f"{path}/npm_search.json", 'r', encoding='utf-8') as f:
        for line in f:
            match_dict = json.loads(line.strip())
            matches[match_dict['match']]

    matches_list = list(matches.keys())
    return clean.search(matches_list)

async def scan_packages(path, package):
    command = f"npm view '{package}'"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    resp = await process.stderr.read()

    results = []

    if "is not in this registry" in resp.decode('utf-8'):
        data = await search.package_json_results(path, package)
        results.append(json.loads(data))
        search_data = await search.package_search_json_results(f"{path}/npm_search.json", package)
        results.extend(search_data)
    return results

async def scope_available(path, scope):
    command = f"npm search '{scope}'"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    resp = await process.stdout.read()

    results = []

    if "No matches found" in resp.decode('utf-8'):
        if await scope_404(scope):
            data = await search.package_json_results(path, scope)
            results.append(json.loads(data))
            search_data = await search.package_search_json_results(f"{path}/npm_search.json", scope)
            results.extend(search_data)
    return results

async def scope_404(scope):
    url = f'https://npmjs.com/~{scope.split('@')[1]}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 404:
                return True
            else:
                return False