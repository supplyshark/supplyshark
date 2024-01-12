from . import clean, db, file, github, search
from subprocess import getoutput

def find_pip(path):
    packages = []
    for p in ["pip", "pip3", "poetry"]:
        if p != "poetry":
            args = ["", "--upgrade ", "-U "]
        else:
            args = [""]
        packages += search.install(p, path, args)
    return packages

def find_reqfile(reqfile):
    packages = []
    with open(reqfile, "r", encoding="utf8", errors="ignore") as f:
        for l in f.readlines():
            l = clean.package(l)
            if l[:1].isalpha():
                packages += [l]
    return packages

def run(path, user, repo, output, gitlab):
    packages = find_pip(path)
    for reqfile in search.files(path, "requirements.txt"):
        packages += find_reqfile(reqfile)

    pips = list(set(packages))
    for p in pips:
        if p != "" and p != "pip":
            stdout = getoutput(f"poetry search '{p}'")
            if stdout == "":
                file.out(f"[pip] [{user}/{repo}] {p}", output)
                url = github.get_url(user, repo, gitlab)
                #db.write_results(p, 7, user, repo, url)