import os
import io
import hashlib
from subprocess import check_output
from ctypes import wintypes
from re import findall
from time import sleep

from PIL import Image
from tkinter import Canvas, filedialog, messagebox

from Setting import *



class ScreenshotUtils(object):
    """
    截图的关键是坐标；这个类管理着图片的引用和截图坐标；
    """
    def __init__(self):
        # 必须持久化的变量：
        self.final_images: list[Image.Image] = list()
        self.page_index: int = 0
        # 截图时的临时变量
        self.start_x = self.start_y = self.end_x = self.end_y = -1
        self.move_start_x = self.move_start_y = self.move_end_x = self.move_end_y = 0
        self.current_image: Image.Image = None
        # 一些组件之间的共享变量
        self.magnifier_coords: tuple[int, int] = None
        self.rect_coords: tuple[int, int, int, int] = None
        self.local_canvas: Canvas = None

    def initialize_coords(self):
        self.start_x = self.start_y = self.end_x = self.end_y = -1
        self.rect_coords = [0, 0, Window.screen_width, Window.screen_height]

    def initialize_temp_variables(self):
        self.current_image = None
        self.magnifier_coords = None
        self.rect_coords = None
        self.local_canvas = None

    def get_default_screenshot_coords(self):
        self.start_x = self.start_y = 0
        self.end_x = Window.screen_width
        self.end_y = Window.screen_height

    @property
    def coords_underupdated(self) -> bool:
        return self.start_x == -1 or self.start_y == -1 or self.end_x == -1 or self.end_y == -1
    

class OCRUtils(object):
    TEXT_WIDTH = Window.TKS(200)
    TEXT_HEIGHT = Window.TKS(150)
    def __init__(self, env: 'Env'):
        self.env = env

    def __get_ocr_result(self, image: Image.Image) -> str:
        random_bytes = os.urandom(4)
        random_int = int.from_bytes(random_bytes, byteorder='big')
        File.temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = File.temp_dir / f"{random_int}.png"
        image.save(temp_path)
        command: str = self.env.ocr_config["command"]
        command = command.replace("$image_path", str(temp_path))
        output = check_output(command, shell=True)
        return output

    def __parse_result(self, result_str: bytes) -> list[dict]:
        try:
            result_str = result_str.decode("gbk", errors="replace")
            result: str = findall(r"(\[.*\])", result_str)[-1]
            result = result.replace("nan",  "0")
            result = eval(result)
        except (SyntaxError, NameError):
            return "Reference Error! Maybe you need to change your ocr plugin?"
        return self.__get_format_text(result)
    
    def __get_format_text(self, results: list[dict]) -> str:
        if len(results) == 0:
            return "No result"

        parse_key = self.env.ocr_config["parser_keys"]
        text_blocks = []
        total_h = 0

        for result in results:
            box = result[parse_key["box"]]
            text = result[parse_key["text"]]
            if isinstance(box[0], list):
                box = [*box[0], *box[2]]
            width = box[2] - box[0]
            height = box[3] - box[1]
            total_h += height
            text_blocks.append({'text': text, 'box': (box[0], box[1], width, height)})
            

        av_h = int(total_h / len(text_blocks))

        def sort_func(block):
            x, y, _, _ = block['box']
            return y // av_h, x

        text_blocks = sorted(text_blocks, key=sort_func)
        result = ''
        last_bottom = last_right = first_line_x = 0

        for i, block in enumerate(text_blocks):
            text = block['text']
            x, y, w, h = block['box']

            if i == 0:
                result += text
                last_bottom = y + h
                last_right = x + w
                first_line_x = x
                continue

            new_line = False
            if y > last_bottom - h // 2:
                result += '\n'
                last_right = first_line_x
                new_line = True

            if new_line:
                if x - first_line_x > h // 2:
                    result += ' ' * int(round((x - last_right) / av_h, 0)) * 2
            elif x > last_right:
                result += ' ' * int(round((x - last_right) / av_h, 0)) * 2

            result += text
            last_bottom = y + h
            last_right = x + w

        return result
    
    def get_ocr_result(self, image: Image.Image):
        temp_file_path = File.temp_dir / f"识别结果_{WindowUtils.WIN_ID()}"
        result_bytes = self.__get_ocr_result(image)
        format_result = self.__parse_result(result_bytes)
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(format_result)
        os.system(f"start /b _internal/notepad.exe {temp_file_path}")
        WindowUtils.SetWindowToTop(f"{temp_file_path.name} - 记事本")
        for file in os.scandir(File.temp_dir):
            os.remove(file.path)


class WindowUtils(object):
    __WIN_ID = 0
    @staticmethod
    def FindWindow(window_name):
        FindWindowW = user32.FindWindowW
        return FindWindowW(None, window_name)

    @staticmethod
    def SetWindowPos(hwnd):
        SetWindowPos = user32.SetWindowPos
        SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        SetWindowPos.restype = wintypes.BOOL
        SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001)

    @staticmethod
    def SetWindowToTop(window_name):
        hwnd = WindowUtils.FindWindow(window_name)
        while hwnd == 0:
            sleep(0.1)
            hwnd = WindowUtils.FindWindow(window_name)
        WindowUtils.SetWindowPos(hwnd)
        WindowUtils.__WIN_ID += 1

    @staticmethod
    def WIN_ID():
        return WindowUtils.__WIN_ID
    

class ImageUtils(object):
    @staticmethod
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
    
    @staticmethod
    def copy_image(image):
        from io import BytesIO
        import win32clipboard
        output = BytesIO()
        image.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        finally:
            win32clipboard.CloseClipboard()

    @staticmethod
    def copy_rgb_color(color: str):
        import pyperclip
        pyperclip.copy(color)
        del pyperclip

    @staticmethod
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

