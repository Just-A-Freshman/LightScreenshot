from PIL import Image
from Setting import SCREEN_WIDTH, SCREEN_HEIGHT, TkS
from collections import deque
from tkinter import Canvas, Text, Widget
from subprocess import check_output
from typing import TYPE_CHECKING
from re import findall
import os


if TYPE_CHECKING:
    from Setting import Env




class Event(object):
    def __init__(self, x, y):
        self.x_root = x
        self.y_root = y


class ScreenshotUtils(object):
    """
    截图的关键是坐标；这个类管理着图片的引用和截图坐标；
    """
    def __init__(self):
        # 必须持久化的变量：
        self.final_images: deque[Image.Image] = deque([])
        self.page_index: int = 0
        # 截图时的临时变量
        self.start_x = self.start_y = self.end_x = self.end_y = -1
        self.move_start_x = self.move_start_y = self.move_end_x = self.move_end_y = 0
        self.current_image: Image.Image = None
        self.pixel_reader = None
        # 一些组件之间的共享变量
        self.magnifier_coords: tuple[int, int] = None
        self.rect_coords: tuple[int, int, int, int] = None
        self.local_canvas: Canvas = None

    def initialize_coords(self):
        self.start_x = self.start_y = self.end_x = self.end_y = -1
        self.rect_coords = [0, 0, SCREEN_WIDTH, SCREEN_HEIGHT]

    def initialize_temp_variables(self):
        self.current_image = None
        self.pixel_reader = None
        self.magnifier_coords = None
        self.rect_coords = None
        self.local_canvas = None

    def get_default_screenshot_coords(self):
        self.start_x = self.start_y = 0
        self.end_x = SCREEN_WIDTH
        self.end_y = SCREEN_HEIGHT

    @property
    def coords_underupdated(self) -> bool:
        return self.start_x == -1 or self.start_y == -1 or self.end_x == -1 or self.end_y == -1
    

class OCRUtils(object):
    TEXT_WIDTH = TkS(200)
    TEXT_HEIGHT = TkS(150)
    def __init__(self, screenshot: ScreenshotUtils, env: 'Env'):
        self.screenshot = screenshot
        self.env = env
        self.ocr_result_text: Text = None

    def destroy_ocr_result_text(self):
        if self.ocr_result_text is None:
            return
        self.ocr_result_text.destroy()
        self.ocr_result_text = None

    def toggle_ocr_result_text(self, conceal: bool) -> None:
        if self.ocr_result_text is None:
            return
        if conceal:
            self.ocr_result_text.place_forget()
            return
        cls = self.__class__
        x1, y1, x2, y2 = self.screenshot.rect_coords
        place_x, place_y = x2, y1
        if place_x + cls.TEXT_WIDTH > SCREEN_WIDTH:
            place_x = x1 - cls.TEXT_WIDTH
        if place_y + cls.TEXT_HEIGHT > SCREEN_HEIGHT:
            place_y = y2 - cls.TEXT_HEIGHT
        self.ocr_result_text.place(x=place_x, y=place_y, width=cls.TEXT_WIDTH, height=cls.TEXT_HEIGHT)

    def __get_ocr_result(self, image: Image.Image) -> str:
        random_bytes = os.urandom(4)
        random_int = int.from_bytes(random_bytes, byteorder='big')
        os.makedirs("src/Temp", exist_ok=True)
        temp_path = os.path.abspath(os.path.join("src/Temp", f"{random_int}.png"))
        image.save(temp_path)
        exe_path = os.path.abspath(self.env.ocr_config["exe_path"])
        args = self.env.ocr_config["args"]
        current_dir = os.getcwd()
        os.chdir(os.path.dirname(exe_path))
        command = f'{exe_path} {args}={temp_path}'
        output = check_output(command, shell=True, text=True)
        os.chdir(current_dir)
        return output
    
    def __parse_result(self, result: str):
        parse_key = self.env.ocr_config["parse_key"]
        results = findall(f"""['"]{parse_key}['"]:\s*['"](.*?)['"]""", result)
        results = [
            bytes(line, 'utf-8').decode('unicode_escape') 
            if "\\u" in line else line for line in results
        ]
        return results

    def get_ocr_result(self, parent: Widget, image: Image.Image) -> str:
        if self.ocr_result_text is None:
            self.ocr_result_text = Text(parent, font=("微软雅黑", 10))
        result_str = self.__get_ocr_result(image)
        results = self.__parse_result(result_str)
        self.ocr_result_text.delete("1.0", "end")
        for result in results:
            self.ocr_result_text.insert("end", result + '\n')
        self.toggle_ocr_result_text(conceal=False)
        for file in os.scandir("src/Temp"):
            os.remove(file.path)
