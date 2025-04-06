import os
import io
import hashlib
import importlib
from typing import TYPE_CHECKING, Callable, Sequence
from ctypes import wintypes
from re import findall
from time import time, sleep

from threading import Thread
from subprocess import check_output
from tkinter import Canvas, filedialog, messagebox

import keyboard
from PIL import Image
if TYPE_CHECKING:
    import pyperclip
    import win32clipboard


from Setting import *


class HistoryRecord(metaclass=ClassMethodMeta):
    _list: list[Path] = []
    _page = 0
    File.history_dir.mkdir(parents=True, exist_ok=True)

    def load_from_dir(cls):
        cls._list = list(File.history_dir.glob("*.[pP][nN][gG]"))

    def append(cls, image: Image.Image):
        path = File.history_dir / ImageUtils.get_random_image_name(image)
        image.save(path)
        cls._list.append(path)

    def remove_current_image(cls) -> bool:
        if cls.empty():
            return False
        cls._list.pop(cls._page)
        cls._page = max(0, cls._page - (cls._page == len(cls._list)))
        return True

    def turn_page(cls, is_left: bool):
        new_page = max(0, min(cls._page - 1 if is_left else cls._page + 1, len(cls._list) - 1))
        if new_page == cls._page:
            return False
        cls._page = new_page
        return True

    def turn_last_page(cls):
        cls._page = len(cls._list) - 1

    def current_image(cls) -> Image.Image | None:
        try:
            image_path = cls._list[cls._page]
        except IndexError:
            return None
        if image_path.exists():
            return Image.open(cls._list[cls._page]).convert("RGB")
        if cls.remove_current_image():
            return cls.current_image()

    def current_image_path(cls) -> Path:
        return cls._list[cls._page]

    def empty(cls):
        # 返回列表的长度是否为0
        return len(cls._list) == 0


class ScreenshotUtils(object):
    """
    截图的关键是坐标；这个类管理着图片的引用和截图坐标；
    """
    magnifier_coords: tuple[int, int] = None
    rect_coords: tuple[int, int, int, int] = None

    def __init__(self):
        # 截图时的临时变量
        self.start_x = self.start_y = self.end_x = self.end_y = -1
        self.move_start_x = self.move_start_y = 0
        self.current_image: Image.Image = None

    def initialize_coords(self):
        self.start_x = self.start_y = self.end_x = self.end_y = -1
        ScreenshotUtils.rect_coords = [0, 0, Window.screen_width, Window.screen_height]

    def initialize_temp_variables(self):
        self.current_image = None
        self.magnifier_coords = None
        self.rect_coords = None
        self.local_canvas = None

    def get_default_screenshot_coords(self):
        self.start_x = self.start_y = 0
        self.end_x = Window.screen_width
        self.end_y = Window.screen_height
    

class RedrawUtils(metaclass=ClassMethodMeta):
    """
    Since the selection area is actually a window that can obscure the image item,
    we need to redraw the image item that is obscured by the window inside the window itself.
    """ 
    _redraw_sequence: dict = {"rectangle": 0, "image": 1, "text": 2, "line": 3}
    # __redraw_items维护了一个carrier_master中的图案id和carrier子类重绘的图案id的映射关系
    _redraw_items: dict[str, str] = dict()
    _redraw_carrier: Canvas = None
    _carrier_master: Canvas = None

    def append_redraw_tags(cls, *args):
        for item in args:
            item = cls._carrier_master.find_withtag(item)
            if item is not None and len(item) != 0:
                cls._redraw_items[item[0]] = ""

    def set_redraw_carrier(cls, value: Canvas):
        cls._redraw_carrier = value
        cls._carrier_master = value.master
        for item in cls._redraw_items:
            cls._redraw_items[item] = ""

    def get_overlapping_items(cls):
        overlapping = cls._carrier_master.find_overlapping(*ScreenshotUtils.rect_coords)
        overlapping = filter(lambda item: item in cls._redraw_items, overlapping)
        return sorted(overlapping, key=lambda item: cls._redraw_sequence[cls._carrier_master.type(item)])
    
    def delete_unredraw_items(cls, overlapping: list):
        conceal_items = filter(lambda item: item not in overlapping, cls._redraw_items.keys())
        for item in conceal_items:
            redraw_item = cls._redraw_items[item]
            cls._redraw_carrier.delete(redraw_item)
            cls._redraw_items[item] = ""

    def redraw(cls):
        if ScreenshotUtils.rect_coords is None:
            return
        overlapping = cls.get_overlapping_items()
        cls.delete_unredraw_items(overlapping)
        func = lambda figure: getattr(cls, f"redraw_{figure}")
        for overlap in overlapping:
            try:
                drawn_item = func(cls._carrier_master.type(overlap))(overlap)
                cls._redraw_items[overlap] = drawn_item
            except (KeyError, IndexError):
                pass
            
    def redraw_text(cls, overlap: str) -> str:
        coords = cls.map_coords(overlap)
        text = cls._carrier_master.itemcget(overlap, "text")
        map_item = cls._redraw_items[overlap]
        if map_item == "":
            styles = ("anchor", "fill", "font")
            style_dict = {style: cls._carrier_master.itemcget(overlap, style) for style in styles}
            map_item = cls._redraw_carrier.create_text(*coords, text=text, **style_dict)
        else:
            cls._redraw_carrier.itemconfig(map_item, text=text)
            cls._redraw_carrier.coords(map_item, *coords)
        return map_item

    def redraw_rectangle(cls, overlap: str) -> str:
        coords = cls.map_coords(overlap)
        map_item = cls._redraw_items[overlap]
        if map_item == "":
            styles = ("fill", "width", "outline")
            style_dict = {style: cls._carrier_master.itemcget(overlap, style) for style in styles}
            map_item = cls._redraw_carrier.create_rectangle(*coords, **style_dict)
        else:
            cls._redraw_carrier.coords(map_item, *coords)
        return map_item
    
    def redraw_line(cls, overlap: str) -> str:
        coords = cls.map_coords(overlap)
        map_item = cls._redraw_items[overlap]
        if map_item == "":
            styles = ("width", "fill")
            style_dict = {style: cls._carrier_master.itemcget(overlap, style) for style in styles}
            map_item = cls._redraw_carrier.create_line(*coords, **style_dict)
        else:
            cls._redraw_carrier.coords(map_item, *coords)
        return map_item

    def redraw_image(cls, overlap: str) -> str:
        coords = cls.map_coords(overlap)
        imgtk = cls._carrier_master.itemcget(overlap, "image")
        map_item = cls._redraw_items[overlap]
        if map_item == "":
            map_item = cls._redraw_carrier.create_image(*coords, image=imgtk, anchor="nw")
        else:
            cls._redraw_carrier.itemconfig(map_item, image=imgtk)
            cls._redraw_carrier.coords(map_item, *coords)
        cls._redraw_carrier.imgtk = imgtk
        return map_item

    def map_coords(cls, overlap) -> tuple[int, int] | tuple[int, int, int, int]:
        def _map(x, y):
            return x - inner_bbox[0], y - inner_bbox[1]
        inner_bbox = ScreenshotUtils.rect_coords
        points = cls._carrier_master.coords(overlap)
        if len(points) == 2:
            return _map(*points)
        else:
            x1, y1, x2, y2 = points
            return *_map(x1, y1), *_map(x2, y2)

    def destroy_redraw_info(cls):
        cls._redraw_items = dict()
        cls._redraw_carrier = None
        cls._carrier_master = None
    
    
class OCRUtils(object):
    TEXT_WIDTH = Window.TKS(200)
    TEXT_HEIGHT = Window.TKS(150)
    def __init__(self, env: 'Env'):
        self.env = env

    def _get_ocr_result(self, image: Image.Image) -> str:
        random_int = ImageUtils.get_random_image_name(image)
        File.temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = File.temp_dir / random_int
        image.save(temp_path)
        command: str = self.env.ocr_config["command"]
        command = command.replace("$image_path", str(temp_path))
        return check_output(command, shell=True)

    def _parse_result(self, result_str: bytes) -> list[dict]:
        try:
            result_str = result_str.decode("gbk", errors="replace")
            result: str = findall(r"(\[.*\])", result_str)[-1]
            result = result.replace("nan",  "0")
            result = eval(result)
        except (SyntaxError, NameError):
            return "Reference Error! Maybe you need to change your ocr plugin?"
        return self._format_output(result)
    
    def _format_output(self, results: list[dict]) -> str:
        if len(results) == 0:
            return "未能识别到文字!"
        try:
            parse_box = self.env.ocr_config["parser_keys"]["box"]
            parse_text = self.env.ocr_config["parser_keys"]["text"]
            if len(results[0][parse_box]) != 4:
                return "\n".join(i[parse_text] for i in results)
        except KeyError:
            return str(results)
        # 识别输入中框的坐标格式到底是以下哪种: 
        # [x1, y1, x2, y2] / [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        text_blocks = []
        total_height = 0
        for result in results:
            x1, y1, x2, y2 = result[parse_box]
            text = result[parse_text]
            if isinstance(x1, Sequence):
                x1, y1, x2, y2 = (*x1, *x2)
            w, h = x2 - x1, y2 - y1
            total_height += h
            text_blocks.append((text, (x1, y1, w, h)))

        avg_height = total_height / len(text_blocks)
        text_blocks.sort(key=lambda x: (round(x[1][1] / avg_height, 2), x[1][0]))
        first_block = text_blocks[0]
        result = [first_block[0]]
        x, y, w, h = first_block[1]
        last_bottom = y + h
        last_right = x + w
        first_line_x = x

        for block in text_blocks[1:]:
            text = block[0]
            x, y, w, h = block[1]
            if y > last_bottom - h // 2:
                result.append('\n')
                last_right = first_line_x
                if x - first_line_x > h // 2:
                    result.append(' ' * int(round((x - last_right) / avg_height, 0)) * 2)                
            if x > last_right:
                result.append(' ' * int(round((x - last_right) / avg_height, 0)) * 2)

            result.append(text)
            last_bottom = y + h
            last_right = x + w
        return ''.join(result)
    
    def get_ocr_result(self, image: Image.Image):
        temp_file_path = File.temp_dir / f"识别结果_{WindowUtils.WIN_ID()}"
        result_bytes = self._get_ocr_result(image)
        format_result = self._parse_result(result_bytes)
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(format_result)
        os.system(f"start /b _internal/notepad.exe {temp_file_path}")
        WindowUtils.SetWindowToTop(f"{temp_file_path.name} - 记事本")
        Thread(target=FileUtils.remove_files(File.temp_dir)).start()


class ShortcutsUtils(metaclass=ClassMethodMeta):
    # 这些快键键都是通过keyboard管理的, 分为截图时快键键和非截图时快键键
    def add_shortcuts(cls, keys: list[str], target: Callable, condition: Callable):
        shortcuts = "+".join(keys)
        keyboard.add_hotkey(shortcuts, cls.__state_decorators(target, condition))

    def __state_decorators(cls, target: Callable, condition: Callable):
        def wrapper(*args, **kwargs):
            if condition():
                return target(*args, **kwargs)
        return wrapper
           

class WindowUtils(object):
    __WIN_ID = 0
    def FindWindow(window_name):
        FindWindowW = user32.FindWindowW
        return FindWindowW(None, window_name)

    def SetWindowPos(hwnd):
        SetWindowPos = user32.SetWindowPos
        SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        SetWindowPos.restype = wintypes.BOOL
        SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001)

    def SetWindowToTop(window_name, timeout: float = 0.5, interval: float = 0.05) -> bool:
        hwnd = WindowUtils.FindWindow(window_name)
        start_time = time()
        while hwnd == 0 and (time() - start_time) < timeout:
            sleep(interval)
            hwnd = WindowUtils.FindWindow(window_name)
        if hwnd != 0:
            WindowUtils.SetWindowPos(hwnd)
            WindowUtils.__WIN_ID += 1
            return True
        return False

    def WIN_ID():
        return WindowUtils.__WIN_ID
    

class ImageUtils(object):
    def hash_image(image: Image.Image) -> str:
        if image.format is None:
            image.format = "PNG"
        buffered = io.BytesIO()
        image.save(buffered, format=image.format)
        buffered.seek(0)
        image_bytes = buffered.getvalue()
        md5_hash = hashlib.md5()
        md5_hash.update(image_bytes)
        return md5_hash.hexdigest()
    
    def copy_image(image: Image.Image):
        if image is None:
            return
        _win32clipboard: 'win32clipboard' = importlib.import_module("win32clipboard")
        output = io.BytesIO()
        image.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        _win32clipboard.OpenClipboard()
        try:
            _win32clipboard.EmptyClipboard()
            _win32clipboard.SetClipboardData(_win32clipboard.CF_DIB, data)
        finally:
            _win32clipboard.CloseClipboard()

    def ask_save_image(initialfile: str = ""):
        State.is_saving = True
        filename = filedialog.asksaveasfilename(
            defaultextension=".png", initialfile=initialfile,
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")],
        )
        State.is_saving = False
        return filename
    
    def get_random_image_name(image: Image.Image) -> str:
        random_suffix = int.from_bytes(os.urandom(4), byteorder='big')
        return f"{image.width}x{image.height}_{random_suffix}.png"

    def copy_rgb_color(color: str):
        _pyperclip: 'pyperclip' = importlib.import_module("pyperclip")
        _pyperclip.copy(color)

    def load_image() -> Image.Image:
        file_types = (("Image files", "*.jpg *.png *.jpeg"), )
        img_path = filedialog.askopenfilename(filetypes=file_types)
        if not img_path:
            return
        try:
            image: Image.Image = Image.open(img_path)
            if image.width > Window.screen_width or image.height > Window.screen_height:
                image = image.thumbnail((Window.screen_width, Window.screen_height))
            return image.convert("RGB")
        except Exception:
            return messagebox.showerror("错误", "无法识别该图片文件!")


class FileUtils(object):
    def open_file_path(path_str: str):
        path = Path(path_str) if path_str else Path.cwd()
        if path.exists():
            Thread(target=os.startfile, args=(path, )).start()

    def remove_files(path: Path):
        if not path.exists():
            return
        if not Path.is_dir(path):
            return
        os.makedirs(path, exist_ok=True)
        for file in path.iterdir():
            try:
                os.remove(file)
            except Exception:
                pass
