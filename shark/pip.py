from . import clean, search
from collections import defaultdict
from pathlib import Path
import aiofiles
import asyncio
import json
import shlex

async def find_requirements_txt(directory: Path) -> list[str]:
    lines = []

    async def process_file(file_path: Path) -> None:
        async with aiofiles.open(file_path, 'r') as f:
            lines.extend([
                line.strip().split()[0].split("=")[0].split(">")[0].split("<")[0]
                for line in await f.readlines() if line[0].isalpha()
            ])
    
    directory = Path(directory).resolve()
    tasks = [asyncio.create_task(process_file(file)) for file in directory.rglob('requirements.txt')]
    await asyncio.gather(*tasks)
    return lines

def read_pip_search_json(path: str) -> list:
    matches = defaultdict(set)

    with open(f"{path}/pip_search.json", 'r', encoding='utf-8') as f:
        for line in f:
            match_dict = json.loads(line.strip())
            matches[match_dict['match']]
    
    matches_list = list(matches.keys())
    return clean.search(matches_list)

async def scan_packages(path, package):
    command = f"poetry search '{package}'"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                   stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE)
    resp = await process.stdout.read()
    results = []
    if resp == b'':
        results = [{"package": package}]
        data = await search.requirements_txt_results(path, package)
        results.extend(json.loads(data))
        search_data = await search.package_search_json_results(f"{path}/pip_search.json", package)
        results.extend(search_data)
    
    return results