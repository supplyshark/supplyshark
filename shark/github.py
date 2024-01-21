from . import search
from dotenv import load_dotenv
from github import Github, Auth
from os import getenv
from shutil import rmtree
import aiohttp
import asyncio
import jwt
import pygit2
import re
import time

def gh_get_user(user):
    try:
        load_dotenv()
        g = Github(auth=Auth.Token(getenv("GITHUB_AUTH")))
        user = g.get_user(user)
    except:
        user = None
    return user

def gh_get_repos(user):
    repos = gh_get_user(user).get_repos()
    return list(map(lambda x: x.name, filter(lambda x: not x.fork and not x.archived, repos)))

async def check_github_user(username) -> bool:
    load_dotenv()

    header = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f"Bearer {getenv("GITHUB_AUTH")}",
        'X-GitHub-Api-Version': '2022-11-28'
    }

    url = f"https://api.github.com/users/{username}"

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.get(url) as resp:
            data = await resp.json()
    
    if 'message' in data and data['message'] == 'Not Found':
        return True
    else:
        return False

async def get_access_token(id):
    load_dotenv()
    with open(getenv("PEM_FILE"), 'rb') as pem_file:
        signing_key = jwt.jwk_from_pem(pem_file.read())

    payload = {
        'iat': int(time.time()),
        'exp': int(time.time() + 600),
        'iss': getenv("APP_ID")
    }

    jwt_instance = jwt.JWT()
    encoded_jwt = jwt_instance.encode(payload, signing_key, alg='RS256')

    header = {
        'Authorization': f"Bearer {encoded_jwt}",
        'Accept': 'application/vnd.github+json'
    }

    url = f"https://api.github.com/app/installations/{id}/access_tokens"

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.post(url) as resp:
            data = await resp.json()
    
    return data['token']

async def check_github_repo(token, account, repo):
    url = f"https://api.github.com/repos/{account}/{repo}"
    header = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f"Bearer {token}",
        'X-GitHub-Api-Version': '2022-11-28'
    }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.get(url) as resp:
            data = await resp.json()
    
    repo_info = {
        'repo_name': data['name'],
        'repo_private': data['private'],
        'repo_forked': data['fork'],
        'repo_archived': data['archived']
    }

    return repo_info

async def gh_clone_repo(user, repo, token):
    path = f"/tmp/.supplyshark/{user}/{repo}"
    auth_method = 'x-access-token'
    try:
        callbacks = pygit2.RemoteCallbacks(pygit2.UserPass(auth_method, token))

        async def clone_repo():
            pygit2.clone_repository(f"https://github.com/{user}/{repo}.git", path, callbacks=callbacks)
        
        async def search_repo():
            await search.get_packages(path, user, repo)

        clone_task = asyncio.ensure_future(clone_repo())
        await asyncio.wait([clone_task])
        search_task = asyncio.ensure_future(search_repo())
        await asyncio.wait([search_task])
        await rmtree(path)
    except:
        pass

async def cli_gh_clone_repo(user, repo):
    path = f"/tmp/.supplyshark/{user}/{repo}"
    try:
        async def clone_repo():
            print(f"[+] Downloading {user}/{repo}")
            pygit2.clone_repository(f"https://github.com/{user}/{repo}.git", path)
        
        async def search_repo():
            print(f"[+] Copying files from {user}/{repo} to {path}")
            await search.get_packages(path, user, repo)

        clone_task = asyncio.ensure_future(clone_repo())
        await asyncio.wait([clone_task])
        search_task = asyncio.ensure_future(search_repo())
        await asyncio.wait([search_task])
        await rmtree(path)
    except:
        pass

def return_user(value):
    if re.compile(r"[A-Za-z0-9]+/([A-Za-z0-9]+)", re.IGNORECASE).match(value):
        user = value.split("/")[0]
    elif re.compile(r"github:[A-Za-z0-9]+/[A-Za-z0-9]+", re.IGNORECASE).match(value):
        user = value.split(":")[1].split("/")[0]
    elif re.compile(r"[A-Za-z0-9]+\+[A-Za-z0-9]+://[A-Za-z0-9]+@[A-Za-z0-9]+\.[A-Za-z0-9]+(:|/)[A-Za-z0-9]+/[A-Za-z0-9]+", re.IGNORECASE).match(value):
        pre = value.split("@")[1]
        if ":" in pre:
            user = value.split(":")[2].split("/")[0]
        else:
            user = pre.split("/")[1]
    elif re.compile(r"git://[A-Za-z0-9]+\.[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+", re.IGNORECASE).match(value):
        user = value.split("/")[3]
    else:
        user = ""
    return user

def return_user_regular(value):
    pattern = re.compile(r"github\.com/(.*?)/+", re.IGNORECASE)
    user = pattern.findall(value)[0]
    return user