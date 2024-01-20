import aiofiles
import asyncio
import pathlib
import json
import shlex

async def get_packages(path, username, repo):
    func_args_list = [
        (npm_install_files, (path, username)),
        (pip_install_files, (path, username)),
        (gem_install_files, (path, username)),
        (copy_files, (path, username, repo, 'package.json')),
        (copy_files, (path, username, repo, 'Gemfile')),
        (copy_files, (path, username, repo, 'Cargo.toml')),
        (copy_files, (path, username, repo, 'go.mod')),
        (copy_files, (path, username, repo, 'requirements.txt')),
    ]

    for func, args in func_args_list:
        await func(*args)

async def npm_install_files(path, username):
    command = f"rg -e 'yarn add|npm install|pnpm install|npm i|npm ci' --no-heading -n {path}"
    output_path = f"/tmp/.supplyshark/_output/{username}"
    output_file = f"{output_path}/npm_search.json"
    process = await asyncio.create_subprocess_exec(*shlex.split(command), stdout=asyncio.subprocess.PIPE)
    async with aiofiles.open(output_file, 'a') as f:
        while True:
            line = await process.stdout.readline()
            if line == b'':
                break
            line = line.decode('utf-8')
            file_path = line.split(":")[0]
            line_number = line.split(":")[1]
            match = line.split(":")[2]
            await f.write(json.dumps({
                "file": file_path.split("/tmp/.supplyshark/")[1],
                "line_number": line_number,
                "match": match.replace('\n', '')
            }) + '\n')

async def pip_install_files(path, username):
    command = f"rg -e 'pip install|poetry install|pip3 install' --no-heading -n {path}"
    output_path = f"/tmp/.supplyshark/_output/{username}"
    output_file = f"{output_path}/pip_search.json"
    process = await asyncio.create_subprocess_exec(*shlex.split(command), stdout=asyncio.subprocess.PIPE)
    async with aiofiles.open(output_file, 'a') as f:
        while True:
            line = await process.stdout.readline()
            if line == b'':
                break
            line = line.decode('utf-8')
            file_path = line.split(":")[0]
            line_number = line.split(":")[1]
            match = line.split(":")[2]
            await f.write(json.dumps({
                "file": file_path.split("/tmp/.supplyshark/")[1],
                "line_number": line_number,
                "match": match.replace('\n', '')
            }) + '\n')

async def gem_install_files(path, username):
    command = f'rg "gem i |gem \'|gem install|gem \\\"" --no-heading -n {path}'
    output_path = f"/tmp/.supplyshark/_output/{username}"
    output_file = f"{output_path}/gem_search.json"
    process = await asyncio.create_subprocess_exec(*shlex.split(command), stdout=asyncio.subprocess.PIPE)
    async with aiofiles.open(output_file, 'a') as f:
        while True:
            line = await process.stdout.readline()
            if line == b'':
                break
            line = line.decode('utf-8')
            file_path = line.split(":")[0]
            line_number = line.split(":")[1]
            match = line.split(":")[2]
            await f.write(json.dumps({
                "file": file_path.split("/tmp/.supplyshark/")[1],
                "line_number": line_number,
                "match": match.replace('\n', '')
            }) + '\n')

async def copy_files(path, username, repo, filename):
    file_paths = []
    dest_dir = pathlib.Path(f'/tmp/.supplyshark/_output/{username}/{repo}')

    for root in pathlib.Path(path).rglob(filename):
        file_paths.append(root)
    
    for file_path in file_paths:
        source_file = file_path.relative_to(path)
        dest_file = dest_dir / source_file

        dest_dir_path = dest_file.parent
        if not dest_dir_path.exists():
            dest_dir_path.mkdir(parents=True)
        
        async with aiofiles.open(file_path, 'rb') as input_file, aiofiles.open(dest_file, 'wb') as output_file:
            data = await input_file.read()
            await output_file.write(data)

async def package_json_results(path, value):
    command = f"rg -tjson -g package.json -F '{value}' --no-heading -n {path}"
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

async def package_json_results_git(path, value):
    command = f"rg -tjson -g package.json -F '{value}' --no-heading -n {path}"
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
        results.append({"file": file_path.split("/tmp/.supplyshark/_output/")[1], "line_number": line_number, "value": value})

    return json.dumps(results)

async def cargo_toml_results(path, value):
    command = f"rg -g Cargo.toml -F '{value}' --no-heading -n {path}"
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
        results.append({"file": file_path.split("/tmp/.supplyshark/_output/")[1], "line_number": line_number, "value": value})

    return json.dumps(results)

async def requirements_txt_results(path, value):
    command = f"rg -g requirements.txt -F '{value}' --no-heading -n {path}"
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

async def go_mod_results(path, value):
    command = f"rg -g go.mod -F '{value}' --no-heading -n {path}"
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
        results.append({"file": file_path.split("/tmp/.supplyshark/_output/")[1], "line_number": line_number, "value": value})

    return json.dumps(results)

async def package_search_json_results(path, value):
    matches = []
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        async for line in f:
            item = json.loads(line.strip())
            if value in item['match']:
                matches.append([item])

    return matches