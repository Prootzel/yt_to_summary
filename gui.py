import customtkinter as tk
from PIL import Image

ICON_PATH = "resources/icons/"
BG_COLOR = "#121212"
BG_LIGHT = "#1e1e1e"

BUTTON_CORNER_RADIUS : int = 5
BUTTON_COLOR = "#ff0000"
BUTTON_COLOR_HIGHLIGHT = "#ffff00"
BUTTON_COLOR_PRESS = "#00ff00"

TEXT_COLOR = ("#ffffff", "#000000")

class Button(tk.CTkLabel):
    def __init__(self, master, text : str, icon_name : str, command : callable):
        self.is_focussed = False
        
        light = Image.open(ICON_PATH + icon_name)
        self.icon = tk.CTkImage(light_image=light)
        super().__init__(master, text="", image=self.icon, fg_color=BUTTON_COLOR, corner_radius=BUTTON_CORNER_RADIUS,width=100, height=100)
        
        print(ICON_PATH + icon_name)
        
        self.event = command
        self.bind("<Button-1>", lambda _: self.press())
        self.bind("<ButtonRelease-1>", lambda _: self.release())
        
        self.bind("<Enter>", lambda _: self.hover_enter())
        self.bind("<Leave>", lambda _: self.hover_exit())
        
    def press(self):
        self.configure(fg_color=BUTTON_COLOR_PRESS)
        self.event()
    
    def release(self):
        if(not self.is_focussed):
            self.configure(fg_color=BUTTON_COLOR)
        else:
            self.hover_enter()
        
    def hover_enter(self):
        self.configure(fg_color=BUTTON_COLOR_HIGHLIGHT)
        self.is_focussed = True
    
    def hover_exit(self):
        self.configure(fg_color=BUTTON_COLOR)
        self.is_focussed = False
    
class Window(tk.CTk):
    def __init__(self, name : str, size : str | tuple[int, int]):
        super().__init__()
        self.title(name)
        self.geometry(size)
        self.configure(bg_color=BG_COLOR)
        
class InputBox(tk.CTkEntry):
    def __init__(self, master, placeholder_text, textvariable, enter_callback : callable, clear_on_enter : bool = True):
        super().__init__(master, placeholder_text=placeholder_text, textvariable=textvariable)
        
        self.event = enter_callback
        self.clear_on_enter = clear_on_enter
        
        self.bind("<Return>", self.enter)
    
    def enter(self, _):
        self.event()
        if(self.clear_on_enter):
            self.clear()
    
    def clear(self):
        self._entry.delete(0, "end")