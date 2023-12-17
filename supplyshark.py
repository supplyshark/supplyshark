from pathlib import Path
from threading import Thread
import argparse
import multiprocessing
import shark

def chunk(ls, n):
    return [ls[i::n] for i in range(n)]

def run(repos, user, output):
    for repo in repos:
        path = shark.github.clone_repo(user, repo)
    
        t1 = Thread(target=shark.npm.main, args=(path, repo, output,))
        t2 = Thread(target=shark.pip.run, args=(path, repo, output,))
        t3 = Thread(target=shark.gem.run, args=(path, repo, output,))
        t4 = Thread(target=shark.cargo.run, args=(path, repo, output,))
        t5 = Thread(target=shark.go.run, args=(path, repo, output,))

        tt = [t1, t2, t3, t4, t5]
        for t in tt:
            t.start()
            t.join()
    
        shark.file.del_folder(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", type=str, required=True)
    parser.add_argument("-o", type=str, required=True)
    args = parser.parse_args()
    tmp = f"/tmp/.supplyshark/{args.u}"
    Path(tmp).mkdir(parents=True, exist_ok=True)
    repos = shark.github.get_repos(args.u)

    cpu = multiprocessing.cpu_count()
    print(f"[+] Starting SupplyShark with {cpu} processors")
    c = chunk(repos, cpu)

    procs = []
    for i, s in enumerate(c):
        proc = multiprocessing.Process(target=run, args=(s, args.u, args.o))
        procs.append(proc)
        proc.start()
    
    for p in procs:
        p.join()

    shark.file.del_folder(tmp)
