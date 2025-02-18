from PIL import Image
from Setting import SCREEN_WIDTH, SCREEN_HEIGHT, TkS
from collections import deque


class Event(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class ScreenshotUtils(object):
    """
    截图的关键是坐标；这个类管理着图片的引用和截图坐标；
    """
    ZOOM: int = 4
    ZOOM_WIDTH: float = TkS(28.75)
    ZOOM_SCREEN_SIZE: int = int(ZOOM_WIDTH*ZOOM)
    MAGNIFIER_OFFSET: int = 36
    WIDTH_HEIGHT_OFFSET = 40
    POS_TAG_GAP = 10
    RGB_TAG_GAP = 47
    MAGNIFIER_ADJUST = 70
    AJUST_BAR_WIDTH: int = TkS(100)

    def __init__(self):
        self.start_x = self.start_y = self.end_x = self.end_y = 0
        self.move_start_x = self.move_start_y = self.move_end_x = self.move_end_y = 0
        self.page_index: int = 0
        self.current_image: Image.Image = None
        self.pixel_reader = None
        self.final_images: deque[Image.Image] = deque([])
        # 这种是只移动但不改变大小和内容的控件，只需移动无需重绘
        self.screenshot_move_widget = list()
        # 这种是移动和改变大小的控件，需要实时重绘
        self.screenshot_redraw_widget = list()
    
    @classmethod
    def move_widget_coords(cls, x, y) -> list[tuple[int, int, int, int]]:
        # 按照主框架，水平线，垂直线的顺序返回坐标
        main_frame_coord  = (x, y, x+cls.ZOOM_SCREEN_SIZE, y+cls.ZOOM_SCREEN_SIZE)
        horrontal_line_coord = (x, y+cls.ZOOM_SCREEN_SIZE // 2, x+cls.ZOOM_SCREEN_SIZE, y+cls.ZOOM_SCREEN_SIZE // 2)
        vertical_line_coord = (x+cls.ZOOM_SCREEN_SIZE // 2, y, x+cls.ZOOM_SCREEN_SIZE // 2, y+cls.ZOOM_SCREEN_SIZE)
        return [main_frame_coord, horrontal_line_coord, vertical_line_coord]

    def redraw_widget_coords(self, x, y) -> list[tuple]:
        # 按照"放大镜图像"、"长 × 宽"、"POS标签"、"RGB标签"的顺序返回坐标
        offset = self.__class__.MAGNIFIER_OFFSET
        zoom_size = self.__class__.ZOOM_SCREEN_SIZE
        if x + offset + zoom_size < SCREEN_WIDTH:
            x_offset = x + offset
        else:
            x_offset = x - offset - zoom_size
        if y + offset + zoom_size + self.__class__.MAGNIFIER_ADJUST < SCREEN_HEIGHT:
            y_offset = y + offset
        else:
            y_offset = y - offset - zoom_size - self.__class__.MAGNIFIER_ADJUST
        width_height_y = max(min(self.start_y, self.end_y) - self.__class__.WIDTH_HEIGHT_OFFSET, 0)
        width_height_info = (max(min(self.start_x, self.end_x), 0), width_height_y)
        magnifier_coord = (x_offset, y_offset)
        pos_info = (x_offset, y_offset + zoom_size + self.__class__.POS_TAG_GAP)
        rgb_info = (x_offset, y_offset + zoom_size + self.__class__.RGB_TAG_GAP)
        return [magnifier_coord, width_height_info, pos_info, rgb_info]
    