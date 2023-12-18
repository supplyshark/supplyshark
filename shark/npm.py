from . import github, search, file
from subprocess import getoutput
from requests import get
import json

def scope_available(scope):
    stdout = getoutput(f"npm search {scope}")
    if "No matches found" in stdout:
        return True
    else:
        return False

def scope_404(scope):
    r = get(f"https://npmjs.com/~{scope}")
    if "NotFoundError: Scope not found" in r.text:
        return True
    else:
        return False

def npm_available(package):
    stdout = getoutput(f"npm view '{package}'")
    if "is not in this registry" in stdout:
        return True
    else:
        return False

def get_packages(path):
    packages = []
    for p in ["npm", "yarn", "pnpm"]:
        if p == "yarn":
            packages += search.yarn(path)
        else:
            args = ["", "-g", "--save"]
            packages += search.install(p, path, args)
    return list(set(packages))

def npm_scope(package, user, repo, output):
    scope = package.split("/")[0]
    if scope_available(scope) and scope_404(scope.split("@")[1]):
        file.out(f"[npm] [{user}/{repo}] {package}", output)

def run(package, user, repo, output):
    if package.startswith("@"):
        npm_scope(package, user, repo, output)
    elif npm_available(package):
        file.out(f"[npm] [{user}/{repo}] {package}", output)
    
def find_npmfile(data, key, matches, user, repo, output):
    for k, v in data[key].items():
        if not any(x in v for x in matches):
            run(k, user, repo, output)
        elif github.available(v):
            file.out(f"[npm] [{user}/{repo}] GitHub User: {v}", output)

def get_npmfile(npmfile, user, repo, output):
    with open(npmfile, "rb") as f:
        data = json.load(f)
        matches = ["workspace:",
                   "file:",
                   "npm:",
                   "git+",
                   "github:",
                   "https://github",
                   "./",
                   "git://",
                   "/",
                   "link:"]
        
        for key in ["dependencies", "devDependencies"]:
            if key in data:
                find_npmfile(data, key, matches, user, repo, output)

def main(path, user, repo, output):
    packages = get_packages(path)
    for p in packages:
        run(p, user, repo, output)   
    
    for npmfile in search.files(path, "package.json"):
        get_npmfile(npmfile, user, repo, output)
