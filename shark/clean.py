def check(result):
    if len(result.split()) > 1:
        return False
    else:
        return True
    
def package(line):
    for ch in ['"', "'", "`", ";", ",", "}", "+", ")", "("]:
        if ch in line:
            line = line.replace(ch, "")
    
    line = line.split(">")[0].split("=")[0].split("<")[0]
    line = line.split("\\")[0].split("@latest")[0].split("~")[0]

    if line.endswith("."):
        line = line[:1]
    
    if line.startswith("."):
        line = ""
    
    if line.endswith("-"):
        line = ""

    if line.startswith(" "):
        line = line[1:]
    
    line = line.split(" ")[0]

    if "%" in line:
        line = ""
    elif "*" in line:
        lien = ""
    elif line.startswith("https://"):
        line = ""
    elif line == "PATH_TO_TARBALL":
        line = ""
    elif line == "any-required-dependencies":
        line = ""
    elif line == "previously":
        line = ""
    elif line == "*":
        line = ""
    elif line.startswith("{"):
        line = ""
    
    line = line.split("[")[0]

    if line == "Yarn":
        line = ""
    
    if line.endswith("."):
        line = line[:-1]

    if "@x.y.z" in line:
        line = ""
    
    line = line.lower().rstrip()

    return line

def package_gem(gem):
    for ch in ['"', "'", "`", "{", "}"]:
        if ch in gem:
            gem = gem.replace(ch, "")
    
    gem = gem.split(",")[0].split(":")[0].split("\\")[0]
    gem = gem.split("/")[0].split(" ")[0].split("#")[0]
    gem = gem.split("<")[0].split(";")[0]

    if gem.endswith(".gem"):
        gem = ""
    elif gem.startswith("."):
        gem = ""
    elif gem.endswith("."):
        gem = gem[:-1]
    elif gem.startswith("$"):
        gem = ""
    elif gem.endswith("-"):
        gem = ""
    elif "(" in gem:
        gem = ""
    elif "%" in gem:
        gem = ""
    
    return gem
