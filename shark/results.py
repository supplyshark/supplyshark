from colorama import Fore
import json

def get_branch(repo_name, repos):
    for repo in repos:
        if repo['repo_name'] == repo_name:
            return repo['default_branch']
    return None

def _write_result(label, item, repo_urls, bug_urls, output_file):
    msg = f"[{label}] {item} {list(set(repo_urls))} {list(set(bug_urls))}"
    print(f"{Fore.CYAN}{msg}{Fore.RESET}")
    with open(output_file, "a") as f:
        print(msg, file=f)

def npm_results(npm_data, repos, output_file="results.txt"):
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

            _write_result("npm", package, repo_urls, bug_urls, output_file)
            count += 1
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

            _write_result("npm scope", scope, repo_urls, bug_urls, output_file)
            count += 1
        except:
            pass
    
    return count

def gem_results(gem_data, repos, output_file="results.txt"):
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

            _write_result("gem", package, repo_urls, bug_urls, output_file)
            count += 1
        except:
            pass
    
    return count

def pip_results(pip_data, repos, output_file="results.txt"):
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

            _write_result("pip", package, repo_urls, bug_urls, output_file)
            count += 1
        except:
            pass
    
    return count

def process_results(results, repos, output_file="results.txt"):
    data = json.loads(results)
    
    counts = [
        npm_results(data[0]['npm_results'], repos, output_file),
        gem_results(data[1]['gem_results'], repos, output_file)
    ]

    return sum(counts)
