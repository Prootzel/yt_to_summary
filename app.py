#region imports
from pytubefix import YouTube
import re
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
from pprint import pprint
from prozt.prozt import prozt as print
import GPUtil, psutil, platform, cpuinfo

from colorama import Fore

import whisper

import os

from math import ceil

import warnings

from sys import exit

import subprocess
import pyjson5 as json

import webbrowser, pyperclip

from datetime import datetime

from notifypy import Notify
#endregion

#region global functions
warnings.simplefilter(action='ignore', category=FutureWarning)

def print_title(title:str):
    print(("|" + title + "|").center(TERMINAL_WIDTH, "="), fg_color = Fore.GREEN)
    
def print_warning(warning : str):
    print(f"⚠ WARNING ⚠: {warning}", fg_color=Fore.YELLOW)

def print_error(error : str):
    print(f"⚠ ERROR ⚠: {error}", fg_color=Fore.RED)
    
def check_type(to_check, check_type) -> bool:
    return type(to_check) is check_type

def bell():
    print("\a", end = "", flush = True)

def send_notification():
    notification = Notify()
    notification.title = "The summary is done"
    notification.message = "Check back in your terminal to see the result"
    notification.application_name = "Prootzel's Summarizer"
    
    notification.send()

#endregion

#region constants
TERMINAL_WIDTH = os.get_terminal_size().columns

AVAILABLE_TRANSCRIPTION_MODELS = {
    "tiny" : 1,
    "base" : 1,
    "small" : 2,
    "medium" : 5,
    "large" : 10
}
#endregion

#region load settings
with open("settings.json") as f:
    SETTINGS = json.loads(f.read())

print_title("Application Settings")
pprint(SETTINGS, indent=4)

AUD_FOLDER : str = SETTINGS["audio_folder"]
AI_FOLDER : str = "cache/ai"

MAX_TEXT_CHUNK_SIZE = SETTINGS["max_text_chunk_size"]
MIN_SUM_CHUNK_RATIO = SETTINGS["min_sum_chunk_ratio"]
MAX_SUM_CHUNK_RATIO = SETTINGS["max_sum_chunk_ratio"]

TRANSCRIPTION_MODEL = whisper.load_model(SETTINGS["transcription_model"])

SUMMARIZATION_MODEL = pipeline("summarization", SETTINGS["summarization_model"])

#endregion

def print_hw_info():
    def get_size(bytes, suffix="B"):
        """
        Scale bytes to its proper format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor
    print_title("System Information")
    uname = platform.uname()
    print(f"System: {uname.system}")
    print(f"Release: {uname.release}")
    print(f"Version: {uname.version}")
    print(f"Machine: {uname.machine}")
    print(f"Processor: {uname.processor}")
    print(f"Processor: {cpuinfo.get_cpu_info()['brand_raw']}")
    
    print_title("CPU Info")
    print("Physical cores:", psutil.cpu_count(logical=False))
    print("Total cores:", psutil.cpu_count(logical=True))
    cpufreq = psutil.cpu_freq()
    print(f"Max Frequency: {cpufreq.max:.2f}Mhz")
    
    print_title("Memory Information")
    svmem = psutil.virtual_memory()
    print(f"Total: {get_size(svmem.total)}")
    
    print_title("GPU Information")
    
    gpus = GPUtil.getGPUs()
    for i, gpu in enumerate(gpus):
        print(f"GPU {i}:")
        print(f"Name: {gpu.name}")
        print(f"ID: {gpu.id}")
        print(f"UUID: {gpu.uuid}")
        print(f"Memory: {gpu.memoryTotal}")
    
    return gpus[0].memoryTotal

GPU_MEM = print_hw_info()

def verify_settings():
    print_title("Settings Verification")
    def check_transcription_model():
        if(SETTINGS["transcription_model"] not in AVAILABLE_TRANSCRIPTION_MODELS.keys()):
            print_error("Invalid transcription model selected, proceed with care")
        else:
            if(GPU_MEM < (AVAILABLE_TRANSCRIPTION_MODELS[SETTINGS["transcription_model"]] * 1024)):
                print_warning("Not enough VRAM available for selected transcription model")
                
    def verify_setting_types():
        def check_setting_type(name : str, should_be):
            if(not check_type(SETTINGS[name], should_be)):
                print_warning(f"Invalid settings | {name}: {SETTINGS[name]} ({type(SETTINGS[name])} should be {should_be})")
            else:
                print(f"Valid settings | {name}: {SETTINGS[name]} ({type(SETTINGS[name])} should be {should_be})")
        
        check_setting_type("audio_folder", str)
        check_setting_type("transcription_folder", str)
        check_setting_type("output_folder", str)
        
        check_setting_type("max_text_chunk_size", int)
        check_setting_type("min_sum_chunk_ratio", int)
        check_setting_type("max_sum_chunk_ratio", int)
        
        check_setting_type("transcription_model", str)
        check_setting_type("summarization_model", str)
        
        check_setting_type("copy_to_clipboard_once_done", bool)
        check_setting_type("open_slite", bool)
        check_setting_type("send_notification", bool)
        check_setting_type("console_bell", bool)


    verify_setting_types()
    check_transcription_model()

verify_settings()

def main():
    while True:
        try:
            main_loop()
        except KeyboardInterrupt:
            exit()

def verify_url(url : str) -> bool:
    return True

def clean_url(url : str) -> str:
    return url

def main_loop():
    print_title("Prootzel's Video Summarizer")
    while True:
        user_input = input("Enter YouTube Video URL (Ctrl + C to exit program) > ")
        if(verify_url(user_input)):
            break
    
    url = clean_url(user_input)

    video_name = fetch_video(url)
    
    result_path = video_name + ".m4a"
    
    trans_path = SETTINGS["transcription_folder"] + result_path + "_transcription.txt"

    result_path = AUD_FOLDER + result_path

    print(f"Audio downloaded to './{result_path}'")

    if(os.path.isfile(trans_path)):
        print("Transcription already exists, skipping transcription step...")
        
        with open(trans_path) as f:
            transcription = f.read()
    else:
        print("Starting transcription...")

        transcription = transcribe(result_path)

        print("Finished transcription")

        with open(trans_path, "w") as file:
            file.write(transcription)

        print(f"Transcription saved to './{trans_path}'")

    print("Starting summary...")
    _linesep = "=" * 40
    summary_header = [
        f"@{datetime.now()}",
        f"Title: {video_name}",
        f"URL: {url}",
        _linesep,
        ""
    ]

    summary = summarize(transcription, summary_header)


    with open(SETTINGS["output_folder"] + video_name + ".txt", "w") as file:
        file.write(summary)

    print("Done")
    print()
    
    print_title(video_name)
    print(summary)
    
    print()
    
    if(SETTINGS["open_slite"]):
        webbrowser.open("https://slite.com/micro-apps/document-formatter/")
    if(SETTINGS["copy_to_clipboard_once_done"]):
        pyperclip.copy(summary)
    if(SETTINGS["send_notification"]):
        send_notification()
    if(SETTINGS["console_bell"]):
        bell()


def clean_file_name(string : str) -> str:
    return re.sub('[ /><:"|\\?\*,]', "_", string).replace(".", "")

def fetch_video(url) -> str:
    vid = YouTube(url)
    audio_download = vid.streams.get_audio_only()

    entry = YouTube(url).title

    print(f"\nVideo found: {entry}\n")

    filename = clean_file_name(entry)
    
    if(os.path.isfile(AUD_FOLDER + filename)):
        return clean_file_name(entry) + ".m4a"

    print("Downloading Audio...")
    audio_download.download(filename=filename, output_path=AUD_FOLDER)

    print("Download Completed")
    
    return filename

def transcribe(file_path : str) -> str:
    result = TRANSCRIPTION_MODEL.transcribe(file_path, fp16 = False)
    return result["text"]

def summarize(text : str, header : list[str]) -> str:
    num_chunks = ceil(len(text)/(MAX_TEXT_CHUNK_SIZE*.9))
    chunk_divider = round(MAX_TEXT_CHUNK_SIZE * .9)
    
    num_digits = len(str(chunk_divider*MAX_TEXT_CHUNK_SIZE))
    
    sum_chunks = header.copy()
    
    for i in range(num_chunks):
        cur_chunk_index = chunk_divider * i
        next_chunk_index = min(chunk_divider * (i+1), len(text)-1)
        
        chunk_summary = summarize_chunk(text[cur_chunk_index:next_chunk_index])[0]["summary_text"]
        
        sum_chunks.append(chunk_summary)
        
        print(f"({f'{cur_chunk_index}'.rjust(num_digits)} | {f'{next_chunk_index}'.rjust(num_digits)}): {chunk_summary[0:190] + '...' if len(chunk_summary) > 49 else chunk_summary}")
        
    return "\n".join(sum_chunks)

def summarize_chunk(text : str) -> str:
    chunk_size = len(text)
    max_length = chunk_size//MAX_SUM_CHUNK_RATIO
    min_length = chunk_size//MIN_SUM_CHUNK_RATIO
    
    return SUMMARIZATION_MODEL(text, max_length = max_length, min_length = min_length)

main()