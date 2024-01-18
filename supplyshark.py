from pathlib import Path
from threading import Thread
from sys import exit
import argparse
import multiprocessing
import shark

def chunk(ls, n):
    return [ls[i::n] for i in range(n)]

def threads(path, user, name, output, gitlab):
    t1 = Thread(target=shark.npm.main, args=(path, user, name, output, gitlab,))
    t2 = Thread(target=shark.pip.run, args=(path, user, name, output, gitlab,))
    t3 = Thread(target=shark.gem.run, args=(path, user, name, output, gitlab,))
    t4 = Thread(target=shark.cargo.run, args=(path, user, name, output, gitlab,))
    t5 = Thread(target=shark.go.run, args=(path, user, name, output, gitlab,))
    
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    
    shark.file.del_folder(path)

def run_thread(repos, user, output, gitlab, url):
    for repo in repos:
        try:
            if gitlab:
                name = repo.split(f"{url}/{user}/")[1].split(".git")[0]
                print(f"[+] Downloading {user}/{name}")
                path = shark.github.gl_clone_repo(repo, url)
            else:
                name = repo
                print(f"[+] Downloading {user}/{name}")
                path = shark.github.gh_clone_repo(user, name)
            
            threads(path, user, name, output, gitlab)
        except:
            pass

def run(user, output, gitlab, url):
    tmp = f"/tmp/.supplyshark/{user}"
    Path(tmp).mkdir(parents=True, exist_ok=True)
    if gitlab:
        repos = shark.github.gl_get_repos(user, url)
    else:
        repos = shark.github.gh_get_repos(user)
    c = chunk(repos, multiprocessing.cpu_count())

    procs = []
    for i, s in enumerate(c):
        proc = multiprocessing.Process(target=run_thread, args=(s, user, output, gitlab, url))
        procs.append(proc)
        proc.start()

    for p in procs:
        p.join()

    shark.file.del_folder(tmp)

def run_file(file, output, gitlab, url):
    with open(file, "r") as f:
        for ff in f.readlines():
            try:
                run(ff.strip(), output, gitlab, url)
            except:
                pass

def old_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", type=str)
    parser.add_argument("-o", type=str, required=True)
    parser.add_argument("-L", type=str)
    parser.add_argument("-r", type=str)
    parser.add_argument("--gitlab", type=bool, action=argparse.BooleanOptionalAction)
    parser.add_argument("--url", type=str, default="https://gitlab.com")
    args = parser.parse_args()
    
    tmp = "/tmp/.supplyshark"
    if Path(tmp).exists():
        shark.file.del_folder(tmp)

    # Read list of orgs
    if args.L is not None:
        run_file(args.L, args.o, args.gitlab, args.url)
    # Specific repository
    elif args.r is not None:
        run_thread([args.r], args.u, args.o, args.gitlab, args.url)
    # Single user
    else:
        run(args.u, args.o, args.gitlab, args.url)

def start(uid):
    settings = shark.db.fetch_user_app_settings(uid)
    sub = shark.db.get_subscription_name(uid)

    id = settings['installation_id']
    account = settings['account_name']
    repos = settings['repositories']
    forked = settings['forked']
    archived = settings['archived']

if __name__ == "__main__":
    runs = shark.db.get_scheduled_runs()
    if len(runs) == 0:
        print("No scheduled runs today.")
        exit(0)

    for uid in runs:
        if shark.db.is_active(uid):
            start(uid)