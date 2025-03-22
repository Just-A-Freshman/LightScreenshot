import tkinter as tk
import gc
from threading import Thread, Event
from typing import Literal, TYPE_CHECKING

from tkinter_extension.Widget.DrawCanvas import ImageCanvas, DrawingCanvas
from tkinter_extension.Widget.Button import CharacterButton
from Utils import ImageUtils
from Setting import Window, Style, File
if TYPE_CHECKING:
    from Utils import ScreenshotUtils
    from MainControl import ScreenshotTool

from PIL import Image, ImageTk, ImageGrab, ImageDraw



class BasicImageCanvas(object):
    event = Event()
    def __init__(self, master):
        self.master: tk.Widget = master

    def call(self, *args, **kwargs):
        pass

    def show_menu(self, event):
        def clear(right_click_menu: ButtonMenu):
            # 通过设置超时，那些没有实际执行任务被阻塞的线程也会在超时后被清除掉
            self.event.wait(timeout=3)
            right_click_menu.crash()
            del right_click_menu
            gc.collect()
        right_click_menu: ButtonMenu = ButtonMenu(self)
        right_click_menu.add_default_command()
        right_click_menu.post(event.x_root, event.y_root)
        self.event.clear()
        Thread(target=clear, args=(right_click_menu, )).start()


class ScreenshotCanvas(tk.Canvas):
    alpha = 90
    def __init__(self, master, screenshot: 'ScreenshotUtils', *args, **kwargs):
        super().__init__(master, *args, **kwargs, bg="white", highlightthickness=0)
        self.master = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.orig_image: Image.Image = None
        self.orig_imagetk: ImageTk.PhotoImage = None
        self.overlay_imagetk: ImageTk.PhotoImage = None
        self.__image_id: int = 0
        self.__temp_rect_id: int = 0
        self.__temp_thread: Thread = None

    def make_screenshot(self):
        self.orig_image = ImageGrab.grab()
        self.screenshot.current_image = self.orig_image
        self.orig_imagetk = ImageTk.PhotoImage(self.orig_image)
        self.__image_id = self.create_image(0, 0, anchor=tk.NW, image=self.orig_imagetk)
        self.__temp_rect_id = self.create_rectangle(0, 0, Window.screen_width, Window.screen_height, outline=Style.get("Color", 8), width=2)
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.__temp_thread = Thread(target=self.get_overlay_image)
        self.__temp_thread.start()

    def get_overlay_image(self) -> ImageTk.PhotoImage:
        overlay = Image.new(
            "RGBA", (self.orig_image.width, self.orig_image.height),
            (0, 0, 0, self.__class__.alpha)
        )
        overlayed_image = Image.alpha_composite(self.orig_image.convert("RGBA"), overlay)
        self.overlay_imagetk = ImageTk.PhotoImage(overlayed_image)

    def on_press(self):
        self.__temp_thread.join()
        self.delete(self.__temp_rect_id)
        self.itemconfig(self.__image_id, image=self.overlay_imagetk)


class Magnifier(object):
    ZOOM: int = 4
    ZOOM_AREA: float = Window.TKS(28.75)
    ZOOM_SIZE = int(ZOOM_AREA * ZOOM)
    BORDER_WIDTH: int = 2
    LAYOUT_OFFSET: int = 36
    LAYOUT_ADJUST: int = 70

    def __init__(self, master: tk.Canvas, screenshot: 'ScreenshotUtils'):
        self.master = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.magnifier_window: int = None
        self.zoom_image: int = None
        self.basic_canvas: tk.Canvas = None
        self.create_magnifier()

    def create_magnifier(self):
        cls = self.__class__
        self.basic_canvas = tk.Canvas(
            self.master, width=cls.ZOOM_SIZE, height=cls.ZOOM_SIZE, 
            highlightthickness=2, highlightbackground=Style.get("Color", 8),
        )
        # 水平线和垂直线
        self.zoom_image = self.basic_canvas.create_image(
            cls.BORDER_WIDTH, cls.BORDER_WIDTH, anchor=tk.NW, image=None
        )
        self.basic_canvas.create_line(
            cls.BORDER_WIDTH, cls.ZOOM_SIZE // 2 + cls.BORDER_WIDTH, 
            cls.ZOOM_SIZE + cls.BORDER_WIDTH, cls.ZOOM_SIZE // 2 + cls.BORDER_WIDTH,
            fill=Style.get("Color", 8), width=2
        )
        self.basic_canvas.create_line(
            cls.ZOOM_SIZE // 2 + cls.BORDER_WIDTH, cls.BORDER_WIDTH, 
            cls.ZOOM_SIZE // 2 + cls.BORDER_WIDTH, cls.ZOOM_SIZE + cls.BORDER_WIDTH,
            fill=Style.get("Color", 8), width=2
        )
        self.magnifier_window = self.master.create_window(
            -cls.ZOOM_SIZE, -cls.ZOOM_SIZE, anchor=tk.NW, window=self.basic_canvas
        )

    def update_magnifier(self, x: int, y: int):
        self.toggle_magnifier(conceal=False)
        self.screenshot.magnifier_coords = self.caculate_magnifier_pos(x, y)
        self.master.coords(self.magnifier_window, *self.screenshot.magnifier_coords)
        zoom_area = self.__class__.ZOOM_AREA
        zoom_size = self.__class__.ZOOM_SIZE
        img = self.screenshot.current_image.crop((x - zoom_area//2, y - zoom_area//2, x + zoom_area//2, y + zoom_area//2))
        img = img.resize((zoom_size, zoom_size))
        imgtk = ImageTk.PhotoImage(img)
        self.basic_canvas.itemconfig(self.zoom_image, image=imgtk)
        self.basic_canvas.imgtk = imgtk

    def caculate_magnifier_pos(self, pointerx: int, pointery: int) -> tuple[int, int]:
        offset = self.__class__.LAYOUT_OFFSET
        zoom_size = self.__class__.ZOOM_SIZE
        layout_adjust = self.__class__.LAYOUT_ADJUST
        if pointerx + offset + zoom_size < Window.screen_width:
            x = pointerx + offset
        else:
            x = pointerx - offset - zoom_size
        if pointery + offset + zoom_size + layout_adjust < Window.screen_height:
            y = pointery + offset
        else:
            y = pointery - offset - zoom_size - layout_adjust
        return x, y
    
    def toggle_magnifier(self, conceal: bool = False):
        state = "hidden" if conceal else "normal"
        self.master.itemconfig(self.magnifier_window, state=state)


class ScreenshotTip(object):
    tip_style = {"anchor": tk.NW, "fill": Style.get("Color", 0), "font": (Style.get("fontFamily", 0), 10)}
    bg_style = {"outline": Style.get("Color", 1), "fill": Style.get("Color", 1)}
    def __init__(self, master: ScreenshotCanvas, screenshot: 'ScreenshotUtils'):
        self.master: ScreenshotCanvas = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.__rgb_tuple: bool = True
        self.__tip_item: list[int] = []
        self.__shelter_item: list[int] = []
        self.create_pointer_tip()
        self.create_rect_size_tip()

    def create_pointer_tip(self):
        pos_tip = self.master.create_text(0, 0, **self.__class__.tip_style)
        rgb_tip = self.master.create_text(0, 0, **self.__class__.tip_style)
        pos_bg = self.master.create_rectangle(0, 0, 0, 0, **self.__class__.bg_style)
        rgb_bg = self.master.create_rectangle(0, 0, 0, 0, **self.__class__.bg_style)
        self.__tip_item.extend([pos_tip, pos_bg, rgb_tip, rgb_bg])

    def create_rect_size_tip(self):
        rect_size_tip = self.master.create_text(0, 0, **self.__class__.tip_style)
        rect_size_bg = self.master.create_rectangle(0, 0, 0, 0, **self.__class__.bg_style)
        self.__tip_item.extend([rect_size_tip, rect_size_bg])

    def update_pointer_tip(self, x: int, y: int):
        self.toggle_pointer_tip(conceal=False)
        magnifier_x, magnifier_y = self.screenshot.magnifier_coords
        zoom_size = Magnifier.ZOOM_SIZE
        # 更新位置信息
        pos_info = f"POS: ({x}, {y})"
        pos_tip_coord = (magnifier_x, magnifier_y + zoom_size + 10)
        # 更新RGB信息
        tuple_rgb_color = self.screenshot.current_image.getpixel((x, y))
        if self.__rgb_tuple:
            rgb_info = f"RGB: {tuple_rgb_color}"
        else:
            rgb_info = 'RGB: #' + ''.join(map(lambda x: f'{x:02x}', tuple_rgb_color)).upper()
        rgb_tip_coord = (magnifier_x, magnifier_y + zoom_size + 48)
        self._update_text_and_bg(self.__tip_item[0], pos_info, pos_tip_coord)
        self._update_text_and_bg(self.__tip_item[2], rgb_info, rgb_tip_coord)
        self.shelter_redraw()

    def update_rect_size_tip(self):
        self.toggle_rect_size_tip(conceal=False)
        left, top, right, bottom = self.screenshot.rect_coords
        rect_w, rect_h = int(right - left), int(bottom - top)
        rect_size_tip_info = f"{rect_w} × {rect_h}"
        rect_size_tip_coord = (max(left, 0), max(top - 40, 0))
        self._update_text_and_bg(self.__tip_item[4], rect_size_tip_info, rect_size_tip_coord)
        self.shelter_redraw()

    def _update_text_and_bg(self, text_item, text_content, text_coords):
        self.master.itemconfig(text_item, text=text_content)
        self.master.coords(text_item, *text_coords)
        bg_item = self.__tip_item[self.__tip_item.index(text_item) + 1]
        bg_coords = self.master.bbox(text_item)
        self.master.coords(bg_item, *bg_coords)
        self.master.tag_raise(text_item)

    def toggle_pointer_tip(self, conceal: bool = False):
        self._toggle_items_visibility(self.__tip_item[0: 4], conceal)

    def toggle_rect_size_tip(self, conceal: bool = False):
        self._toggle_items_visibility(self.__tip_item[4: 6], conceal)

    def toggle_rgb_state(self):
        if self.master.itemcget(self.__tip_item[0], "state") == "hidden":
            return
        self.__rgb_tuple = not self.__rgb_tuple
        self.update_pointer_tip(*self.master.winfo_pointerxy())

    def _toggle_items_visibility(self, items, conceal: bool):
        state = "hidden" if conceal else "normal"
        for item in items:
            self.master.itemconfig(item, state=state)

    def shelter_redraw(self):
        self.delete_shelter_item()
        overlapping = self.master.find_overlapping(*self.screenshot.rect_coords)
        for overlap in overlapping:
            if overlap not in self.__tip_item:
                continue
            item_type = self.master.type(overlap)
            if item_type == "text":
                coords = self.map_coords(*self.master.coords(overlap))
                text = self.master.itemcget(overlap, "text")
                id = self.screenshot.local_canvas.create_text(*coords, text=text, **ScreenshotTip.tip_style)
                self.__shelter_item.append(id)
            elif item_type == "rectangle":
                x1, y1, x2, y2 = self.master.coords(overlap)
                mapped_x1, mapped_y1 = self.map_coords(x1, y1)
                mapped_x2, mapped_y2 = self.map_coords(x2, y2)
                id = self.screenshot.local_canvas.create_rectangle(mapped_x1, mapped_y1, mapped_x2, mapped_y2, **ScreenshotTip.bg_style)
                self.__shelter_item.append(id)

    def delete_shelter_item(self):
        for id in self.__shelter_item:
            self.screenshot.local_canvas.delete(id)
        self.__shelter_item.clear()

    def map_coords(self, x, y):
        inner_bbox = self.screenshot.rect_coords
        return x - inner_bbox[0], y - inner_bbox[1]

    def current_color(self) -> str:
        color_info: str = self.master.itemcget(self.__tip_item[2], "text")
        color_info = color_info.replace("RGB:", "")
        return color_info.strip()


class AdjustableRect(object):
    """
    The judgement seq is so important that you must care about:
    (right, bottom), (left, top), (right, top), (left, bottom),
    (center_x, top), (center_x, bottom), (left, center_y), (right, center_y)
    """
    ANCHOR_SIZE = 3
    ANCHOR_HOVER_DISTANCE = 20
    RECT_BORDER_WIDTH = 2
    CURSOR_FILES_NAME = ["aero_nwse_l.cur", "aero_nesw_l.cur", "aero_ns_l.cur", "aero_ew_l.cur"]
    CURSOR_FILES = [f"@C:/Windows/Cursors/{cursor_file}" for cursor_file in CURSOR_FILES_NAME]
    CURSORS = [
        CURSOR_FILES[0], CURSOR_FILES[0], CURSOR_FILES[1], CURSOR_FILES[1],
        CURSOR_FILES[2], CURSOR_FILES[2], CURSOR_FILES[3], CURSOR_FILES[3],
        "fleur", "arrow"
    ]

    def __init__(self, master: ScreenshotCanvas, screenshot: 'ScreenshotUtils'):
        self.master: ScreenshotCanvas = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.local_image_canvas: tk.Canvas = None
        self.__local_image: int = 0
        self.__rect: int = 0
        self.__anchors: list[int] = []
        self.anchor_id: int = 0
        self.create_rect()
    
    def rect_coords(self) -> tuple[int, int, int, int]:
        return self.master.bbox(self.__rect)

    def anchor_coords(self) -> tuple[int, int, int, int]:
        left, top, right, bottom = self.rect_coords()
        horizontal_middle = (left + right) // 2
        vertical_middle = (top + bottom) // 2
        return (
            (left, top), (horizontal_middle, top), (right, top), (right, vertical_middle),
            (right, bottom), (horizontal_middle, bottom), (left, bottom), (left, vertical_middle)
        )

    def get_anchor(self, event) -> int:
        cls = self.__class__
        left, top, right, bottom = self.rect_coords()
        center_x, center_y = (left + right) // 2, (top + bottom) // 2
        def near(actual, target):
            return abs(actual - target) < cls.ANCHOR_HOVER_DISTANCE
        # 务必注意这个判断顺序，这与后面rect_adjust密切相关
        judgement_pos = (
            (right, bottom), (left, top), (right, top), (left, bottom),
            (center_x, top), (center_x, bottom), (left, center_y, ), (right, center_y)
        )
        for index, pos in enumerate(judgement_pos):
            if near(event.x_root, pos[0]) and near(event.y_root, pos[1]):
                return index
        if left < event.x_root < right and top < event.y_root < bottom:
            return 8
        return -1
 
    def create_anchors(self):
        cls = self.__class__
        for coord in self.anchor_coords():
            anchor = self.master.create_rectangle(
                coord[0]-cls.ANCHOR_SIZE, coord[1]-cls.ANCHOR_SIZE,
                coord[0]+cls.ANCHOR_SIZE, coord[1]+cls.ANCHOR_SIZE,
                fill=Style.get("Color", 8), outline=Style.get("Color", 8)
            )
            self.__anchors.append(anchor)

    def create_rect(self) -> None:
        self.local_image_canvas = tk.Canvas(self.master, highlightthickness=0, highlightbackground=Style.get("Color", 8))
        self.screenshot.local_canvas = self.local_image_canvas
        self.__local_image = self.local_image_canvas.create_image(0, 0, anchor="nw", image=self.master.orig_imagetk)
        self.__border = self.local_image_canvas.create_rectangle(
            1, 1, Window.screen_width - 1, Window.screen_height - 1, 
            outline=Style.get("Color", 8), width=self.__class__.RECT_BORDER_WIDTH
        )
        self.__rect = self.master.create_window(
            -Window.screen_width, -Window.screen_height, 
            anchor="nw", window=self.local_image_canvas, 
        )
        self.create_anchors()

    def move_anchors(self):
        cls = self.__class__
        for anchor, coord in zip(self.__anchors, self.anchor_coords()):
            self.master.coords(
                anchor, coord[0]-cls.ANCHOR_SIZE, coord[1]-2, 
                coord[0]+cls.ANCHOR_SIZE, coord[1]+cls.ANCHOR_SIZE
            )

    def on_press(self, event):
        self.screenshot.start_x = event.x_root
        self.screenshot.start_y = event.y_root

    def on_release(self, _):
        self.screenshot.start_x, self.screenshot.start_y,\
        self.screenshot.end_x, self.screenshot.end_y = self.rect_coords()

    def on_hover(self, event):
        self.anchor_id = self.get_anchor(event)
        cursor = self.CURSORS[self.anchor_id]
        self.master.config(cursor=cursor)

    def move_rect(self, event):
        offset_x = event.x_root - self.screenshot.move_start_x
        offset_y = event.y_root - self.screenshot.move_start_y
        if self.screenshot.start_x + offset_x >= 0 and self.screenshot.end_x + offset_x <= Window.screen_width:
            self.screenshot.start_x += offset_x
            self.screenshot.end_x += offset_x
        if  self.screenshot.start_y + offset_y >= 0 and self.screenshot.end_y + offset_y <= Window.screen_height:
            self.screenshot.start_y += offset_y
            self.screenshot.end_y += offset_y
        self.screenshot.move_start_x = event.x_root
        self.screenshot.move_start_y = event.y_root
        self.update_rect()

    def rect_adjust(self, event):
        if self.anchor_id == 8:
            return self.move_rect(event)
        update_pos = (event.x_root, event.y_root)
        if self.anchor_id == 0:
            self.screenshot.end_x, self.screenshot.end_y = update_pos
        elif self.anchor_id == 1:
            self.screenshot.start_x, self.screenshot.start_y = update_pos
        elif self.anchor_id == 2:
            self.screenshot.end_x, self.screenshot.start_y = update_pos
        elif self.anchor_id == 3:
            self.screenshot.start_x, self.screenshot.end_y = update_pos
        elif self.anchor_id == 4:
            self.screenshot.start_y = event.y_root
        elif self.anchor_id == 5:
            self.screenshot.end_y = event.y_root
        elif self.anchor_id == 6:
            self.screenshot.start_x = event.x_root
        elif self.anchor_id == 7:
            self.screenshot.end_x = event.x_root
        else:
            return
        self.update_rect()

    def update_rect(self):
        x1 = min(self.screenshot.start_x, self.screenshot.end_x)
        y1 = min(self.screenshot.start_y, self.screenshot.end_y)
        x2 = max(self.screenshot.start_x, self.screenshot.end_x)
        y2 = max(self.screenshot.start_y, self.screenshot.end_y)
        self.master.coords(self.__rect, x1, y1)
        self.master.itemconfig(self.__rect, width=max(x2 - x1, 1), height=max(y2 - y1, 1))
        self.local_image_canvas.coords(self.__local_image, -x1, -y1)
        self.local_image_canvas.coords(self.__border, 1, 1, x2 - x1 - 1, y2 - y1 - 1)
        self.screenshot.rect_coords = self.master.bbox(self.__rect)
        self.move_anchors()


class EditBar(object):
    BAR_WIDTH = Window.TKS(150)
    BAR_HEIGHT = Window.TKS(35)
    DELTA = Window.TKS(5)
    def __init__(self, master: ScreenshotCanvas, screenshot: 'ScreenshotUtils'):
        self.master: ScreenshotCanvas = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.__edit_bar = self.create_edit_bar()

    def create_edit_bar(self):
        edit_bar = tk.Frame(self.master, bg=Style.get("Color", 0))
        cancel_btn = self._set_cancel_btn(edit_bar)
        confirm_btn = self._set_confirm_btn(edit_bar)
        ocr_btn = self._set_ocr_btn(edit_bar)
        nail_btn = self._set_nail_btn(edit_bar)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        confirm_btn.pack(side=tk.RIGHT, padx=10)
        ocr_btn.pack(side=tk.RIGHT, padx=10)
        nail_btn.pack(side=tk.RIGHT, padx=10)
        return edit_bar
    
    def get_children(self):
        return self.__edit_bar.winfo_children()
    
    def _set_cancel_btn(self, master) -> CharacterButton:
        cancel_btn = CharacterButton(
            master, text="×", bg=Style.get("Color", 0),
            enter_fg=Style.get("Color", 9), fg=Style.get("Color", 10), font=(Style.get("fontFamily", 0), Style.get("fontSize", 4))
        )
        return cancel_btn

    def _set_confirm_btn(self, master) -> CharacterButton:
        confirm_btn = CharacterButton(
            master, fg=Style.get("Color", 11), text="√",
            enter_fg=Style.get("Color", 12), bg=Style.get("Color", 0), 
            font=(Style.get("fontFamily", 0), Style.get("fontSize", 4))
        )
        return confirm_btn
    
    def _set_ocr_btn(self, master) -> CharacterButton:
        ocr_btn = CharacterButton(
            master, text="T", bg=Style.get("Color", 0), 
            font=(Style.get("fontFamily", 3), Style.get("fontSize", 4)), 
            fg=Style.get("Color", 13), enter_fg=Style.get("Color", 14)
        )
        return ocr_btn
    
    def _set_nail_btn(self, master) -> CharacterButton:
        nail_btn = CharacterButton(
            master, text="📌", bg=Style.get("Color", 0),
            font=(Style.get("fontFamily", 1), 16), fg=Style.get("Color", 15), enter_fg=Style.get("Color", 14)
        )
        return nail_btn
    
    def toggle_edit_bar(self, conceal: bool = False):
        if conceal:
            self.__edit_bar.place_forget()
            return
        width = self.__class__.BAR_WIDTH
        height = self.__class__.BAR_HEIGHT
        delta = self.__class__.DELTA
        place_x = max(min(self.screenshot.end_x - width, Window.screen_width - width), 0)
        place_y = min(self.screenshot.end_y + delta, Window.screen_height - height)
        if place_y == Window.screen_height - height and self.screenshot.start_y - height - delta > 0:
            place_y = self.screenshot.start_y - height - delta
        self.__edit_bar.place(x=place_x, y=place_y, width=width, height=height)

    def _bind_command(self, command_list: list):
        widgets: list[CharacterButton] = self.get_children()
        for widget, command in zip(widgets, command_list):
            widget.config(command=command)


class ShowImageCanvas(BasicImageCanvas):
    def __init__(self, master: 'ScreenshotTool'):
        super().__init__(master)
        self.master: 'ScreenshotTool' = master
        self.__basic_frame = tk.Frame(master, bg=Style.get("Color", 3))
        self.__canvas_image: ImageCanvas = None

    def __pack_basic_frame(self):
        self.__basic_frame.pack(expand=True, fill="both")
        self.__basic_frame.rowconfigure(0, weight=1)
        self.__basic_frame.columnconfigure(0, weight=1)

    def show_image(self, image: Image.Image):
        show_width, show_height = self.__get_fit_show_size(image)
        self.master.geometry(f"{show_width}x{show_height + self.master.menu_bar.winfo_height()}")
        self.__pack_basic_frame()
        if self.__canvas_image:
            self.__init_canvas_image_state(image)
        else:
            self.__canvas_image = ImageCanvas(image)
            self.__canvas_image.set_basic_canvas(self.__basic_frame, Style.get("Color", 3))
            self.__canvas_image.canvas.bind("<Button-3>", self.show_menu)
        self.__show_image(show_width, show_height)

    def __get_fit_show_size(self, image: Image.Image) -> tuple[int, int]:
        if image.width < Window.screen_width // 2 and image.height < Window.screen_height // 2:
            show_width, show_height = image.size
        else:
            image_scale = image.width / image.height
            screen_scale = Window.screen_width / Window.screen_height
            if image_scale > screen_scale:
                show_width = Window.screen_width // 2
                show_height = int(show_width / image_scale)
            else:
                show_height = Window.screen_height // 2
                show_width = int(show_height * image_scale)
        return show_width, show_height

    def __show_image(self, show_width, show_height):
        self.__canvas_image.grid(row=0, column=0)
        self.__canvas_image.set_container()
        self.__canvas_image.show_image(show_width, show_height)
        self.__canvas_image.canvas.config(scrollregion=self.__canvas_image.canvas.bbox("all"))

    def __init_canvas_image_state(self, image):
        self.__canvas_image.canvas.delete("all")
        self.__canvas_image.__init__(image)

    def call(self, name: Literal["copy", "save", "destroy"]):
        if name == "copy":
            self.master.copy_image()
        elif name == "save":
            self.master.save_image()
        elif name == "kill":
            self.master.delete_image()
        self.event.set()
        
    def destroy(self):
        self.__canvas_image.canvas.delete("all")


class NailImageCanvas(tk.Toplevel, BasicImageCanvas):
    snapshot_dict: dict = dict()
    min_scale_size: int = 100

    def __new__(cls, *args, **kwargs):
        image: Image.Image = args[0]
        md5_hash = ImageUtils.hash_image(image)
        if md5_hash in cls.snapshot_dict:
            nail_image_canvas: 'NailImageCanvas' = cls.snapshot_dict[md5_hash]
            nail_image_canvas.bell()
            nail_image_canvas.flash(5)
            return
        else:
            nail_image_canvas = super().__new__(cls)
            cls.snapshot_dict[md5_hash] = nail_image_canvas
            return nail_image_canvas

    def __init__(self, image: Image.Image):
        super().__init__(background=Style.get("Color", 5))
        self.x = self.y = 0
        self.orig_image: Image.Image = image
        self.image_scale: float = 1.0
        self.phototk: ImageTk.PhotoImage = None
        self.nail_canvas: DrawingCanvas = None
        self.tip_label: tk.Label = None
        self.tip_id: str = None
        self.overrideredirect(True)
        self.attributes("-topmost", True)

    def set_nail_canvas(self, x: int, y: int):
        self.geometry(f"{self.orig_image.width}x{self.orig_image.height}+{x}+{y}")
        self.nail_canvas = DrawingCanvas(self, highlightthickness=1, highlightcolor="red", highlightbackground=Style.get("Color", 6))
        self.update_image(self.orig_image)
        self.nail_canvas.create_image(0, 0, image=self.phototk, anchor=tk.NW)
        self.nail_canvas.pack(fill=tk.BOTH, expand=True)
        self.bind_event()

    def update_image(self, image: Image.Image):
        self.phototk = ImageTk.PhotoImage(image)
        self.nail_canvas.itemconfig(1, image=self.phototk)
        self.nail_canvas.imagetk = self.phototk
       
    def bind_event(self):
        self.nail_canvas.bind("<ButtonPress-1>", self.start_dragging)
        self.nail_canvas.bind("<ButtonRelease-1>", self.stop_dragging)
        self.nail_canvas.bind("<B1-Motion>", self.do_dragging)
        self.nail_canvas.bind("<Button-3>", self.show_menu)  # 右键菜单
        self.nail_canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # 鼠标中键滚动
        self.nail_canvas.bind("<Control-s>", lambda _: self.call("save"))
        self.nail_canvas.bind("<Control-c>", lambda _: self.call("copy"))
        self.nail_canvas.bind("<Delete>", lambda _: self.call("kill"))

    def start_dragging(self, event):
        if self.nail_canvas.drawing_mode:
            return self.nail_canvas._draw_single_point(event)
        self.x = event.x
        self.y = event.y

    def stop_dragging(self, event):
        self.nail_canvas._finalize_stroke(event)
        if not self.nail_canvas.drawing_mode:
            self.x = 0
            self.y = 0

    def do_dragging(self, event):
        if self.nail_canvas.drawing_mode:
            return self.nail_canvas._draw_continuous(event)
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.winfo_x() + deltax
        new_y = self.winfo_y() + deltay
        self.geometry(f"+{new_x}+{new_y}")

    def on_mouse_wheel(self, event) -> None:
        if self.nail_canvas.drawing_mode:
            return
        scale_factor = 1.1 if event.delta > 0 else 1 / 1.1
        last_image_scale = self.image_scale
        self.image_scale *= scale_factor
        new_width = int(self.orig_image.width * self.image_scale)
        new_height = int(self.orig_image.height * self.image_scale)
        min_size = self.__class__.min_scale_size
        max_width = self.winfo_screenwidth()
        max_height = self.winfo_screenheight()

        if (new_width < min_size or new_height < min_size) and event.delta < 0:
            self.image_scale = max(min_size / self.orig_image.width, min_size / self.orig_image.height)

        if (new_width > max_width or new_height > max_height) and event.delta > 0:
            self.image_scale = min(max_width / self.orig_image.width, max_height / self.orig_image.height)
        scale_factor = self.image_scale / last_image_scale
        new_image = self.current_image()
        self.adjust_graphics_items(scale_factor)
        self.update_image(new_image)
        self.geometry(f"{new_image.width}x{new_image.height}")
        self.show_tip(f"大小: {int(self.image_scale * 100)}%")

    def adjust_graphics_items(self, scale_factor: float):
        self.nail_canvas.scale('all', 0, 0, scale_factor, scale_factor)
        for item in self.nail_canvas.stroke_history():
            orig_width = float(self.nail_canvas.itemcget(item, "width"))
            self.nail_canvas.itemconfig(item, width=orig_width * scale_factor)

    def current_image(self) -> Image.Image:
        current_width = int(self.orig_image.width * self.image_scale)
        current_height = int(self.orig_image.height * self.image_scale)
        current_image = self.orig_image.resize((current_width, current_height), Image.Resampling.LANCZOS)
        return current_image

    def griding_current_image(self):
        image = self.current_image()
        draw: ImageDraw.ImageDraw = ImageDraw.Draw(image)
        for item in self.nail_canvas.find_all():
            item_type = self.nail_canvas.type(item)
            coords = self.nail_canvas.coords(item)
            if item_type == 'line':
                self.draw_line_with_points(
                    draw, coords, fill=self.nail_canvas.itemcget(item, 'fill'),
                    width=int(float(self.nail_canvas.itemcget(item, 'width')))
                )
                # draw.line(coords, fill=self.nail_canvas.itemcget(item, 'fill'), width=int(float(self.nail_canvas.itemcget(item, 'width'))), joint='curve')
            elif item_type == 'oval':
                draw.ellipse(
                    coords, fill=self.nail_canvas.itemcget(item, 'fill'),
                    outline=self.nail_canvas.itemcget(item, 'outline')
                )
        return image
    
    def show_tip(self, text):
        if self.tip_label is None:
            self.tip_label = tk.Label(self, bg="white", fg="black")
        self.tip_label.config(text=text)
        self.tip_label.place(x=5, y=5)
        if self.tip_id:
            self.after_cancel(self.tip_id)
        self.tip_id = self.after(1000, self.tip_label.place_forget)

    def flash(self, count: int) -> None:
        if count <= 0:
            return
        count -= 1
        self.attributes("-alpha", 0)
        self.after(50, lambda: self.attributes("-alpha", 1))
        self.after(100, lambda: self.flash(count))

    def draw_line_with_points(self, draw: ImageDraw.ImageDraw, coords: tuple[int], fill: str, width: float):
        coords = [int(coord) for coord in coords]
        radius = width / 2
        points = self.get_line_points(*coords)
        for point in points:
            x, y = point
            coords = (x - radius, y - radius, x + radius, y + radius)
            draw.ellipse(coords, fill=fill)

    @staticmethod
    def get_line_points(x1: int, y1: int, x2: int, y2: int, step_precision: float = 1.0):
        dx = x2 - x1
        dy = y2 - y1
        distance = max(abs(dx), abs(dy))
        
        if distance == 0:
            yield (round(x1), round(y1))
            return

        step_x = dx / distance
        step_y = dy / distance

        current_x = x1
        current_y = y1
        traveled = 0

        while traveled <= distance:
            yield (round(current_x), round(current_y))
            current_x += step_x * step_precision
            current_y += step_y * step_precision
            traveled += step_precision

    def call(self, name: Literal["copy", "save", "kill"]):
        main_control: 'ScreenshotTool' = self._root()
        if name == "copy":
            main_control.copy_image(self.griding_current_image())
        elif name == "save":
            main_control.save_image(image=self.griding_current_image())
        elif name == "kill":
            self.nail_canvas = None
            NailImageCanvas.snapshot_dict.pop(ImageUtils.hash_image(self.orig_image))
            self.event.set()
            super().destroy()
        self.event.set()


class ButtonMenu(tk.Menu):
    ICO_TUPLE = tuple()

    def __init__(self, master: BasicImageCanvas):
        self.executant: BasicImageCanvas = master
        self.master = master if hasattr(master, "tk") else master.master
        self.initialize_ico()
        super().__init__(self.master, tearoff=0, font=(Style.get("fontFamily", 0), Style.get("fontSize", 1)))
        
    def initialize_ico(self):
        if self.ICO_TUPLE:
            return
        self.ICO_TUPLE = (
            tk.PhotoImage(file=File.kill_ico),
            tk.PhotoImage(file=File.copy_ico),
            tk.PhotoImage(file=File.save_ico),
        )

    def add_default_command(self) -> None:
        name_list = ("kill", "copy", "save")
        for name, image in zip(name_list, self.ICO_TUPLE):
            self.add_command(
                label=name, command=lambda name=name: self.executant.call(name),
                compound=tk.LEFT, image=image
            )

    def crash(self):
        super().destroy()
        for attr in self.__dict__:
            setattr(self, attr, None)

