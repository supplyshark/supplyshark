from . import clean
from pathlib import Path
from subprocess import getoutput
import re
import asyncio
import aiofiles
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
    command = f"rg -e 'yarn add|npm install|pnpm install' --no-heading --json {path}"
    output_file = f"/tmp/.supplyshark/_output/{username}/npm_search.json"
    process = await asyncio.create_subprocess_exec(*shlex.split(command), stdout=asyncio.subprocess.PIPE)
    async with aiofiles.open(output_file, 'a') as f:
        while True:
            line = await process.stdout.readline()
            if line == b'':
                break
            await f.write(line.decode('utf-8'))

async def pip_install_files(path, username):
    command = f"rg -e 'pip install|poetry install|pip3 install' --no-heading --json {path}"
    output_file = f"/tmp/.supplyshark/_output/{username}/pip_search.json"
    process = await asyncio.create_subprocess_exec(*shlex.split(command), stdout=asyncio.subprocess.PIPE)
    async with aiofiles.open(output_file, 'a') as f:
        while True:
            line = await process.stdout.readline()
            if line == b'':
                break
            await f.write(line.decode('utf-8'))

async def gem_install_files(path, username):
    command = f'rg "gem i |gem \'|gem install|gem \\\"" --no-heading --json {path}'
    output_file = f"/tmp/.supplyshark/_output/{username}/gem_search.json"
    process = await asyncio.create_subprocess_exec(*shlex.split(command), stdout=asyncio.subprocess.PIPE)
    async with aiofiles.open(output_file, 'a') as f:
        while True:
            line = await process.stdout.readline()
            if line == b'':
                break
            await f.write(line.decode('utf-8'))

async def copy_files(path, username, repo, filename):
    file_paths = []
    dest_dir = Path(f'/tmp/.supplyshark/_output/{username}/{repo}')

    for root in Path(path).rglob(filename):
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

def install(package, path, args):
    packages = []
    for arg in args:
        stdout = getoutput(f"grep -r --exclude-dir=node_modules '{package} install {arg}' {path}")
        pattern = re.compile(r"{package}\s+install\s+{arg}(.*)".format(package=package, arg=arg))
        result = pattern.findall(stdout)
        for r in result:
            if clean.check(r):
                packages += [clean.package(r)]
    return list(set(packages))

def gems(path):
    gems = []
    for a in ["install ", "i ", '\\\"', '\'']:
        stdout = getoutput(f'grep -r --exclude-dir=node_modules "gem {a}" {path} | grep -vE "igem |agem |_gem |git:|path:|github.com|rails-assets.org"')
        pattern = re.compile(r"gem {a}(.*)".format(a=a))
        result = pattern.findall(stdout)
        for gem in result:
            gems += [clean.package_gem(gem)]
    return list(set(gems))

def yarn(path):
    packages = []
    for a in ["", "-D"]:
        stdout = getoutput(f"grep -r --exclude-dir=node_modules --exclude=yarn-error.log 'yarn add {a}' {path}")
        pattern = re.compile(r"yarn\s+add\s+{a}(.*)".format(a=a))
        result = pattern.findall(stdout)
        for r in result:
            if clean.check(r):
                packages += [clean.package(r)]

    return list(set(packages))

def files(path, file):
    files = []
    for f in Path(path).rglob(file):
        if "node_modules" not in str(f):
            files += [f]
    return files
