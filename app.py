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

import pyjson5 as json

import webbrowser, pyperclip

from datetime import datetime

from notifypy import Notify

import gui

import sys

from customtkinter import StringVar

from util_classes import YTSummary

from threading import Thread

import json as basic_json

import subprocess
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




# class main_window():
#     def __init__(self):
#         super().__init__(parent=None)
#         self.setWindowTitle("Prootzel's Summarizer")
        
#         self.setGeometry(100, 100, 1600, 900)
        
#         self._create_tool_bar()
#         self._create_central_widget()
    
#     def _create_central_widget(self):
#         self.central_widget = QWidget(self)
        
#         layout = QGridLayout(self.central_widget)
        
        
        
#         layout.addWidget(QLabel("Hello!"), 0, 0, 1, 2)
        
        
#         self.input = QLineEdit()
#         self.input.setFixedHeight(40)
#         layout.addWidget(self.input, 1, 0)
        
#         self.input_send = QPushButton(QIcon("resources/icons/send-icon.svg"), "")
#         self.input_send.setFixedSize(40, 40)
#         layout.addWidget(self.input_send, 1, 1)
        
#         self.central_widget.setLayout(layout)
#         #self.input_widget.setLayout(QHBoxLayout(self.input_widget))
        
#         self.setCentralWidget(self.central_widget)
    
#     def _create_menu(self):
#         self.menu = self.menuBar()
#         self.options = self.menu.addMenu("&Menu")
#         self.options.addAction("&Exit", self.close)
        
#     def _create_tool_bar(self):
#         self.tools = QToolBar()
#         self.tools.addAction("Wawa", self.close)
        
#         spacer = QWidget()
#         spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
#         self.tools.addWidget(spacer)
        
#         settings_icon = QIcon("resources/icons/setting-icon.svg")
        
#         self.tools.addAction(settings_icon, "", self.close).setToolTip("Settings")
        
#         self.tools.setMovable(False)
#         self.tools.setFixedWidth(50)
#         self.tools.setStyleSheet("QToolButton {padding-top: 5px; padding-bottom: 20px;}")
#         self.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self.tools)
    
#     def _create_status_bar(self):
#         self.status = QStatusBar()
#         self.status.showMessage("Ready")
#         self.setStatusBar(self.status)
        
#     def set_status(self, status : str):
#         self.status.showMessage(status)
        
    

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

#region GUI

#endregion

#region load settings
with open("settings.json") as f:
    SETTINGS = json.loads(f.read())

if(not SETTINGS["skip_intro"]):
    print_title("Application Settings")
    pprint(SETTINGS, indent=4)

AUD_FOLDER : str = SETTINGS["audio_folder"]
AI_FOLDER : str = "cache/ai"
OUTPUT_FOLDER = SETTINGS["output_folder"]

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

def load_chats() -> list[YTSummary]:
    chats = []
    
    for filename in os.listdir(OUTPUT_FOLDER):
        if(not filename.endswith(".json")):
            continue
        with open(OUTPUT_FOLDER + filename, "r") as f:
            content = basic_json.loads(f.read())
        
        chats.append(YTSummary(**content))
    
    return chats

def verify_settings(GPU_MEM):
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
        check_setting_type("skip_intro", bool)


    verify_setting_types()
    check_transcription_model()


def main():
    if(not SETTINGS["skip_intro"]):
        GPU_MEM = print_hw_info()
        verify_settings(GPU_MEM)
    print_title("Prootzel's Video Summarizer")
    
    while True:
        try:
            main_loop()
        except KeyboardInterrupt:
            exit()

def verify_url(url : str) -> bool:
    if(url.startswith("!") or not url.startswith("https://") or not "youtube" in url):
        return False
    return True

def clean_url(url : str) -> str:
    return url

def verify_command(command : str) -> bool:
    if(command.startswith("!")):
        return True
    return False

def handle_command(command : str):
    command = command[1:]
    command_with_args = command.split(" ")
    command = command_with_args[0]
    args = command_with_args[1:]
    if(os.path.isfile("commands/" + command + ".json")):
        
        if(os.path.isfile("commands/" + command + ".py")):
            command_module = getattr(__import__(f"commands", globals(), locals(), [command]), command)
            command_module.run(args)
        else:
            print_error("Command is faulty")
        
    else:
        print_error("Command not found")

def main_loop():
    while True:
        user_input = input("Enter YouTube Video URL (Ctrl + C to exit program) > ")
        if(verify_url(user_input)):
            break
        elif(verify_command(user_input)):
            handle_command(user_input)
            return
        
    download_and_sum_url(user_input)

def download_and_sum_url(user_input):
    url = clean_url(user_input)

    video_info = fetch_video(url)
    try:
        video_name = video_info["name"]
        video_channel = video_info["channel"]
    except:
        video_name = video_info[:-4]
        video_channel = "undefined"
    
        
    
    result_path = clean_file_name(video_name)
    
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
    
    summary = {
        "time": f"{datetime.now()}",
        "title": video_name,
        "url": url,
        "channel": video_channel
    }

    summary_content = summarize(transcription)
    
    summary |= {"content": summary_content}


    with open(SETTINGS["output_folder"] + clean_file_name(video_name) + ".json", "w") as file:
        basic_json.dump(summary, file, indent=4)

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
    load_chats()
    update_chat_buttons()


def clean_file_name(string : str) -> str:
    return re.sub(r'[ /><:"|\\?\*,]', "_", string).replace(".", "")

def fetch_video(url) -> dict:
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
    
    return {
        "name" : entry,
        "channel" : vid.channel_id
    }

def transcribe(file_path : str) -> str:
    result = TRANSCRIPTION_MODEL.transcribe(file_path, fp16 = False)
    return result["text"]

def summarize(text : str) -> str:
    num_chunks = ceil(len(text)/(MAX_TEXT_CHUNK_SIZE*.9))
    chunk_divider = round(MAX_TEXT_CHUNK_SIZE * .9)
    
    num_digits = len(str(chunk_divider*MAX_TEXT_CHUNK_SIZE))
    
    
    threads = [None] * num_chunks
    results = [None] * num_chunks
    
    for i in range(num_chunks):
        cur_chunk_index = chunk_divider * i
        next_chunk_index = min(chunk_divider * (i+1), len(text)-1)
        
        
        threads[i] = Thread(target=lambda: summarize_chunk(text[cur_chunk_index:next_chunk_index], results, i))
        threads[i].start()
        
        #print(f"({f'{cur_chunk_index}'.rjust(num_digits)} | {f'{next_chunk_index}'.rjust(num_digits)}): {chunk_summary[0:190] + '...' if len(chunk_summary) > 49 else chunk_summary}")
    
    for t in threads:
        t.join()
    
    return "\n".join(results)

def summarize_chunk(text : str, outputlist, index):
    chunk_size = len(text)
    max_length = chunk_size//MAX_SUM_CHUNK_RATIO
    min_length = chunk_size//MIN_SUM_CHUNK_RATIO
    
    outputlist[index] = SUMMARIZATION_MODEL(text, max_length = max_length, min_length = min_length)[0]["summary_text"]

window = gui.Window("Summarizer", "1600x900")

#toolbar = tk.Frame(window)
#toolbar.grid(row=0, column=0, sticky=tk.W)
#_icon = tk.PhotoImage(file="resources/icons/setting-icon.png")
#options = gui.Button(window, text="", icon_name="setting-icon.png", command=print)

def input_callback(user_input):
    if(verify_url(user_input)):
        download_and_sum_url(user_input)
        load_chats()
        update_chat_buttons()
    elif(verify_command(user_input)):
        handle_command(user_input)
        return
    
def start_callback(user_input):
    Thread(target=input_callback, args=[user_input]).start()

def open_settings():
    gui.PopUp("Not available")

chatbar = gui.ScrollableFrame(window, "#2B2A2A", 50, 0, 330, 900)
chatbar.grid_propagate(flag=False)
chatbar.lower()

chats = load_chats()
chat_buttons = []
def update_chat_buttons():
    for btn in chat_buttons:
        btn.destroy()
    for i, chat in enumerate(chats):
        if(len(chat.title)>30):
            title = chat.title[:42] + "..."
        else:
            title = chat.title
        
        
        button = gui.Button(
            chatbar, title, None, lambda i=i:change_chat(i), 280, 30
        )
        
        button.grid(row=i, column = 0, padx = 40, pady = 5)
        chat_buttons.append(button)

def new_yt_summary():
    for ui in current_overlay_ui:
        ui.destroy()
    
    inputbox_overlay.place(x=100000, y=0)
    inputbox.configure(state = "normal")
    output_label.set_text("Enter link below")

update_chat_buttons()


inputbox_overlay = gui.Frame(window, "transparent", 420, 814, 1140, 53, 20)
current_overlay_ui = []




def change_chat(i):
    for ui in current_overlay_ui:
        ui.destroy()
    
    cur_chat = chats[i]
    print(f"Changed to chat {i}")
    output_label.set_text(chats[i].content.replace("\n", "\n\n"))
    
    
    
    
    if(cur_chat.type == "YTSummary"):
        inputbox_overlay.grid_propagate(False)
        inputbox_overlay.columnconfigure(0, weight=0)
        inputbox_overlay.columnconfigure(1, weight=1)
        print("Detected Summary")
        inputbox_overlay.configure(fg_color = "#5C006B")
        inputbox_overlay.lift(inputbox)
        
        description = f"by {cur_chat.channel} (@{cur_chat.time})"
        description = description if len(description) < 70 else f"by {cur_chat.channel[:70-len(description)]} (@{cur_chat.time})"
        
        title = cur_chat.title if len(cur_chat.title) < 70 else cur_chat.title[:70]
        title_label = gui.TextLabel(inputbox_overlay, cur_chat.title, None, None, 30)
        info_label = gui.TextLabel(inputbox_overlay, description)
        
        current_overlay_ui.append(title_label)
        current_overlay_ui.append(info_label)
        
        def open_in_browser(url):
            webbrowser.open(url)
        
        def open_in_editor(fp):
            subprocess.call(["notepad.exe", fp])
        
        url = cur_chat.url
        open_url_button = gui.Button(inputbox_overlay, "Open in Browser", None, lambda url=url:open_in_browser(url), 280, 30)
        current_overlay_ui.append(open_url_button)
        
        fp = SETTINGS["output_folder"] + clean_file_name(cur_chat.title) + ".json"
        open_json_button = gui.Button(inputbox_overlay, "Open in Text Editor", None, lambda fp=fp:Thread(target=open_in_editor(fp)).start(), 280, 30)
        current_overlay_ui.append(open_json_button)
        
        
        title_label.grid(row=0, column=0)
        info_label.grid(row=1, column=0)
        
        open_url_button.grid(row=0, column=1, sticky="e", padx=50)
        open_json_button.grid(row=1, column=1, sticky="e", padx=50)
        
        inputbox.configure(state = "disabled")
    
    else:
        inputbox.configure(state = "normal")
        inputbox.lift(inputbox_overlay)
    
    
    for cur_index, button in enumerate(chat_buttons):
        if(cur_index == i):
            button.can_change_state = False
            button.configure(fg_color = "#5C006B")
        else:
            button.can_change_state = True
            button.configure(fg_color = gui.BUTTON_COLOR)

input_var = StringVar(window)

inputbox = gui.InputBox(window, "Hello, world!", input_var, start_callback, height=53)
inputbox.place(x=420, y=814, relwidth = 1140/1600)

toolbar = gui.Frame(window, "#1E1E1E", x=0, y=0, width=80, height=900, corner_radius=0)

# Not there yet...
#settings_button = gui.Button(window, "", command=open_settings, icon_name="setting-icon.png", width=70, height=70)
#settings_button.place(x=5, y=820)

add_button = gui.Button(window, "+", None, command=new_yt_summary, width=70, height=70)
add_button.place(x=5, y=740)

with open("lorem_ipsum.txt") as f:
    lorem = f.read()

output_frame = gui.ScrollableFrame(window, "transparent", x=420, y=40, width=1440, height=750, corner_radius=0)
output_frame.place(x=420, y=40)

output_label = gui.TextLabel(output_frame, lorem, width=1140, height=750)
output_label.grid(row=0, column=0)

if len(chat_buttons) > 0:
    change_chat(0)

sys.exit(window.mainloop())