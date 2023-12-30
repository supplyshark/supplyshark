from colorama import Fore
from shutil import rmtree

def out(msg, output):
    print(f"{Fore.CYAN}{msg}{Fore.RESET}")
    with open(output, "a") as out:
        print(msg, file=out)

def del_folder(path):
    rmtree(path)