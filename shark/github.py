from dotenv import load_dotenv
from github import Github, Auth
from gitlab import Gitlab
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

def gl_get_repos(user):
    load_dotenv()
    token = getenv("GITLAB_AUTH")
    gl = Gitlab(private_token=token)
    group = gl.groups.get(user)
    projects = group.projects.list(get_all=True, archived=0)
    return list(map(lambda x: x.http_url_to_repo, filter(lambda x: user in x.http_url_to_repo, projects)))

def gh_get_repos(user):
    repos = gh_get_user(user).get_repos()
    return list(map(lambda x: x.name, filter(lambda x: not x.fork and not x.archived, repos)))

def clone_repo(user, name, gitlab):
    path = f"/tmp/.supplyshark/{user}/{name}"
    if gitlab:
        url = "https://gitlab.com"
    else:
        url = "https://github.com"
    clone_repository(f"{url}/{user}/{name}.git", path)
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
