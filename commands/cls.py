import os

# source: https://stackoverflow.com/questions/517970/how-can-i-clear-the-interpreter-console
def run(arguments : list[str]):
    os.system('cls' if os.name=='nt' else 'clear')