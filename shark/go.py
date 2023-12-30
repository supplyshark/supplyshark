from . import db, file, github, search
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

def run(path, org_user, repo, output, gitlab):
    gh = []
    for modfile in search.files(path, "go.mod"):
        gh += find_gh(modfile)

    users = list(set(gh))
    for user in users:
        if github.gh_get_user(user) is None:
            file.out(f"[go] [{org_user}/{repo}] GitHub User: {user}", output)
            url = github.get_url(org_user, repo, gitlab)
            db.write_results(user, 3, org_user, repo, url)