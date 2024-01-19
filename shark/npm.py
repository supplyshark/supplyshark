from . import db, github, search, file, clean
from subprocess import getoutput
from requests import get
import json
import asyncio
import aiofiles
from pathlib import Path
from collections import defaultdict
import shlex
import aiohttp

async def find_package_json(directory: str) -> list:
    packages = defaultdict(set)
    
    async def process_file(file_path: Path) -> None:
        async with aiofiles.open(file_path, 'r') as f:
            data = json.loads(await f.read())
            for key in ('dependencies', 'devDependencies'):
                packages[key].update(data.get(key, {}).keys())
    
    directory = Path(directory).resolve()
    tasks = [asyncio.create_task(process_file(file)) for file in directory.rglob('package.json')]
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

async def scan_packages(package):
    command = f"npm view '{package}'"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    resp = await process.stderr.read()
    if "is not in this registry" in resp.decode('utf-8'):
        print(package)

async def scope_available(scope):
    command = f"npm search '{scope}'"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    resp = await process.stdout.read()
    if "No matches found" in resp.decode('utf-8'):
        await scope_404(scope)

async def scope_404(scope):
    url = f'https://npmjs.com/~{scope.split('@')[1]}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 404:
                print(scope)


''''   
def find_npmfile(data, key, matches, user, repo, output, gitlab):
    for k, v in data[key].items():
        if not any(x in v for x in matches):
            run(k, user, repo, output, gitlab)
        elif github.gh_available(v):
            file.out(f"[npm] [{user}/{repo}] GitHub User: {v}", output)
            url = github.get_url(user, repo, gitlab)
            #db.write_results(v, 2, user, repo, url)

def get_npmfile(npmfile, user, repo, output, gitlab):
    with open(npmfile, "rb") as f:
        data = json.load(f)
        matches = ["workspace:",
                   "file:",
                   "npm:",
                   "git+",
                   "github:",
                   "https://github",
                   "./",
                   "git://",
                   "/",
                   "link:"]
        
        for key in ["dependencies", "devDependencies"]:
            if key in data:
                find_npmfile(data, key, matches, user, repo, output, gitlab)
'''
