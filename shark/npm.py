from . import search, clean
from collections import defaultdict
from pathlib import Path
import json
import aiofiles
import aiohttp
import asyncio
import shlex

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
            try:
                data = json.loads(await f.read())
                for key in ('dependencies', 'devDependencies'):
                    if key in data:
                        dependencies = data.get(key, {})
                        for k, v in dependencies.items():
                            if not any(badvalue in v for badvalue in badvalues):
                                packages[key].add(k)
            except:
                print("[!] Invalid JSON. Skipping.")
    
    directory = Path(directory).resolve()
    tasks = [asyncio.create_task(process_file(file)) for file in directory.rglob('package.json') if file.is_file()]
    await asyncio.gather(*tasks)
    return list(packages['dependencies'].union(packages['devDependencies']))

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
        results = [{"package": package}]
        data = await search.package_json_results(path, package)
        results.extend(json.loads(data))
        search_data = await search.package_search_json_results(f"{path}/npm_search.json", package)
        results.extend(search_data)
    
    if results == [{"package": package}]:
        results = []

    return results

async def scope_available(path, scope):
    command = f"npm search 'scope:{scope.split("@")[1]}'"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    resp = await process.stdout.read()

    results = []
    if "No matches found" in resp.decode('utf-8'):
        if await scope_404(scope):
            results = [{"scope": scope}]
            data = await search.package_json_results(path, scope)
            results.extend(json.loads(data))
            search_data = await search.package_search_json_results(f"{path}/npm_search.json", scope)
            results.extend(search_data)
    if results == [{"scope": scope}]:
        results = []

    return results

async def scope_404(scope):
    url = f'https://npmjs.com/~{scope.split('@')[1]}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 404:
                return True
            else:
                return False