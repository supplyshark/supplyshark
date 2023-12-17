from . import file, github, search
import re

def find_gh(modfile):
    gh = []
    with open(modfile, "r", encoding="utf8", errors="ignore") as f:
        for l in f.readlines():
            line = l.strip()
            if l.strip().startswith("github.com"):
                pattern = re.compile(r"github\.com/(.*?)/+", re.IGNORECASE)
                gh += pattern.findall(line)

    return gh

def run(path, repo, output):
    gh = []
    for modfile in search.files(path, "go.mod"):
        gh += find_gh(modfile)

    users = list(set(gh))
    for user in users:
        if gh.find_user is None:
            file.out(f"[go] [{repo}] GitHub User: {user}", output)