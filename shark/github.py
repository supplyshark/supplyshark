from . import search
from dotenv import load_dotenv
from github import Github, Auth
from os import getenv
from pathlib import Path
from shutil import rmtree
import pygit2
import re

def gh_get_user(user):
    try:
        load_dotenv()
        g = Github(auth=Auth.Token(getenv("GITHUB_AUTH")))
        user = g.get_user(user)
    except:
        user = None
    return user

def gh_get_repos(user):
    g = gh_get_user(user)
    
    if g is None:
        print(f"[!] Account {user} does not exist.")
        return None, None
    
    else:
        repos = gh_get_user(user).get_repos()
        gh_list = list(map(lambda x: {
            "repo_name": x.name, 
            "default_branch": x.default_branch
            }, filter(lambda x: not x.fork and not x.archived, repos)))
        repo_list = list(map(lambda x: x.name, filter(lambda x: not x.fork and not x.archived, repos)))
        return repo_list, gh_list

def clean_git(path):
    git_ignore = f"{path}/.gitignore"
    dot_git = f"{path}/.git"
    if Path(git_ignore).exists():
        Path(git_ignore).unlink()
    if Path(dot_git).exists():
        rmtree(dot_git)

def cli_gh_clone_repo(user, repo):
    path = f"/tmp/.supplyshark/{user}/{repo}"
    load_dotenv()
    auth_method = "x-access-token"
    try:
        callbacks = pygit2.RemoteCallbacks(pygit2.UserPass(auth_method, getenv("GITHUB_AUTH")))
        pygit2.clone_repository(f"https://github.com/{user}/{repo}.git", path, callbacks=callbacks)
        clean_git(path)
        search.get_packages(path, user, repo)
        rmtree(path)
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
