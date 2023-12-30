from pathlib import Path
from threading import Thread
import argparse
import multiprocessing
import shark

def chunk(ls, n):
    return [ls[i::n] for i in range(n)]

def run_thread(repos, user, output, gitlab):
    for repo in repos:
        print(f"[+] Downloading {user}/{repo}")

        if gitlab:
            name = repo.split("/")[4].split(".git")[0]
        else:
            name = repo

        print(f"[+] Downloading {user}/{name}")
        path = shark.github.clone_repo(user, name, gitlab)
    
        t1 = Thread(target=shark.npm.main, args=(path, user, name, output,))
        t2 = Thread(target=shark.pip.run, args=(path, user, name, output,))
        t3 = Thread(target=shark.gem.run, args=(path, user, name, output,))
        t4 = Thread(target=shark.cargo.run, args=(path, user, name, output,))
        t5 = Thread(target=shark.go.run, args=(path, user, name, output,))
        
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

def run(user, output, gitlab):
    tmp = f"/tmp/.supplyshark/{user}"
    Path(tmp).mkdir(parents=True, exist_ok=True)
    if gitlab:
        repos = shark.github.gl_get_repos(user)
    else:
        repos = shark.github.gh_get_repos(user)
    c = chunk(repos, multiprocessing.cpu_count())

    procs = []
    for i, s in enumerate(c):
        proc = multiprocessing.Process(target=run_thread, args=(s, user, output, gitlab))
        procs.append(proc)
        proc.start()

    for p in procs:
        p.join()

    shark.file.del_folder(tmp)

def run_file(file, output, gitlab):
    with open(file, "r") as f:
        for ff in f.readlines():
            run(ff.strip(), output, gitlab)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", type=str)
    parser.add_argument("-o", type=str, required=True)
    parser.add_argument("-L", type=str)
    parser.add_argument("-r", type=str)
    parser.add_argument("--gitlab", type=bool)
    args = parser.parse_args()
    
    tmp = "/tmp/.supplyshark"
    if Path(tmp).exists():
        shark.file.del_folder(tmp)

    # Read list of orgs
    if args.L is not None:
        run_file(args.L, args.o, args.gitlab)
    # Specific repository
    elif args.r is not None:
        run_thread(list(args.r), args.u, args.o, args.gitlab)
    # Single user
    else:
        run(args.u, args.o, args.gitlab)