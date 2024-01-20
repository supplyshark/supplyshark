from . import db, file, github, search, clean
from requests import get
from subprocess import getoutput
import re
import asyncio
import shlex
from collections import defaultdict
import json
import aiohttp

def read_gem_search_json(path: str) -> list:
    matches = defaultdict(set)

    with open(f"{path}/gem_search.json", 'r', encoding='utf-8') as f:
        for line in f:
            match_dict = json.loads(line.strip())
            matches[match_dict['match']]
    
    matches_list = list(matches.keys())
    return clean.gem_search(matches_list)

async def scan_gems(gem):
    command = f"gem search '{gem}'"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    resp = await process.stdout.read()
    if resp == b'\n':
        await gem_404(gem)

async def gem_404(gem):
    url = f"https://rubygems.org/gems/{gem}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 404:
                print(gem)


def gem_files(gemfile):
    results = []
    with open(gemfile, "r", encoding="utf8", errors="ignore") as f:
        for line in f.readlines():
            pattern = re.compile(r'git: "https://github.com/(.*?)/+', re.IGNORECASE)
            result = pattern.findall(line)
            results += result

    return results