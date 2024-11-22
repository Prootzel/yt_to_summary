import os
from prozt.prozt import prozt as print
import pyjson5
from colorama import Fore

def full_help():
    print("Name".ljust(20), end="", sep="", fg_color=Fore.GREEN)
    print("Aliases".ljust(20), end="", sep="", fg_color=Fore.YELLOW)
    print("Description")
    for file in os.listdir("commands"):
        if(file.endswith(".json")):
            with open("commands/"+file) as f:
                json = pyjson5.loads(f.read())
                
                command_name = json["name"]
                command_aliases = json["aliases"]
                help_text = json["short_help"]
                
                print(command_name.ljust(20), end="", sep="", fg_color = Fore.GREEN)
                print(str(command_aliases)[1:-1].replace("'", "").ljust(20), end="", sep="", fg_color = Fore.YELLOW)
                print(help_text.ljust(30))
    
def help_for_command(command : str):
    file_location = f"commands/{command}.json"
    if(os.path.isfile(file_location)):
        with open(file_location) as f:
            json = pyjson5.loads(f.read())
            print("Name:        ", sep="", end="")
            print(json['name'], fg_color=Fore.GREEN)
            print("Aliases:     ", sep="", end="")
            print(str(json['aliases'])[1:-1].replace("'", ""), fg_color=Fore.YELLOW)
            print("Description: " + json['long_help'].replace('\n', '\n' + ' ' * 13))
def run(arguments : list[str]):
    if(len(arguments) == 0):
        full_help()
    else:
        for arg in arguments:
            help_for_command(arg)