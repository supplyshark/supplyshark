from tomllib import load
from . import db, file, github, search
import re

def find_git(cargofile):
    gh = []
    with open(cargofile, "rb") as f:
        data = load(f)
        if "dependencies" in data:
            for k, v in data["dependencies"].items():
                if "git" in v:
                    pattern = re.compile(r"github\.com/(.*?)/+", re.IGNORECASE)
                    gh += pattern.findall(v['git'])
    return gh

def run(path, org_user, repo, output, gitlab):
    gh = []
    for cargofile in search.files(path, "Cargo.toml"):
        gh += find_git(cargofile)
    
    users = list(set(gh))
    for user in users:
        if github.gh_get_user(user) is None:
            file.out(f"[cargo] [{org_user}/{repo}] GitHub User: {user}", output)
            url = github.get_url(org_user, repo, gitlab)
            #db.write_results(user, 4, org_user, repo, url)