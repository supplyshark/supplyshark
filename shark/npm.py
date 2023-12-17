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
    r = get(f"https://mpjs.com/~{scope}")
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

def npm_scope(invalid, package, repo, output):
    scope = package.split("/")[0]
    if not any(x in scope for x in invalid):
        if scope_available(scope) and scope_404(scope.split("@")[1]):
            file.out(f"[npm] [{repo}] {package}", output)
        else:
            invalid += [scope]
    return invalid

def run(invalid, package, repo, output):
    if package.startswith("@"):
        invalid += npm_scope(invalid, package, repo, output)
    elif npm_available(package):
        file.out(f"[npm] [{repo}] {package}", output)
    
    return invalid

def find_npmfile(invalid, data, key, matches, repo, output):
    for k, v in data[key].items():
        if not any(x in v for x in matches):
            invalid += run(invalid, k, repo, output)
        elif github.available(v):
            file.out(f"[npm] [{repo}] GitHub User: {v}", output)
    return invalid

def run_npmfile(invalid, data, key, matches, repo, output):
    if key in data:
        invalid += find_npmfile(invalid, data, key, matches, repo, output)
    return invalid

def get_npmfile(invalid, npmfile, repo, output):
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
            invalid += run_npmfile(invalid, data, key, matches, repo, output)
    return invalid

def main(path, repo, output):
    packages = get_packages(path)
    invalid = []
    for p in packages:
        invalid += run(invalid, p, repo, output)
    for npmfile in search.files(path, "package.json"):
        invalid += get_npmfile(invalid, npmfile, repo, output)