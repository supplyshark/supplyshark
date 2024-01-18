from dotenv import load_dotenv
from github import Github, Auth
from gitlab import Gitlab
from pathlib import Path
from pygit2 import clone_repository
from os import getenv
import re

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

def gh_clone_repo(user, repo):
    path = f"/tmp/.supplyshark/{user}/{repo}"
    try:
        clone_repository(f"git://github.com/{user}/{repo}.git", path)
    except:
        pass
    return path

def gl_clone_repo(repo, url):
    name = repo.split(f"{url}")[1].split(".git")[0]
    path = f"/tmp/.supplyshark/{name}"
    Path(path).mkdir(parents=True, exist_ok=True)
    clone_repository(repo, path)
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