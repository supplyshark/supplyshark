from . import db
from colorama import Fore
import json

def get_branch(repo_name, repos):
    for repo in repos:
        if repo['repo_name'] == repo_name:
            return repo['default_branch']
    return None

def write_db(package, type, uid, repo_url, bug_url):
    data = db.check_result_exists(uid, package, type)
    if data.count:
        id = data.data[0]['id']
        pdata = db.check_result_new(id)
        repo_urls = pdata['repo_url']
        bug_urls = pdata['bug_url']
        if repo_url.sort() != repo_urls.sort():
            db.delete_result(id)
            db.write_results(package, type, uid, repo_url, bug_url)
            return 1
        elif bug_url.sort() != bug_urls.sort():
            db.delete_result(id)
            db.write_results(package, type, uid, repo_url, bug_url)
            return 1
    if not data.count:
        db.write_results(package, type, uid, repo_url, bug_url)
        return 1
    return 0
    
def npm_results(npm_data, uid, app, repos):
    npm_package_results = npm_data["package_results"]
    npm_scope_results = npm_data["scope_results"]
    count = 0

    for package_result in npm_package_results:
        try:
            package = package_result[0]["package"]
            bug_urls = []
            repo_urls = []
            for i in range(1, len(package_result)):
                file = package_result[i][0]["file"]
                line_number = package_result[i][0]['line_number']
                repo = "/".join(file.split("/")[:2])
                branch = get_branch(repo.split("/")[1], repos)
                repo_url = f"https://github.com/{repo}"
                file_path = "/".join(file.split("/")[2:])
                bug_url = f"{repo_url}/blob/{branch}/{file_path}?plain=1#L{line_number}"
                bug_urls.append(bug_url)
                repo_urls.append(repo_url)

            if app:
                new_count = write_db(package, 1, uid, list(set(repo_urls)), list(set(bug_urls)))
                count += new_count
            else:
                msg = f"[npm] {package} {list(set(repo_urls))} {list(set(bug_urls))}"
                print(f"{Fore.CYAN}{msg}{Fore.RESET}")
                with open("results.txt", "a") as f:
                    print(msg, file=f)
        except:
            pass

    for scope_result in npm_scope_results:
        try:
            scope = scope_result[0]["scope"]
            bug_urls = []
            repo_urls = []
            for i in range(1, len(scope_result)):
                file = scope_result[i][0]["file"]
                line_number = scope_result[i][0]['line_number']
                repo = "/".join(file.split("/")[:2])
                branch = get_branch(repo.split("/")[1], repos)
                repo_url = f"https://github.com/{repo}"
                file_path = "/".join(file.split("/")[2:])
                bug_url = f"{repo_url}/blob/{branch}/{file_path}?plain=1#L{line_number}"
                bug_urls.append(bug_url)
                repo_urls.append(repo_url)

            if app:
                new_count = write_db(scope, 2, uid, list(set(repo_urls)), list(set(bug_urls)))
                count += new_count
            else:
                msg = f"[npm scope] {scope} {list(set(repo_urls))} {list(set(bug_urls))}"
                print(f"{Fore.CYAN}{msg}{Fore.RESET}")
                with open("results.txt", "a") as f:
                    print(msg, file=f)
        except:
            pass
    
    return count

def gem_results(gem_data, uid, app, repos):
    gem_package_results = gem_data['package_results']
    count = 0

    for package_result in gem_package_results:
        try:
            package = package_result[0]["package"]
            bug_urls = []
            repo_urls = []
            for i in range(1, len(package_result)):
                file = package_result[i][0]["file"]
                line_number = package_result[i][0]['line_number']
                repo = "/".join(file.split("/")[:2])
                repo_url = f"https://github.com/{repo}"
                branch = get_branch(repo.split("/")[1], repos)
                file_path = "/".join(file.split("/")[2:])
                bug_url = f"{repo_url}/blob/{branch}/{file_path}?plain=1#L{line_number}"
                bug_urls.append(bug_url)
                repo_urls.append(repo_url)

            if app:
                new_count = write_db(package, 4, uid, list(set(repo_urls)), list(set(bug_urls)))
                count += new_count
            else:
                msg = f"[gem] {package} {list(set(repo_urls))} {list(set(bug_urls))}"
                print(f"{Fore.CYAN}{msg}{Fore.RESET}")
                with open("results.txt", "a") as f:
                    print(msg, file=f)
        except:
            pass
    
    return count

def pip_results(pip_data, uid, app, repos):
    pip_package_results = pip_data['package_results']
    count = 0

    for package_result in pip_package_results:
        try:
            bug_urls = []
            repo_urls = []
            package = package_result[0]["package"]
            for i in range(1, len(package_result)):
                file = package_result[i][0]["file"]
                line_number = package_result[i][0]['line_number']
                repo = "/".join(file.split("/")[:2])
                branch = get_branch(repo.split("/")[1], repos)
                repo_url = f"https://github.com/{repo}"
                file_path = "/".join(file.split("/")[2:])
                bug_url = f"{repo_url}/blob/{branch}/{file_path}?plain=1#L{line_number}"
                bug_urls.append(bug_url)
                repo_urls.append(repo_url)

            if app:
                new_count = write_db(package, 6, uid, list(set(repo_urls)), list(set(bug_urls)))
                count += new_count
            else:
                msg = f"[pip] {package} {list(set(repo_urls))} {list(set(bug_urls))}"
                print(f"{Fore.CYAN}{msg}{Fore.RESET}")
                with open("results.txt", "a") as f:
                    print(msg, file=f)
        except:
            pass
    
    return count

def process_results(uid, results, app, repos):
    data = json.loads(results)
    
    counts = [
        npm_results(data[0]['npm_results'], uid, app, repos),
        gem_results(data[1]['gem_results'], uid, app, repos)
    ]

    return sum(counts)
