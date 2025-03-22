import ctypes
import json
from pathlib import Path



ctypes.windll.shcore.SetProcessDpiAwareness(1)
user32 = ctypes.windll.user32




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


class Window(object):
    def TKS(value, scale_factor: float = ctypes.windll.shcore.GetScaleFactorForDevice(0)) -> int:
        return int(scale_factor / 100 * value)
    
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    setting_window_width = TKS(250)
    window_title = "瞬影"
    window_width = TKS(200)
    window_height = TKS(30)

    
class File(object):
    config_dir = (Path("src") / "config").resolve()
    image_dir = (Path("src") / "image").resolve()
    temp_dir = (Path("src") / "Temp").resolve()
    config_dir = (Path("src") / "config").resolve()
    image_dir = (Path("src") / "image").resolve()
    temp_dir = (Path("src") / "Temp").resolve()
    default_save_dir = image_dir / "default_save"
    ico_dir = image_dir / "ico"
    setting_config = config_dir / "settings.json"
    default_setting = config_dir / "default.json"
    style_config = config_dir / "style.json"
    icon_file = ico_dir / "favicon.ico"
    copy_ico = ico_dir / "copy.png"
    save_ico = ico_dir / "save.png"
    kill_ico = ico_dir / "kill.png"


class Env(object):
    def __init__(self):
        self.shortcuts_id = [0, 0, 0]
        self.capture_shortcuts: list = []
        self.call_shortcuts: list = []
        self.exit_shortcuts: list = []
        self.auto_copy: bool = None
        self.auto_save: bool = None
        self.auto_save_path: str = None
        self.auto_delete: bool = None
        self.auto_delete_upper: int = None
        self.ocr_config: dict = None
        self.edit_exe_path: str = None
        self.load_from_file()
        for key, value in self.load_from_file().items():
            setattr(self, key, value)
        for shortcuts in [self.capture_shortcuts, self.call_shortcuts, self.exit_shortcuts]:
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
            "exit_shortcuts": self.exit_shortcuts,
            "auto_copy": self.auto_copy,
            "auto_save": self.auto_save,
            "auto_save_path": self.auto_save_path,
            "auto_delete": self.auto_delete,
            "auto_delete_upper": self.auto_delete_upper,
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


class Style(object):
    with open(File.style_config, "r", encoding="utf-8") as file:
        __STYLE_DICT = json.load(file)

    @classmethod
    def get(cls, attr: str, id: int) -> any:
        return cls.__STYLE_DICT[attr][id]

