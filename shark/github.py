from dotenv import load_dotenv
from github import Github, Auth
from gitlab import Gitlab
from pathlib import Path
from os import getenv
import re
import jwt
import time
import aiohttp
import asyncio
import pygit2

def gh_get_user(user):
    try:
        load_dotenv()
        g = Github(auth=Auth.Token(getenv("GITHUB_AUTH")))
        user = g.get_user(user)
    except:
        user = None
    return user

def gl_auth(url):
    if url != "https://gitlab.com":
        gl = Gitlab(url)
    else:
        load_dotenv()
        token = getenv("GITLAB_AUTH")
        gl = Gitlab(private_token=token)
    return gl

def gl_get_repos(user, url):
    gl = gl_auth(url)
    group = gl.groups.get(user)
    projects = group.projects.list(get_all=True, archived=0, include_subgroups=1)
    return list(map(lambda x: x.http_url_to_repo, filter(lambda x: user in x.http_url_to_repo, projects)))

def gh_get_repos(user):
    repos = gh_get_user(user).get_repos()
    return list(map(lambda x: x.name, filter(lambda x: not x.fork and not x.archived, repos)))

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

async def check_github_repo(token, forked, archived, account, repo):
    url = f"https://api.github.com/repos/{account}/{repo}"
    header = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f"Bearer {token}",
        'X-GitHub-Api-Version': '2022-11-28'
    }

    async with aiohttp.ClientSession(headers=header) as session:
        async with session.get(url) as resp:
            data = await resp.json()
    
    repo_name = data['name']
    repo_private = data['private']
    repo_forked = data['fork']
    repo_archived = data['archived']

    print(repo_name, repo_private, repo_forked, repo_archived)

def gh_clone_repo(user, repo, token):
    path = f"/tmp/.supplyshark/{user}/{repo}"
    auth_method = 'x-access-token'
    try:
        callbacks = pygit2.RemoteCallbacks(pygit2.UserPass(auth_method, token))
        pygit2.clone_repository(f"https://github.com/{user}/{repo}.git", path, callbacks=callbacks)
    except:
        pass

def gl_clone_repo(repo, url):
    name = repo.split(f"{url}")[1].split(".git")[0]
    path = f"/tmp/.supplyshark/{name}"
    Path(path).mkdir(parents=True, exist_ok=True)
    pygit2.clone_repository(repo, path)
    return path

def gh_available(value):
    if re.compile(r"[A-Za-z0-9]+/([A-Za-z0-9]+)", re.IGNORECASE).match(value):
        user = value.split("/")[0]
    elif re.compile(r"github:[A-Za-z0-9]+/[A-Za-z0-9]+", re.IGNORECASE).match(value):
        user = value.split(":")[1].split("/")[0]
    elif re.compile(r"[A-Za-z0-9]+\+[A-Za-z0-9]+://[A-Za-z0-9]+@[A-Za-z0-9]+\.[A-Za-z0-9]+:[A-Za-z0-9]+/[A-Za-z0-9]+", re.IGNORECASE).match(value):
        user = value.split(":")[2].split("/")[0]
    elif re.compile(r"git://[A-Za-z0-9]+\.[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+", re.IGNORECASE).match(value):
        user = value.split("/")[3]
    else:
        user = ""

    if user == "":
        return False
    elif gh_get_user(user):
        return False
    else:
        return True

def get_url(user, repo, gitlab):
    if gitlab:
        url = f"https://gitlab.com/{user}/{repo}"
    else:
        url = f"https://github.com/{user}/{repo}"
    return url