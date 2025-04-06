import ctypes
import json
from pathlib import Path


ctypes.windll.shcore.SetProcessDpiAwareness(1)
user32 = ctypes.windll.user32


class ClassMethodMeta(type):
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        for attr_name, attr_value in attrs.items():
            if callable(attr_value):
                new_attrs[attr_name] = classmethod(attr_value)
            else:
                new_attrs[attr_name] = attr_value
        return super().__new__(cls, name, bases, new_attrs)


class Shortcuts(object):
    valid_shortcuts = (
        "space", "Shift", "Ctrl", "Alt", "Win", "Tab", "Return",
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R",
        "S", "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "Escape", "F1", "F2", "F3", "~"
    )
    key_tranform = {
        "Shift_L": "Shift", "Shift_R": "Shift", "Control_L": "Ctrl", "Control_R": "Ctrl",
        "Alt_L": "Alt", "Alt_R": "Alt", "Win_L": "Win", "Win_R": "Win",
        "XF86AudioMute": "F1", "XF86AudioLowerVolume": "F2", "XF86AudioRaiseVolume": "F3", 
        "grave": "~",
    }

    @staticmethod
    def clear(keys: list):
        keys[:] = list(filter(lambda key: key in Shortcuts.valid_shortcuts, keys))


class State(object):
    is_capturing: bool = False
    is_resizing: bool = False
    is_saving: bool = False
    force_show_magnifier: bool = False

    @classmethod
    def restore_default(cls):
        cls.is_capturing = False
        cls.is_resizing = False
        cls.force_show_magnifier = False


class Window(object):
    def TKS(value, scale_factor: float = ctypes.windll.shcore.GetScaleFactorForDevice(0)) -> int:
        return int(scale_factor / 100 * value)
    
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    setting_window_width = TKS(250)
    window_title = "瞬影"
    window_width = TKS(200)
    window_height = TKS(30)


class Size(object):
    num: list = [1, 2, 3, 5, 8, 10, 12, 18, 20, 25, 30, 35]
    num: list = [Window.TKS(i) for i in num]


class File(object):
    config_dir = (Path("src") / "config").resolve()
    image_dir = (Path("src") / "image").resolve()
    temp_dir = (Path("src") / "Temp").resolve()
    config_dir = (Path("src") / "config").resolve()
    image_dir = (Path("src") / "image").resolve()
    temp_dir = (Path("src") / "Temp").resolve()
    default_save_dir = image_dir / "default"
    history_dir = image_dir / "history"
    ico_dir = image_dir / "ico"
    help_file = config_dir / "help.html"
    setting_config = config_dir / "settings.json"
    default_setting = config_dir / "default.json"
    style_config = config_dir / "style.json"
    icon_file = ico_dir / "favicon.ico"
    copy_ico = ico_dir / "copy.png"
    save_ico = ico_dir / "save.png"
    kill_ico = ico_dir / "kill.png"


class Env(object):
    def __init__(self):
        self.capture_shortcuts: list = []
        self.call_shortcuts: list = []
        self.nail_shortcuts: list = []
        self.auto_copy: bool = None
        self.auto_save: bool = None
        self.auto_conceal: bool = None
        self.auto_clear: bool = None
        self.auto_save_path: str = None
        self.ocr_config: dict = None
        self.edit_exe_path: str = None
        self.load_from_file()
        for key, value in self.load_from_file().items():
            setattr(self, key, value)
        for shortcuts in [self.capture_shortcuts, self.call_shortcuts, self.nail_shortcuts]:
            Shortcuts.clear(shortcuts)

    def load_from_file(self) -> dict:
        try:
            with open(File.setting_config, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_info("all")
        
    def load_from_self(self):
        return {
            "capture_shortcuts": self.capture_shortcuts,
            "call_shortcuts": self.call_shortcuts,
            "nail_shortcuts": self.nail_shortcuts,
            "auto_copy": self.auto_copy,
            "auto_save": self.auto_save,
            "auto_conceal": self.auto_conceal,
            "auto_clear": self.auto_clear,
            "auto_save_path": self.auto_save_path,
            "ocr_config": self.ocr_config,
            "edit_exe_path": self.edit_exe_path
        }
    
    def save_to_file(self):
        with open(File.setting_config, "w", encoding="utf-8") as file:
            json.dump(self.load_from_self(), file, indent=4, ensure_ascii=False)
            
    def get_default_info(self, attr: str):
        if not Path(File.default_setting).exists():
            raise FileNotFoundError("Default File Not Found!")
        with open(File.default_setting, "r", encoding="utf-8") as file:
            data = json.load(file)
        if attr == "all":
            return data
        return data[attr]


class Style(metaclass=ClassMethodMeta):
    with open(File.style_config, "r", encoding="utf-8") as file:
        __style_dict = json.load(file)
    
    def get(cls, *args):
        attr_dict = cls.__style_dict
        for arg in args[:-1]:
            attr_dict = attr_dict[arg]
        attr = attr_dict[args[-1]]
        if isinstance(attr, str):
            try:
                return Window.TKS(float(attr))
            except ValueError:
                return attr
        return attr


class Tags(object):
    bg_image = "bg_image"
    border_rect = "border_rect"
    zoom_image = "zoom_image"
    vert_axis = "vert_axis"
    horiz_axis = "horiz_axis"
    pos_tip ="pos_tip"
    pos_bg = "pos_bg"
    rgb_tip = "rgb_tip"
    rgb_bg = "rgb_bg"
    rect_size_tip = "rect_size_tip"
    rect_size_bg = "rect_size_bg"
    embed_image = "embed_image"
    border_window = "border_window"
