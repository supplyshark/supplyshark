from dotenv import load_dotenv
from github import Github, Auth
from pygit2 import clone_repository
from os import getenv
from shutil import rmtree
import re

def get_user(user):
    try:
        load_dotenv()
        g = Github(auth=Auth.Token(getenv("GITHUB_AUTH")))
        user = g.get_user(user)
        print(user)
    except:
        user = None
    return user

def get_repos(user):
    repos = get_user(user).get_repos()
    return list(map(lambda x: x.name, filter(lambda x: not x.fork and not x.archived, repos)))

def clone_repo(user, name):
    path = f"/tmp/.supplyshark/{user}/{name}"
    clone_repository(f"https://github.com/{user}/{name}.git", path)
    return path

def available(value):
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
    elif get_user(user):
        return False
    else:
        return True
