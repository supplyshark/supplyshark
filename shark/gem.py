from . import search, clean
from collections import defaultdict
import aiohttp
import asyncio
import json
import re
import shlex

def read_gem_search_json(path: str) -> list:
    matches = defaultdict(set)

    with open(f"{path}/gem_search.json", 'r', encoding='utf-8') as f:
        for line in f:
            match_dict = json.loads(line.strip())
            matches[match_dict['match']]
    
    matches_list = list(matches.keys())
    return clean.gem_search(matches_list)

async def scan_gems(path, gem):
    command = f"gem search '{gem}'"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    resp = await process.stdout.read()
    
    results = []

    if resp == b'\n' and await gem_404(gem):
        results = [{"package": gem}]
        search_data = await search.package_search_json_results(f"{path}/gem_search.json", gem)
        results.extend(search_data)
    return results    

async def gem_404(gem):
    url = f"https://rubygems.org/gems/{gem}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 404:
                return True
            else:
                return False


def gem_files(gemfile):
    results = []
    with open(gemfile, "r", encoding="utf8", errors="ignore") as f:
        for line in f.readlines():
            pattern = re.compile(r'git: "https://github.com/(.*?)/+', re.IGNORECASE)
            result = pattern.findall(line)
            results += result

    return results