from . import db, github, search, file, clean
from subprocess import getoutput
from requests import get
import json
import asyncio
import aiofiles
from pathlib import Path
from collections import defaultdict
import csv

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

def read_npm_search_csv(path: str) -> list:
    matches = defaultdict(set)

    with open(f"{path}/npm_search.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches[row['match']]

    matches_list = list(matches.keys())
    return clean.search(matches_list)

def scope_available(scope):
    stdout = getoutput(f"npm search '{scope}'")
    if "No matches found" in stdout:
        return True
    else:
        return False

def scope_404(scope):
    r = get(f"https://npmjs.com/~{scope}")
    if "NotFoundError: Scope not found" in r.text:
        return True
    else:
        return False

def npm_available(package):
    stdout = getoutput(f"npm view '{package}'")
    if "is not in this registry" in stdout:
        return True
    else:
        return False

def get_packages(path):
    packages = []
    for p in ["npm", "yarn", "pnpm"]:
        if p == "yarn":
            packages += search.yarn(path)
        else:
            args = ["", "-g", "--save"]
            packages += search.install(p, path, args)
    return list(set(packages))

def npm_scope(package, user, repo, output, gitlab):
    scope = package.split("/")[0]
    if scope_available(scope) and scope_404(scope.split("@")[1]):
        file.out(f"[npm] [{user}/{repo}] {package}", output)
        url = github.get_url(user, repo, gitlab)
        #db.write_results(package, 1, user, repo, url)

def run(package, user, repo, output, gitlab):
    if package.startswith("@"):
        npm_scope(package, user, repo, output, gitlab)
    elif npm_available(package):
        file.out(f"[npm] [{user}/{repo}] {package}", output)
        url = github.get_url(user, repo, gitlab)
        #db.write_results(package, 1, user, repo, url)
    
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

def main(path, user, repo, output, gitlab):
    packages = get_packages(path)
    for p in packages:
        run(p, user, repo, output, gitlab)   
    
    for npmfile in search.files(path, "package.json"):
        get_npmfile(npmfile, user, repo, output, gitlab)
