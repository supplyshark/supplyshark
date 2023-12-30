from . import db, file, github, search
from requests import get
from subprocess import getoutput
import re

def gem_404(gem):
    r = get(f"https://rubygems.org/gems/{gem}")
    if "It will be mine. Oh yes. It will be mine." in r.text:
        return True
    else:
        return False

def gem_exists(gem, user, repo, output, gitlab):
    stdout = getoutput(f"gem search '{gem}'")
    if len(stdout) == 0 and gem_404(gem):
        file.out(f"[gem] [{user}/{repo}] {gem}", output)
        url = github.get_url(user, repo, gitlab)
        db.write_results(gem, 5, user, repo, url)

def gem_files(gemfile):
    results = []
    with open(gemfile, "r", encoding="utf8", errors="ignore") as f:
        for line in f.readlines():
            pattern = re.compile(r'git: "https://github.com/(.*?)/+', re.IGNORECASE)
            result = pattern.findall(line)
            results += result

    return results
        
def run(path, org_user, repo, output, gitlab):
    gems = search.gems(path)
    for gem in gems:
        gem_exists(gem, org_user, repo, output, gitlab)
    
    gh = []
    for f in search.files(path, "Gemfile"):
        gh += gem_files(f)
    
    users = list(set(gh))
    for user in users:
        if github.gh_get_user(user) is None:
            file.out(f"[gem] [{org_user}/{repo}] GitHub User: {user}", output)
            url = github.get_url(org_user, repo, gitlab)
            db.write_results(user, 6, org_user, repo, url)
