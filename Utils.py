from PIL import Image
from Setting import SCREEN_WIDTH, SCREEN_HEIGHT, TkS
from collections import deque
from src.plugins.ocr import wcocr
from tkinter import Canvas, Text, Widget
import os
import re


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
    

class WechatOCRUtils(object):
    TEXT_WIDTH = TkS(200)
    TEXT_HEIGHT = TkS(150)
    def __init__(self, screenshot: ScreenshotUtils):
        self.wechatocr_path = self.find_wechatocr_exe()
        self.wechat_path = self.find_wechat_path()
        self.screenshot = screenshot
        self.ocr_result_text: Text = None

    def find_wechatocr_exe(self) -> str:
        appdata_path = os.getenv("APPDATA")
        if not appdata_path:
            return "src/plugins/ocr/WeChatOCR.exe"
        base_path = os.path.join(appdata_path, r"Tencent\WeChat\XPlugin\Plugins\WeChatOCR")
        version_pattern = re.compile(r'\d+')
        try:
            path_temp = os.listdir(base_path)
        except FileNotFoundError:
            return "src/plugins/ocr/WeChatOCR.exe"
        for temp in path_temp:
            if version_pattern.match(temp):
                wechatocr_path = os.path.join(base_path, temp, 'extracted', 'WeChatOCR.exe')
                if os.path.isfile(wechatocr_path):
                    return wechatocr_path
        return "src/plugins/ocr/WeChatOCR.exe"

    def find_wechat_path(self) -> str:
        common_paths = r"C:\Program Files\Tencent\WeChat"
        version_pattern = re.compile(r'\[\d+\.\d+\.\d+\.\d+\]')
        path_temp = os.listdir(common_paths)
        for temp in path_temp:
            if version_pattern.match(temp):
                wechat_path = os.path.join(common_paths, temp)
                if os.path.isdir(wechat_path):
                    return wechat_path
        return "src/plugins/ocr"

    def destroy_ocr_result_text(self):
        if self.ocr_result_text is None:
            return
        self.ocr_result_text.destroy()
        self.ocr_result_text = None
    
    def check_valid(self) -> bool:
        if not os.path.isfile(self.wechatocr_path) and os.path.isdir(self.wechat_path):
            self.ocr_result_text.insert("end", "未检测到微信安装路径!\n")
            self.ocr_result_text.insert("end", "如要使用OCR功能，请访问下述网址进行资源下载: \n")
            self.ocr_result_text.insert("end", "https://github.com/Just-A-Freshman/Wechat_OCR/tree/main/WechatOCR/src\n")
            self.ocr_result_text.insert("end", "将下载文件中src目录下的所有文件放到该文件夹下:\n")
            self.ocr_result_text.insert("end", f"{os.path.join(os.path.dirname(__file__), r'src/plugins/ocr')}\n")
            return False
        return True

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

    def get_ocr_result(self, parent: Widget, image: Image.Image) -> str:
        if self.ocr_result_text is None:
            self.ocr_result_text = Text(parent, font=("微软雅黑", 10))
        valid_flag = self.check_valid()
        if not valid_flag:
            self.toggle_ocr_result_text(conceal=False)
        random_bytes = os.urandom(4)
        random_int = int.from_bytes(random_bytes, byteorder='big')
        temp_path = os.path.join("src/Temp", f"{random_int}.png")
        image.save(temp_path)
        wechat_path = self.find_wechat_path()
        wechatocr_path = self.find_wechatocr_exe()
        wcocr.init(wechatocr_path, wechat_path)
        result = wcocr.ocr(temp_path)
        self.ocr_result_text.delete("1.0", "end")
        for temp in result['ocr_response']:
            self.ocr_result_text.insert("end", temp['text'])
            self.ocr_result_text.insert("end", "\n")
        self.toggle_ocr_result_text(conceal=False)
        for file in os.scandir("src/Temp"):
            os.remove(file.path)
