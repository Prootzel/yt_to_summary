import customtkinter as tk
from PIL import Image


ICON_PATH = "resources/icons/"
BG_COLOR = "#121212"
BG_LIGHT = "#1e1e1e"

BUTTON_CORNER_RADIUS : int = 5
BUTTON_COLOR = "#3c4042"
BUTTON_COLOR_HIGHLIGHT = "#606368"
BUTTON_COLOR_PRESS = "#ea80fc"
BUTTON_TRANSITION_TIME = 300

FONT = "Roboto"
FONT_SIZE_P = 20

TEXT_COLOR = ("#ffffff", "#000000")

ANIM_STEP = 30

def lerp(a : float, b : float, t: float) -> float:
    return a + t * (b-a)

def color_lerp(a : tuple, b : tuple, t : float) -> tuple[int, int, int]:
    red = lerp(a[0], b[0], t)
    green = lerp(a[1], b[1], t)
    blue = lerp(a[2], b[2], t)
    
    return (red, green, blue)

def code_to_color(code : str) -> tuple[str, str, str]:
    red = int("0x" + code[1:3], 0)
    green = int("0x" + code[3:5], 0)
    blue = int("0x" + code[5:7], 0)
    
    return (red, green, blue)

def color_to_code(color : tuple[int, int, int]) -> str:
    return "#" + hex(color[0])[2:] + hex(color[1])[2:] + hex(color[2])[2:]

class Button(tk.CTkLabel):
    def __init__(self, master, text : str, icon_name : str, command : callable, width, height):
        self.is_focussed = False
        
        self.can_change_state = True
        
        if(icon_name):
            light = Image.open(ICON_PATH + icon_name)
            self.icon = tk.CTkImage(light_image=light)
            super().__init__(master, text="", image=self.icon, fg_color=BUTTON_COLOR, corner_radius=BUTTON_CORNER_RADIUS,width=width, height=height)
        
        else:
            super().__init__(master, text=text, fg_color=BUTTON_COLOR, corner_radius=BUTTON_CORNER_RADIUS,width=width, height=height)
        
        
        self.event = command
        self.bind("<Button-1>", lambda _: self.press())
        self.bind("<ButtonRelease-1>", lambda _: self.release())
        
        self.bind("<Enter>", lambda _: self.hover_enter())
        self.bind("<Leave>", lambda _: self.hover_exit())
        
        self.cur_anim_t = 0
        self.transition_time = BUTTON_TRANSITION_TIME
        
    def press(self):
        if(self.can_change_state):
            self.configure(fg_color=BUTTON_COLOR_PRESS)
            self.event()
    
    def release(self):
        if(self.can_change_state):
            if(not self.is_focussed):
                self.configure(fg_color=BUTTON_COLOR)
            else:
                self.hover_enter()
        
    def hover_enter(self):
        if(self.can_change_state):
            self.configure(fg_color=BUTTON_COLOR_HIGHLIGHT)
            self.is_focussed = True
    
    def hover_exit(self):
        if(self.can_change_state):
            self.configure(fg_color=BUTTON_COLOR)
            self.is_focussed = False
    

class Window(tk.CTk):
    def __init__(self, name : str, size : str | tuple[int, int]):
        super().__init__()
        self.title(name)
        self.geometry(size)
        self.configure(bg_color=BG_COLOR)
        
class InputBox(tk.CTkEntry):
    def __init__(self, master, placeholder_text, textvariable, enter_callback : callable, clear_on_enter : bool = True, **kwargs):
        if(textvariable == None):
            textvariable = tk.StringVar(master)
        
        super().__init__(master, bg_color=BG_LIGHT, corner_radius=5, placeholder_text=placeholder_text, textvariable=textvariable, **kwargs)
        
        self.event = enter_callback
        self.clear_on_enter = clear_on_enter
        
        self.bind("<Return>", self.enter)
    
    def enter(self, _):
        self.event(self._textvariable.get())
        if(self.clear_on_enter):
            self.clear()
    
    def clear(self):
        self._entry.delete(0, "end")


class TextLabel(tk.CTkLabel):
    def __init__(self, master, text, width = None, height = None, font_size_override = 0):
        self.textvar = tk.StringVar(master=master, value=text)
        
        if(font_size_override == 0):
            self.font = tk.CTkFont("Roboto", FONT_SIZE_P)
        else:
            self.font = tk.CTkFont("Roboto", font_size_override)
        
        if(width == None): width = 0
        if(height == None): height = 0
        super().__init__(master, width, height, corner_radius=0, font=self.font, text=text, compound="left", justify="left", anchor="w", wraplength=width)
        
    def set_text(self, new_text : str):
        self.configure(text=new_text)

class Frame(tk.CTkFrame):
    def __init__(self, master, color, x=0, y=0, width=None, height=None, corner_radius = 5):
        super().__init__(master, width=width, height=height, fg_color=color, corner_radius=corner_radius)
        self.place(x=x, y=y)

class ScrollableFrame(tk.CTkScrollableFrame):
    def __init__(self, master, color, x=0, y=0, width=None, height=None, corner_radius = 5):
        super().__init__(master, width=width, height=height, fg_color=color, corner_radius=corner_radius)
        self.place(x=x, y=y) 

class PopUp(tk.CTkToplevel):
    def __init__(self, text):
        super().__init__(height=200, width=450, takefocus=True)
        tk.CTkLabel(self, text=text)

if(__name__ == "__main__"):
    
    app = Window("Window", "600x800")
    
    ind = 0
    
    def callback():
        print(f"Button pressed")
    
    
    button = Button(app, "Hewwo", "setting-icon.png", callback)
    button.grid(row=0, column=0)
    
    inbox = InputBox(app, "owo", None, print)
    inbox.grid(row=1, column=0)
    
    app.mainloop()