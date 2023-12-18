from pathlib import Path
from threading import Thread
import argparse
import multiprocessing
import shark

def chunk(ls, n):
    return [ls[i::n] for i in range(n)]

def run_thread(repos, user, output):
    for repo in repos:
        print(f"[+] Downloading {user}/{repo}")
        path = shark.github.clone_repo(user, repo)
    
        t1 = Thread(target=shark.npm.main, args=(path, user, repo, output,))
        t2 = Thread(target=shark.pip.run, args=(path, user, repo, output,))
        t3 = Thread(target=shark.gem.run, args=(path, user, repo, output,))
        t4 = Thread(target=shark.cargo.run, args=(path, user, repo, output,))
        t5 = Thread(target=shark.go.run, args=(path, user, repo, output,))
        
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

def run(user, output):
    tmp = f"/tmp/.supplyshark/{user}"
    Path(tmp).mkdir(parents=True, exist_ok=True)
    repos = shark.github.get_repos(user)
    
    c = chunk(repos, multiprocessing.cpu_count())

    procs = []
    for i, s in enumerate(c):
        proc = multiprocessing.Process(target=run_thread, args=(s, user, output))
        procs.append(proc)
        proc.start()

    for p in procs:
        p.join()

    shark.file.del_folder(tmp)

def run_file(file, output):
    with open(file, "r") as f:
        for ff in f.readlines():
            run(ff.strip(), output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", type=str)
    parser.add_argument("-o", type=str, required=True)
    parser.add_argument("-L", type=str)
    args = parser.parse_args()
    
    shark.file.del_folder("/tmp/.supplyshark")

    if args.L is not None:
        run_file(args.L, args.o)
    else:
        run(args.u, args.o)
