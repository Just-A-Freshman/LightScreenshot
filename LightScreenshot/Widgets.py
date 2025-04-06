import tkinter as tk
import gc
from threading import Thread, Event
from typing import Literal, TYPE_CHECKING

from tkinter_extension.Widget.DrawCanvas import ImageCanvas, DrawingCanvas
from tkinter_extension.Widget.Button import CharacterButton
from Utils import ImageUtils, RedrawUtils, ScreenshotUtils
from Setting import Window, Style, File, Size, Tags
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
    alpha = min(max(0, int(Style.get("Selection", "control", "unselect_alpha") * 255)), 150)
    def __init__(self, master, screenshot: 'ScreenshotUtils', *args, **kwargs):
        super().__init__(master, *args, **kwargs, highlightthickness=0)
        self.master = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.orig_image: Image.Image = None
        self.orig_imagetk: ImageTk.PhotoImage = None
        self.overlay_imagetk: ImageTk.PhotoImage = None
        self.__temp_thread: Thread = None

    def make_screenshot(self):
        self.orig_image = ImageGrab.grab()
        self.orig_imagetk = ImageTk.PhotoImage(self.orig_image)
        self.screenshot.current_image = self.orig_image
        self.create_image(0, 0, anchor=tk.NW, image=self.orig_imagetk, tags=Tags.bg_image)
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.__temp_thread = Thread(target=self.get_overlay_image)
        self.__temp_thread.start()

    def get_overlay_image(self) -> ImageTk.PhotoImage:
        overlay = Image.new(
            "RGBA", (self.orig_image.width, self.orig_image.height),
            (0, 0, 0, self.__class__.alpha)
        )
        overlayed_image: Image.Image = Image.alpha_composite(self.orig_image.convert("RGBA"), overlay)
        self.overlay_imagetk = ImageTk.PhotoImage(overlayed_image)

    def on_press(self):
        self.__temp_thread.join()
        self.itemconfig("bg_image", image=self.overlay_imagetk)
        self.__temp_thread = None


class Magnifier(object):
    SCALE: float = Style.get("Magnifier", "control", "scale")
    ZOOM_AREA: float = Style.get("Magnifier", "control", "zoom_area")
    ZOOM_SIZE = int(ZOOM_AREA * SCALE)
    LAYOUT_OFFSET: int = Size.num[7]
    LAYOUT_ADJUST: int = Size.num[11]

    def __init__(self, master: tk.Canvas, screenshot: 'ScreenshotUtils'):
        self.master = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.zoom_imgtk: ImageTk.PhotoImage = None
        self.tags = (Tags.border_rect, Tags.zoom_image, Tags.vert_axis, Tags.horiz_axis)
        self.create_magnifier()
        RedrawUtils.append_redraw_tags(*self.tags)

    def create_magnifier(self):
        self.master.create_rectangle(0, 0, 0, 0, **Style.get("Magnifier", "border_rect"), tags=self.tags[0])
        self.master.create_image(0, 0, anchor=tk.NW, tags=self.tags[1])
        self.master.create_line(0, 0, 0, 0, **Style.get("Magnifier", "cross_line"), tags=self.tags[2])
        self.master.create_line(0, 0, 0, 0, **Style.get("Magnifier", "cross_line"), tags=self.tags[3])

    def update_magnifier(self, x: int, y: int):
        za = self.ZOOM_AREA
        img = self.screenshot.current_image.crop(
            (x - za // 2, y - za // 2, x + za // 2, y + za // 2
        )).resize((self.ZOOM_SIZE, self.ZOOM_SIZE))
        self.toggle_magnifier(conceal=False)
        self.zoom_imgtk = ImageTk.PhotoImage(img)
        self.master.itemconfig(self.tags[1], image=self.zoom_imgtk)
        ScreenshotUtils.magnifier_coords = self.caculate_magnifier_pos(x, y)
        self.__update_magnifier(*ScreenshotUtils.magnifier_coords)

    def __update_magnifier(self, x: int, y: int) -> None:
        zs = self.ZOOM_SIZE
        self.master.coords(self.tags[0], x, y, x + zs, y + zs)
        self.master.coords(self.tags[1], x, y)
        self.master.coords(self.tags[2], x + zs // 2, y, x + zs // 2, y + zs)
        self.master.coords(self.tags[3], x, y + zs // 2, x + zs, y + zs // 2)

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
    
    def is_concealed(self) -> bool:
        return self.master.itemcget(self.tags[0], "state") == "hidden"
    
    def toggle_magnifier(self, conceal: bool = False):
        state = "hidden" if conceal else "normal"
        for tag in self.tags:
            self.master.itemconfig(tag, state=state)


class ScreenshotTip(object):
    def __init__(self, master: ScreenshotCanvas, screenshot: 'ScreenshotUtils'):
        self.master: ScreenshotCanvas = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.__rgb_tuple: bool = True
        self.tags = (Tags.pos_tip, Tags.pos_bg, Tags.rgb_tip, Tags.rgb_bg, Tags.rect_size_tip, Tags.rect_size_bg)
        self.create_pointer_tip()
        self.create_rect_size_tip()
        RedrawUtils.append_redraw_tags(*self.tags)

    def create_pointer_tip(self):
        self.master.create_text(0, 0, **Style.get("Magnifier", "tip_characters"), tags=self.tags[0])
        self.master.create_text(0, 0, **Style.get("Magnifier", "tip_characters"), tags=self.tags[2])
        self.master.create_rectangle(0, 0, 0, 0, **Style.get("Magnifier", "tip_bg"), tags=self.tags[1])
        self.master.create_rectangle(0, 0, 0, 0, **Style.get("Magnifier", "tip_bg"), tags=self.tags[3])

    def create_rect_size_tip(self):
        self.master.create_text(0, 0, **Style.get("Magnifier", "tip_characters"), tags=self.tags[4])
        self.master.create_rectangle(0, 0, 0, 0, **Style.get("Magnifier", "tip_bg"), tags=self.tags[5])

    def update_pointer_tip(self, x: int, y: int):
        self.toggle_pointer_tip(conceal=False)
        magnifier_x, magnifier_y = ScreenshotUtils.magnifier_coords
        zoom_size = Magnifier.ZOOM_SIZE
        # 更新位置信息
        pos_info = f"POS: ({x}, {y})"
        pos_tip_coord = (magnifier_x, magnifier_y + zoom_size + Size.num[3])
        # 更新RGB信息
        tuple_rgb_color = self.screenshot.current_image.getpixel((x, y))
        rgb_info = self.color_info_convertor(tuple_rgb_color)
        rgb_tip_coord = (magnifier_x, magnifier_y + zoom_size + Size.num[9])
        self._update_text_and_bg(self.tags[0], pos_info, pos_tip_coord)
        self._update_text_and_bg(self.tags[2], rgb_info, rgb_tip_coord)

    def update_rect_size_tip(self):
        self.toggle_rect_size_tip(conceal=False)
        left, top, right, bottom = ScreenshotUtils.rect_coords
        rect_w, rect_h = int(right - left), int(bottom - top)
        rect_size_tip_info = f"{rect_w} × {rect_h}"
        rect_size_tip_coord = (max(left, 0), max(top - Size.num[8], 0))
        self._update_text_and_bg(self.tags[4], rect_size_tip_info, rect_size_tip_coord)

    def _update_text_and_bg(self, text_item, text_content, text_coords):
        self.master.itemconfig(text_item, text=text_content)
        self.master.coords(text_item, *text_coords)
        bg_item = self.tags[self.tags.index(text_item) + 1]
        bg_coords = self.master.bbox(text_item)
        self.master.coords(bg_item, *bg_coords)
        self.master.tag_raise(text_item)

    def toggle_pointer_tip(self, conceal: bool = False):
        self._toggle_items_visibility(self.tags[0: 4], conceal)

    def toggle_rect_size_tip(self, conceal: bool = False):
        self._toggle_items_visibility(self.tags[4: 6], conceal)

    def toggle_rgb_state(self):
        if self.master.itemcget(self.tags[0], "state") == "hidden":
            return
        self.__rgb_tuple = not self.__rgb_tuple
        self.update_pointer_tip(*self.master.winfo_pointerxy())

    def _toggle_items_visibility(self, items, conceal: bool):
        state = "hidden" if conceal else "normal"
        for item in items:
            self.master.itemconfig(item, state=state)
    
    def color_info_convertor(self, color: tuple[int, int, int]) -> str:
        if self.__rgb_tuple:
            return f"RGB: {color}"
        else:
            return 'RGB: #' + ''.join(map(lambda x: f'{x:02x}', color)).upper()

    def current_color(self) -> str:
        color_info: str = self.master.itemcget(self.tags[2], "text")
        color_info = color_info.replace("RGB:", "")
        return color_info.strip()


class AdjustableRect(object):
    """
    The judgement seq is so important that you must care about:
    (right, bottom), (left, top), (right, top), (left, bottom),
    (center_x, top), (center_x, bottom), (left, center_y), (right, center_y)
    """
    ANCHOR_SIZE = 5
    ANCHOR_HOVER_DISTANCE = 20
    CURSOR_FILES_NAME = ["aero_nwse_l.cur", "aero_nesw_l.cur", "aero_ns_l.cur", "aero_ew_l.cur"]
    CURSOR_FILES = [f"@src/cur/{cursor_file}" for cursor_file in CURSOR_FILES_NAME]
    CURSORS = [
        CURSOR_FILES[0], CURSOR_FILES[0], CURSOR_FILES[1], CURSOR_FILES[1],
        CURSOR_FILES[2], CURSOR_FILES[2], CURSOR_FILES[3], CURSOR_FILES[3],
        "fleur", "arrow"
    ]

    def __init__(self, master: ScreenshotCanvas, screenshot: 'ScreenshotUtils'):
        self.master: ScreenshotCanvas = master
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.embed_image_canvas: tk.Canvas = None
        self.tags = (Tags.embed_image, Tags.border_window)
        self.__anchors: list[int] = []
        self.anchor_id: int = 0
        self.create_rect()
    
    def rect_coords(self, recalculate: bool = False) -> tuple[int, int, int, int]:
        if recalculate:
            x1, x2 = sorted([self.screenshot.start_x, self.screenshot.end_x])
            y1, y2 = sorted([self.screenshot.start_y, self.screenshot.end_y])
            x2 += (x2 != Window.screen_width)
            y2 += (y2 != Window.screen_height)
            return x1, y1, x2, y2
        else:
            return self.master.bbox(self.tags[1])

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
                **Style.get("Selection", "anchor")
            )
            self.__anchors.append(anchor)

    def create_embed_canvas(self) -> tk.Canvas:
        canvas = tk.Canvas(self.master, highlightthickness=0)
        canvas.create_image(0, 0, anchor=tk.NW, image=self.master.orig_imagetk, tags=self.tags[0])
        canvas.create_rectangle(
            0, 0, 0, 0,
            **Style.get("Selection", "border_rect"), tags=Tags.border_rect
        )
        return canvas

    def create_rect(self) -> None:
        self.embed_image_canvas = self.create_embed_canvas()
        self.master.create_window(
            -Window.screen_width, -Window.screen_height, 
            anchor=tk.NW, window=self.embed_image_canvas, tags=self.tags[1]
        )
        self.create_anchors()
        RedrawUtils.set_redraw_carrier(self.embed_image_canvas)

    def on_press(self, event):
        self.screenshot.start_x = event.x_root
        self.screenshot.start_y = event.y_root

    def on_release(self):
        self._move_anchors()
        self.toggle_anchors(hidden=False)
        
    def on_motion(self, event):
        self.anchor_id = self.get_anchor(event)
        cursor = self.CURSORS[self.anchor_id]
        self.master.config(cursor=cursor)

    def toggle_anchors(self, hidden: bool = False):
        state = tk.HIDDEN if hidden else tk.NORMAL
        if self.master.itemcget(self.__anchors[0], "state") == state:
            return
        for anchor in self.__anchors:
            self.master.itemconfig(anchor, state=state)

    def _move_anchors(self):
        cls = self.__class__
        for anchor, coord in zip(self.__anchors, self.anchor_coords()):
            self.master.coords(
                anchor, coord[0] - cls.ANCHOR_SIZE, coord[1] - cls.ANCHOR_SIZE, 
                coord[0] + cls.ANCHOR_SIZE, coord[1] + cls.ANCHOR_SIZE
            )

    def _move_border(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self.embed_image_canvas.coords("border_rect", 0, 0, x2 - x1, y2 - y1)

    def _calculate_move_coords(self, event):
        offset_x = event.x_root - self.screenshot.move_start_x
        offset_y = event.y_root - self.screenshot.move_start_y
        if self.screenshot.start_x + offset_x > -1 and\
              self.screenshot.end_x + offset_x < Window.screen_width + 1:
            self.screenshot.start_x += offset_x
            self.screenshot.end_x += offset_x
        if  self.screenshot.start_y + offset_y > -1 and\
              self.screenshot.end_y + offset_y < Window.screen_height + 1:
            self.screenshot.start_y += offset_y
            self.screenshot.end_y += offset_y
        self.screenshot.move_start_x = event.x_root
        self.screenshot.move_start_y = event.y_root

    def on_drag(self, event):
        if self.anchor_id == 8:
            self.move_rect(event)
            return
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
        self.resize_rect()

    def resize_rect(self):
        self.toggle_anchors(hidden=False)
        x1, y1, x2, y2 = ScreenshotUtils.rect_coords = self.rect_coords(recalculate=True)
        self.master.coords(self.tags[1], x1, y1)
        self.master.itemconfig(self.tags[1], width=x2 - x1, height=y2 - y1)
        self.embed_image_canvas.coords(self.tags[0], -x1, -y1)
        self._move_border(x1, y1, x2, y2)
        self._move_anchors()

    def move_rect(self, event):
        self.toggle_anchors(hidden=True)
        self._calculate_move_coords(event)
        x1, y1, x2, y2 = ScreenshotUtils.rect_coords = self.rect_coords(recalculate=True)
        # 新构建window进行【离屏渲染】，强制一次性刷新画面
        self.embed_image_canvas = self.create_embed_canvas()
        self.embed_image_canvas.coords(self.tags[0], -x1, -y1)
        self.master.itemconfig(self.tags[1], window=self.embed_image_canvas)
        RedrawUtils.set_redraw_carrier(self.embed_image_canvas)
        self.master.coords(self.tags[1], x1, y1)
        self._move_border(x1, y1, x2, y2)
        self.master.update_idletasks()


class EditBar(object):
    DELTA = Size.num[3]
    def __init__(self, master: ScreenshotCanvas):
        self.master: ScreenshotCanvas = master
        self.__edit_bar = self.create_edit_bar()

    def get_children(self):
        return self.__edit_bar.winfo_children()

    def create_edit_bar(self):
        def set_character_btn(text: str) -> CharacterButton:
            normal_style = Style.get("Button", "designs")
            special_style = Style.get("Button", "special")
            if text in special_style:
                normal_style = normal_style | special_style[text]
            btn = CharacterButton(edit_bar, text=text, **normal_style)
            btn.pack(side=tk.RIGHT, padx=Size.num[3])
            return btn
        edit_bar = tk.Frame(self.master, Style.get("Frame"))
        set_character_btn("×")
        set_character_btn("√")
        set_character_btn("T")
        set_character_btn(" 📌")
        return edit_bar
    
    def toggle_edit_bar(self, conceal: bool = False):
        if conceal:
            self.__edit_bar.place_forget()
            return
        width = self.__edit_bar.winfo_reqwidth()
        height = self.__edit_bar.winfo_reqheight()
        x1, y1, x2, y2 = ScreenshotUtils.rect_coords
        delta = self.__class__.DELTA
        place_x = max(min(x2 - width, Window.screen_width - width), 0)
        place_y = min(y2 + delta, Window.screen_height - height)
        if place_y == Window.screen_height - height and x1 - height - delta > 0:
            place_y = y1 - height - delta
        self.__edit_bar.place(x=place_x, y=place_y, width=width, height=height)
        self.__edit_bar.tkraise()

    def _bind_command(self, command_list: list):
        widgets: list[CharacterButton] = self.get_children()
        for widget, command in zip(widgets, command_list):
            widget.config(command=command)


class ShowImageCanvas(BasicImageCanvas):
    def __init__(self, master: 'ScreenshotTool'):
        super().__init__(master)
        self.master: 'ScreenshotTool' = master
        self.__basic_frame = tk.Frame(master, bg=Style.get("ShowImageCanvas", "bg"))
        self.__canvas_image: ImageCanvas = None

    def current_show_image(self) -> Image.Image:
        return self.__canvas_image.raw_image()

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
            self.__canvas_image.set_basic_canvas(self.__basic_frame, Style.get("ShowImageCanvas", "bg"))
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
        super().__init__()
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
        self.nail_canvas = DrawingCanvas(self, **Style.get("NailImageCanvas"))
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
        super().__init__(self.master, **Style.get("ButtonMenu"))
        
    def initialize_ico(self):
        if ButtonMenu.ICO_TUPLE:
            return
        ButtonMenu.ICO_TUPLE = (
            tk.PhotoImage(file=File.copy_ico),
            tk.PhotoImage(file=File.save_ico),
            tk.PhotoImage(file=File.kill_ico)
        )

    def add_default_command(self) -> None:
        name_list = ("copy", "save", "kill")
        for name, image in zip(name_list, self.ICO_TUPLE):
            self.add_command(
                label=name, command=lambda name=name: self.executant.call(name),
                compound=tk.LEFT, image=image
            )

    def crash(self):
        super().destroy()
        for attr in self.__dict__:
            setattr(self, attr, None)

