from tkinter import ttk
import ctypes
import json
import os

def TkS(value) -> int:
    return int(ScaleFactor/100*value)



class Env(object):
    def __init__(self):
        self.shortcuts_id = [0, 0, 0]
        self.capture_shortcuts: list = []
        self.call_shortcuts: list = []
        self.exit_shortcuts: list = []
        self.auto_save: bool = None
        self.auto_save_path: str = None
        self.auto_copy: bool = None
        for key, value in self.load_from_file().items():
            setattr(self, key, value)

    def load_from_file(self):
        try:
            with open("settings.json", "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "capture_shortcuts": ["Alt", "A"],
                "call_shortcuts": ["Alt", "S"],
                "exit_shortcuts": ["Alt", "Enter"],
                "auto_save": False,
                "auto_save_path": "",
                "auto_copy": True
            }
        
    def load_from_self(self):
        return {
            "capture_shortcuts": self.capture_shortcuts,
            "call_shortcuts": self.call_shortcuts,
            "exit_shortcuts": self.exit_shortcuts,
            "auto_save": self.auto_save,
            "auto_save_path": self.auto_save_path,
            "auto_copy": self.auto_copy
        }
    
    def save_to_file(self):
        with open("settings.json", "w") as file:
            json.dump(self.load_from_self(), file, indent=4, ensure_ascii=False)
            

class Style(object):
    head1 = ("微软雅黑", 15)
    head2 = ("微软雅黑", 12)
    bg1 = "#FFFFFF"
    bg2 = "#F3F3F3"
    bg3 = "#202020"
    bg4 = "#5F5F5F"
    scrollbar_style = {
        "background": bg4, "lightcolor": bg4, "darkcolor": bg4,
        "troughcolor": bg3, "bordercolor": bg3, "gripcount": 0, "width": 20, 
        "relief": "flat", "borderwidth": 0, "arrowsize": 0
    }
    checkbox_style = {
        "background": bg2, "lightcolor": bg2, "darkcolor": bg2,
        "relief": "flat", "height": 2, "width": 2,
        "image": ""
    }

    def set_scrollbar_style(self):
        style = ttk.Style()
        style.map("TScrollbar", background=[('active', "#737373")])
        style.configure("Vertical.TScrollbar", **self.scrollbar_style)
        style.configure("Horizontal.TScrollbar", **self.scrollbar_style)

    def set_checkbox_style(self):
        style = ttk.Style()
        style.configure("TCheckbutton", **self.checkbox_style)

ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
ctypes.windll.shcore.SetProcessDpiAwareness(1)

user32 = ctypes.windll.user32



VALID_SHORTCUTS_KEYS = (
    "space", "Shift", "Ctrl", "Alt", "Win", "Tab", "Return",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R",
    "S", "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", 
)
KEYS_TRANSFORM = {
    "Shift_L": "Shift", "Shift_R": "Shift",
    "Control_L": "Ctrl", "Control_R": "Ctrl",
    "Alt_L": "Alt", "Alt_R": "Alt",
    "Win_L": "Win", "Win_R": "Win"
}

SCREEN_WIDTH = user32.GetSystemMetrics(0)
SCREEN_HEIGHT = user32.GetSystemMetrics(1)
WINDOW_WIDTH = TkS(280)
WINDOW_HEIGHT = TkS(30)
