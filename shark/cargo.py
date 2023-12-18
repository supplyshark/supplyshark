from tomllib import load
from . import file, github, search
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

def run(path, repo, output):
    gh = []
    for cargofile in search.files(path, "Cargo.toml"):
        gh += find_git(cargofile)
    
    users = list(set(gh))
    for user in users:
        if github.get_user(user):
            file.out(f"[cargo] [{repo}] GitHub User: {user}", output)
