from . import db
import json

def npm_results(npm_data, uid, app, output):
    npm_package_results = npm_data["package_results"]
    npm_scope_results = npm_data["scope_results"]
    npm_git_results = npm_data["git_results"]

    for package_result in npm_package_results:
        try:
            package = package_result[0]["package"]
            for i in range(1, len(package_result)):
                file = package_result[i][0]["file"]
                line_number = package_result[i][0]['line_number']
                repo = "/".join(file.split("/")[:2])
                repo_url = f"https://github.com/{repo}"
                file_path = "/".join(file.split("/")[2:])
                bug_url = f"{repo_url}/blob/main/{file_path}?plain=1#L{line_number}"

                if app:
                    db.write_results(package, 1, uid, repo_url, bug_url)
                else:
                    with open(output, "a") as out:
                        msg = f"{package} [npm] {repo_url} {bug_url}"
                        print(msg, file=out)
        except:
            pass

    for scope_result in npm_scope_results:
        try:
            scope = scope_result[0]["scope"]
            for i in range(1, len(scope_result)):
                file = scope_result[i][0]["file"]
                line_number = scope_result[i][0]['line_number']
                repo = "/".join(file.split("/")[:2])
                repo_url = f"https://github.com/{repo}"
                file_path = "/".join(file.split("/")[2:])
                bug_url = f"{repo_url}/blob/main/{file_path}?plain=1#L{line_number}"

                if app:
                    db.write_results(scope, 2, uid, repo_url, bug_url)
                else:
                    with open(output, "a") as out:
                        msg = f"{scope} [npm scope] {repo_url} {bug_url}"
                        print(msg, file=out)
        except:
            pass
    
    for git_result in npm_git_results:
        try:
            package = git_result['package']
            file = git_result['file']
            line_number = git_result['line_number']
            value = git_result['value']
            gh_user = git_result['user']
            repo = "/".join(file.split("/")[:2])
            repo_url = f"https://github.com/{repo}"
            file_path = "/".join(file.split("/")[2:])
            bug_url = f"{repo_url}/blob/main/{file_path}?plain=1#L{line_number}"

            if app:
                db.write_results_gh(package, 3, uid, repo_url, bug_url, gh_user, value)
            else:
                with open(output, "a") as out:
                    msg = f"{package} [npm github] {gh_user} {repo_url} {bug_url}"
                    print(msg, file=out)
        except:
            pass

def gem_results(gem_data, uid, app, output):
    gem_package_results = gem_data['package_results']
    for package_result in gem_package_results:
        try:
            package = package_result[0]["package"]
            for i in range(1, len(package_result)):
                file = package_result[i][0]["file"]
                line_number = package_result[i][0]['line_number']
                repo = "/".join(file.split("/")[:2])
                repo_url = f"https://github.com/{repo}"
                file_path = "/".join(file.split("/")[2:])
                bug_url = f"{repo_url}/blob/main/{file_path}?plain=1#L{line_number}"

                if app:
                    db.write_results(package, 4, uid, repo_url, bug_url)
                else:
                    with open(output, "a") as out:
                        msg = f"{package} [gem] {repo_url} {bug_url}"
                        print(msg, file=out)
        except:
            pass

def pip_results(pip_data, uid, app, output):
    pip_package_results = pip_data['package_results']
    for package_result in pip_package_results:
        try:
            package = package_result[0]["package"]
            for i in range(1, len(package_result)):
                file = package_result[i][0]["file"]
                line_number = package_result[i][0]['line_number']
                repo = "/".join(file.split("/")[:2])
                repo_url = f"https://github.com/{repo}"
                file_path = "/".join(file.split("/")[2:])
                bug_url = f"{repo_url}/blob/main/{file_path}?plain=1#L{line_number}"

                if app:
                    db.write_results(package, 6, uid, repo_url, bug_url)
                else:
                    with open(output, "a") as out:
                        msg = f"{package} [pip] {repo_url} {bug_url}"
                        print(msg, file=out)
        except:
            pass

def go_results(go_data, uid, app, output):
    go_git_results = go_data['git_results']
    for git_result in go_git_results:
        try:
            package = git_result['package']
            file = git_result['file']
            line_number = git_result['line_number']
            value = git_result['value']
            gh_user = git_result['user']
            repo = "/".join(file.split("/")[:2])
            repo_url = f"https://github.com/{repo}"
            file_path = "/".join(file.split("/")[2:])
            bug_url = f"{repo_url}/blob/main/{file_path}?plain=1#L{line_number}"

            if app:
                db.write_results_gh(package, 7, uid, repo_url, bug_url, gh_user, value)
            else:
                with open(output, "a") as out:
                    msg = f"{package} [go github] {gh_user} {repo_url} {bug_url}"
                    print(msg, file=out)
        except:
            pass

def cargo_results(cargo_data, uid, app, output):
    cargo_git_results = cargo_data['git_results']
    for git_result in cargo_git_results:
        try:
            package = git_result['package']
            file = git_result['file']
            line_number = git_result['line_number']
            value = git_result['value']
            gh_user = git_result['user']
            repo = "/".join(file.split("/")[:2])
            repo_url = f"https://github.com/{repo}"
            file_path = "/".join(file.split("/")[2:])
            bug_url = f"{repo_url}/blob/main/{file_path}?plain=1#L{line_number}"

            if app:
                db.write_results_gh(package, 8, uid, repo_url, bug_url, gh_user, value)
            else:
                with open(output, "a") as out:
                    msg = f"{package} [cargo github] {gh_user} {repo_url} {bug_url}"
                    print(msg, file=out)
        except:
            pass

def process_results(uid, results, app, output):
    data = json.loads(results)
    npm_results(data[0]['npm_results'], uid, app, output)
    gem_results(data[1]['gem_results'], uid, app, output)
    pip_results(data[2]['pip_results'], uid, app, output)
    cargo_results(data[3]['cargo_results'], uid, app, output)
    go_results(data[4]['go_results'], uid, app, output)