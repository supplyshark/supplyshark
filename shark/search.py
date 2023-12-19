from . import clean
from pathlib import Path
from subprocess import getoutput
import re

def install(package, path, args):
    packages = []
    for arg in args:
        stdout = getoutput(f"grep -r '{package} install {arg}' {path}")
        pattern = re.compile(r"{package}\s+install\s+{arg}(.*)".format(package=package, arg=arg))
        result = pattern.findall(stdout)
        for r in result:
            if clean.check(r):
                packages += [clean.package(r)]
    return list(set(packages))

def gems(path):
    gems = []
    for a in ["install ", "i ", '\\\"', '\'']:
        stdout = getoutput(f'grep -r "gem {a}" {path} | grep -vE "git:|github.com"')
        pattern = re.compile(r"gem {a}(.*)".format(a=a))
        result = pattern.findall(stdout)
        for gem in result:
            gems += [clean.package_gem(gem)]
    return list(set(gems))

def yarn(path):
    packages = []
    for a in ["", "-D"]:
        stdout = getoutput(f"grep -r --exclude=yarn-error.log 'yarn add {a}' {path}")
        pattern = re.compile(r"yarn\s+add\s+{a}(.*)".format(a=a))
        result = pattern.findall(stdout)
        for r in result:
            if clean.check(r):
                packages += [clean.package(r)]

    return list(set(packages))

def files(path, file):
    files = []
    for f in Path(path).rglob(file):
        if "node_modules" not in str(f):
            files += [f]
    return files
