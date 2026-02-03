import aiofiles
import asyncio
import pathlib
import json
import shlex
import subprocess
import re

def get_packages(path, username, repo):
    func_args_list = [
        (npm_install_files, (path, username)),
        (pip_install_files, (path, username)),
        (gem_install_files, (path, username)),
        (copy_files, (path, username, repo, 'package.json')),
        (copy_files, (path, username, repo, 'Gemfile')),
        (copy_files, (path, username, repo, 'requirements.txt')),
    ]

    for func, args in func_args_list:
        func(*args)

def find_urls(path, username):
    command = f"rg -o '(?<=https?:\\/\\/)[^\\/]+' --no-heading -n {path}"
    output_path = f"/tmp/.supplyshark/_output/{username}"
    output_file = f"{output_path}/urls_search.json"

    if not pathlib.Path(output_file).exists():
        pathlib.Path(output_file).touch()
    
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)

    with open(output_file, 'a') as f:
        while True:
            line = process.stdout.readline()

            if line == b'':
                break

            line = line.decode('utf-8')
            file_path = line.split(":")[0]
            line_number = line.split(":")[1]
            match = line.split(":")[2]

            f.write(json.dumps({
                "file": file_path.split("/tmp/.supplyshark/")[1],
                "line_number": line_number,
                "match": match.replace('\n', '')
            }) + '\n')

def npm_install_files(path, username):
    command = f"rg -e 'yarn add|npm install|pnpm install|npm i|npm ci' -g '!*yarn-error.log' --no-heading -g '!*/node_modules' -n {path}"
    output_path = f"/tmp/.supplyshark/_output/{username}"
    output_file = f"{output_path}/npm_search.json"
    if not pathlib.Path(output_file).exists():
        pathlib.Path(output_file).touch()
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)

    bad_paths = ['node_modules']

    with open(output_file, 'a') as f:
        while True:
            line = process.stdout.readline()
            if line == b'':
                break
            line = line.decode('utf-8')
            file_path = line.split(":")[0]
            line_number = line.split(":")[1]
            match = line.split(":")[2]
            if not any(bad_path in file_path for bad_path in bad_paths):
                f.write(json.dumps({
                    "file": file_path.split("/tmp/.supplyshark/")[1],
                    "line_number": line_number,
                    "match": match.replace('\n', '')
                }) + '\n')

def pip_install_files(path, username):
    command = f"rg -e 'pip install|poetry install|pip3 install' --no-heading -n {path}"
    output_path = f"/tmp/.supplyshark/_output/{username}"
    output_file = f"{output_path}/pip_search.json"
    if not pathlib.Path(output_file).exists():
        pathlib.Path(output_file).touch()
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)

    with open(output_file, 'a') as f:
        while True:
            line = process.stdout.readline()
            if line == b'':
                break
            line = line.decode('utf-8')
            file_path = line.split(":")[0]
            line_number = line.split(":")[1]
            match = line.split(":")[2]
            f.write(json.dumps({
                "file": file_path.split("/tmp/.supplyshark/")[1],
                "line_number": line_number,
                "match": match.replace('\n', '')
            }) + '\n')

def gem_install_files(path, username):
    command = f'rg "gem i |gem \'|gem install|gem \\\"" --no-heading -g "!*/node_modules" -n {path}'
    output_path = f"/tmp/.supplyshark/_output/{username}"
    output_file = f"{output_path}/gem_search.json"
    if not pathlib.Path(output_file).exists():
        pathlib.Path(output_file).touch()
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)

    bad_values = ['install ./',
                 ':git',
                 'install --dev ./']
    
    bad_paths = ['node_modules']

    with open(output_file, 'a') as f:
        while True:
            line = process.stdout.readline()
            if line == b'':
                break
            line = line.decode('utf-8')
            file_path = line.split(":")[0]
            line_number = line.split(":")[1]
            match = line.split(":")[2]
            if not any(bad_value in line for bad_value in bad_values):
                if not any(bad_path in file_path for bad_path in bad_paths):
                    f.write(json.dumps({
                        "file": file_path.split("/tmp/.supplyshark/")[1],
                        "line_number": line_number,
                        "match": match.replace('\n', '')
                    }) + '\n')

def copy_files(path, username, repo, filename):
    file_paths = []
    dest_dir = pathlib.Path(f'/tmp/.supplyshark/_output/{username}/{repo}')

    bad_paths = ["vendor/bundle/ruby/",
                "node_modules",
                "doc/requirements.txt",
                "jspm_packages"]

    for root in pathlib.Path(path).rglob(filename):
        if not any(bad_path in str(root) for bad_path in bad_paths):
            file_paths.append(root)
    
    for file_path in file_paths:
        source_file = file_path.relative_to(path)
        dest_file = dest_dir / source_file

        dest_dir_path = dest_file.parent
        if not dest_dir_path.exists():
            dest_dir_path.mkdir(parents=True)
        
        try:
            with open(file_path, 'rb') as input_file, open(dest_file, 'wb') as output_file:
                data = input_file.read()
                output_file.write(data)
        except:
            print("[!] Invalid file for copying. Skipping.")
            pass

async def package_json_results(path, value):
    command = f"rg -tjson -g package.json -F '{value}' --no-heading -n {path}"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                  stdout=asyncio.subprocess.PIPE,
                                                  stderr=asyncio.subprocess.PIPE)
    
    badvalues = [': "workspace:',
                ': "file:',
                ': "npm:',
                ': "git+',
                ': "github:',
                ': "https://github',
                ': "./',
                ': "git://',
                ': "/',
                ': "link:']
    
    results = []
    while True:
        line = await process.stdout.readline()
        if line == b'':
            break
        line = line.decode('utf-8')
        file_path = line.split(":")[0]
        line_number = line.split(":")[1]
        if re.search(rf'"{value}.*":', line) and not any(badvalue in line for badvalue in badvalues):
            results.append([{"file": file_path.split("/tmp/.supplyshark/_output/")[1], "line_number": line_number, "value": value}])

    return json.dumps(results)

async def requirements_txt_results(path, value):
    command = f"rg -g requirements.txt -F '{value}' --no-heading -g '!*/doc/requirements.txt' -n {path}"
    process = await asyncio.create_subprocess_exec(*shlex.split(command),
                                                  stdout=asyncio.subprocess.PIPE,
                                                  stderr=asyncio.subprocess.PIPE)
    results = []
    while True:
        line = await process.stdout.readline()
        if line == b'':
            break
        line = line.decode('utf-8')
        file_path = line.split(":")[0]
        line_number = line.split(":")[1]
        results.append([{"file": file_path.split("/tmp/.supplyshark/_output/")[1], "line_number": line_number, "value": value}])

    return json.dumps(results)

async def package_search_json_results(path, value):
    matches = []
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        async for line in f:
            item = json.loads(line.strip())
            if value in item['match']:
                matches.append([item])

    return matches