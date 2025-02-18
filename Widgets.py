import tkinter as tk
import math
from threading import Thread
from tkinter import ttk
from Setting import SCREEN_WIDTH, SCREEN_HEIGHT, Style
from PIL import Image, ImageTk
from typing import TYPE_CHECKING

from time import perf_counter


if TYPE_CHECKING:
    from Utils import ScreenshotUtils
    from MainControl import ScreenshotTool


class FlatButton(tk.Label):
    def __init__(
            self, parent, command=None, enter_fg="#000000", 
            click_color="#25C253", *args, **kwargs
        ):
        super().__init__(parent, *args, **kwargs)
        self.__fg = fg = kwargs.get("fg", "#3B3B3B")
        self.__enter_fg = enter_fg
        self.__click_fg = click_color
        self.command = command
        self.config(cursor="hand2", fg=fg)
        if fg == enter_fg:
            raise ValueError("enter_fg must be different from fg")
        self.bind("<Enter>", lambda _: self.config(fg=enter_fg))
        self.bind("<Leave>", lambda _: self.config(fg=self.__fg))
        self.bind("<Button-1>", lambda _: self.config(fg=self.__click_fg))
        self.bind("<ButtonRelease-1>", self.__command)
 
    def __command(self, event):
        try:
            if self.cget("fg") in (self.__enter_fg, self.__click_fg):
                self.command(event)
            self.config(fg=self.__fg)
        except tk.TclError:
            pass
        except TypeError:
            self.config(fg=self.__fg)

 

class AdjustableRect(object):
    """
    The judgement seq is so important that you must care about:
    (right, bottom), (left, top), (right, top), (left, bottom),
    (center_x, top), (center_x, bottom), (left, center_y, ), (right, center_y)
    """
    ANCHOR_SIZE = 3
    ANCHOR_HOVER_DISTANCE = 20
    CURSOR_FILES_NAME = ["aero_nwse_l.cur", "aero_nesw_l.cur", "aero_ns_l.cur", "aero_ew_l.cur"]
    CURSOR_FILES = [f"@C:/Windows/Cursors/{cursor_file}" for cursor_file in CURSOR_FILES_NAME]
    CURSORS = [
        CURSOR_FILES[0], CURSOR_FILES[0], CURSOR_FILES[1], CURSOR_FILES[1],
        CURSOR_FILES[2], CURSOR_FILES[2], CURSOR_FILES[3], CURSOR_FILES[3],
        "fleur", "arrow"
    ]

    def __init__(self, parent, screenshot):
        self.parent: tk.Canvas = parent
        self.screenshot: 'ScreenshotUtils' = screenshot
        self.__rect: int = 0
        self.__anchors: list[int] = []
        self.anchor_id: int = 0
 
    def rect_coords(self) -> tuple[int, int, int, int]:
        return self.parent.coords(self.__rect)
    
    def anchor_coords(self) -> tuple[int, int, int, int]:
        left, top, right, bottom = self.rect_coords()
        horizontal_middle = (left + right) // 2
        vertical_middle = (top + bottom) // 2
        return (
            (left, top), (horizontal_middle, top), (right, top), (right, vertical_middle),
            (right, bottom), (horizontal_middle, bottom), (left, bottom), (left, vertical_middle)
        )
    
    def rect_width_height(self) -> tuple[int, int]:
        left, top, right, bottom = self.rect_coords()
        return int(right - left), int(bottom - top)
    
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
            if near(event.x, pos[0]) and near(event.y, pos[1]):
                return index
        if left < event.x < right and top < event.y < bottom:
            return 8
        return -1
 
    def create_anchors(self):
        cls = self.__class__
        for coord in self.anchor_coords():
            anchor = self.parent.create_rectangle(
                coord[0]-cls.ANCHOR_SIZE, coord[1]-cls.ANCHOR_SIZE,
                coord[0]+cls.ANCHOR_SIZE, coord[1]+cls.ANCHOR_SIZE,
                fill="#1AAE1A", outline="#1AAE1A"
            )
            self.__anchors.append(anchor)

    def create_rect(self) -> None:
        self.__rect= self.parent.create_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, outline='#1AAE1A', width=2)
        self.create_anchors()

    def move_anchors(self):
        cls = self.__class__
        for anchor, coord in zip(self.__anchors, self.anchor_coords()):
            self.parent.coords(
                anchor, coord[0]-cls.ANCHOR_SIZE, coord[1]-2, 
                coord[0]+cls.ANCHOR_SIZE, coord[1]+cls.ANCHOR_SIZE
            )

    def on_press(self, event):
        self.screenshot.start_x = event.x
        self.screenshot.start_y = event.y

    def on_release(self, _):
        self.screenshot.start_x, self.screenshot.start_y,\
        self.screenshot.end_x, self.screenshot.end_y = self.rect_coords()
 
    def on_hover(self, event):
        self.anchor_id = self.get_anchor(event)
        cursor = self.CURSORS[self.anchor_id]
        self.parent.config(cursor=cursor)

    def move_rect(self, event):
        offset_x = event.x - self.screenshot.move_start_x
        offset_y = event.y - self.screenshot.move_start_y
        if self.screenshot.start_x + offset_x >= 0 and self.screenshot.end_x + offset_x <= SCREEN_WIDTH:
            self.screenshot.start_x += offset_x
            self.screenshot.end_x += offset_x
        if  self.screenshot.start_y + offset_y >= 0 and self.screenshot.end_y + offset_y <= SCREEN_HEIGHT:
            self.screenshot.start_y += offset_y
            self.screenshot.end_y += offset_y
        self.screenshot.move_start_x = event.x
        self.screenshot.move_start_y = event.y
        self.parent.coords(self.__rect, self.screenshot.start_x, self.screenshot.start_y, self.screenshot.end_x, self.screenshot.end_y)
        self.move_anchors()

    def rect_adjust(self, event):
        if self.anchor_id == 8:
            return self.move_rect(event)
        if self.anchor_id == 0:
            self.screenshot.end_x, self.screenshot.end_y = event.x, event.y
        elif self.anchor_id == 1:
            self.screenshot.start_x, self.screenshot.start_y = event.x, event.y
        elif self.anchor_id == 2:
            self.screenshot.end_x, self.screenshot.start_y = event.x, event.y
        elif self.anchor_id == 3:
            self.screenshot.start_x, self.screenshot.end_y = event.x, event.y
        elif self.anchor_id == 4:
            self.screenshot.start_y = event.y
        elif self.anchor_id == 5:
            self.screenshot.end_y = event.y
        elif self.anchor_id == 6:
            self.screenshot.start_x = event.x
        elif self.anchor_id == 7:
            self.screenshot.end_x = event.x
        else:
            return
        self.parent.coords(self.__rect, self.screenshot.start_x, self.screenshot.start_y, self.screenshot.end_x, self.screenshot.end_y)
        self.move_anchors()


class ShowImageCanvas(object):
    def __init__(self, parent: 'ScreenshotTool'):
        self.parent: 'ScreenshotTool' = parent
        self.__basic_frame = tk.Frame(parent, bg="#202020")
        self.__canvas_image: CanvasImage = None

    def __pack_basic_frame(self):
        self.__basic_frame.pack(expand=True, fill="both")
        self.__basic_frame.rowconfigure(0, weight=1)
        self.__basic_frame.columnconfigure(0, weight=1)

    def show_image(self, image: Image.Image):
        show_width, show_height = self.__get_fit_show_size(image)
        self.parent.geometry(f"{show_width}x{show_height + self.parent.menu_bar.winfo_height()}")
        self.__pack_basic_frame()
        if self.__canvas_image:
            self.__init_canvas_image_state(image)
        else:
            self.__canvas_image = CanvasImage(image)
            self.__canvas_image.set_basic_canvas(self.__basic_frame)
        self.__show_image(show_width, show_height)

    def __get_fit_show_size(self, image: Image.Image) -> tuple[int, int]:
        if image.width < SCREEN_WIDTH // 2 and image.height < SCREEN_HEIGHT // 2:
            show_width, show_height = image.size
        else:
            image_scale = image.width / image.height
            screen_scale = SCREEN_WIDTH / SCREEN_HEIGHT
            if image_scale > screen_scale:
                show_width = SCREEN_WIDTH // 2
                show_height = int(show_width / image_scale)
            else:
                show_height = SCREEN_HEIGHT // 2
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

    def destroy(self):
        self.__canvas_image.canvas.delete("all")



class AutoScrollbar(ttk.Scrollbar):
    """ A scrollbar that hides itself if it's not needed. Works only for grid geometry manager """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        raise tk.TclError('Cannot use place with the widget ' + self.__class__.__name__)


class CanvasImage:
    delta = 1.2
    filter = Image.Resampling.LANCZOS
    huge_size = 14000  # define size of the huge image
    band_width = 1024
    reduction = 2
    max_scale = 16
    min_scale = 0.3
    Image.MAX_IMAGE_PIXELS = 1000000000

    def __init__(self, image: Image.Image):
        """ Initialize the ImageFrame """
        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes
        self.__raw_image = image  # raw image, public for outer classes
        self.__previous_state = 0  # previous state of the keyboard
        self.__huge = False     # Decide if this image huge or not
        self.__image = self.__raw_image  # open image, but down't load it
        self.imwidth, self.imheight = self.__image.size  # public for outer classes
        if self.imwidth * self.imheight > math.pow(self.__class__.huge_size, 2) and \
           self.__image.tile[0][0] == 'raw':  # only raw images could be tiled
            self.__huge = True  # image is huge
            self.__offset = self.__image.tile[0][2]  # initial tile offset
            self.__tile = [
                self.__image.tile[0][0],  [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                self.__offset, self.__image.tile[0][3]
            ]  # list of arguments to the decoder
        Thread(target=self.init_pyramid).start()
        self.__ratio = max(self.imwidth, self.imheight) / self.__class__.huge_size if self.__huge else 1.0
        self.__curr_img = 0  # current image from the pyramid
        self.__scale = self.imscale * self.__ratio  # image pyramide scale

    def fit_to_size(self, width, height):
        """ Calculate initial scale to fit the image to the container """
        self.imscale = self.get_fit_scale(width, height)
        # Update scale-related variables
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__class__.reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__class__.reduction, max(0, self.__curr_img))
        self.canvas.scale('all', 0, 0, self.imscale, self.imscale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes

    def get_fit_scale(self, width, height) -> float:
        image_aspect_ratio = self.imwidth / self.imheight
        view_ratio = width / height
        if image_aspect_ratio > view_ratio:
            return width / self.imwidth
        else:
            return height / self.imheight

    def set_basic_canvas(self, parent):
        self.__imframe = tk.Frame(parent, bg=Style.bg3)
        # Vertical and horizontal scrollbars for canvas
        style = Style()
        style.set_scrollbar_style()
        hbar = AutoScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoScrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we', ipadx=10)
        vbar.grid(row=0, column=1, sticky='ns')
        # Create canvas and bind it with scrollbars. Public for outer classes
        self.canvas = tk.Canvas(
            self.__imframe, highlightthickness=0, bg=Style.bg3,
            xscrollcommand=hbar.set, yscrollcommand=vbar.set
        )
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update_idletasks()  # refresh canvas state
        hbar.configure(command=self.__scroll_x)  # bind scrollbars to the canvas
        vbar.configure(command=self.__scroll_y)
        self.bind_event()

    def set_container(self):
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)

    def init_pyramid(self) -> list:
        self.__pyramid = [self.smaller()] if self.__huge else [self.__raw_image]
        current_image = self.__pyramid[-1]
        while current_image.size[0] > 512 and current_image.size[1] > 512:
            new_width = int(current_image.size[0] / self.__class__.reduction)
            new_height = int(current_image.size[1] / self.__class__.reduction)
            current_image = current_image.resize((new_width, new_height), self.__class__.filter)
            self.__pyramid.append(current_image)

    def bind_event(self):
        """ Bind event to the CanvasImage """
        self.canvas.bind('<Configure>', lambda _: self.__show_image())  # handle window resize event
        self.canvas.bind('<ButtonPress-1>', self.__move_from)  # remember canvas position
        self.canvas.bind('<B1-Motion>',     self.__move_to)  # move canvas to the new position
        self.canvas.bind('<ButtonPress-1>', self.__move_from)  # remember canvas position
        self.canvas.bind('<B1-Motion>',     self.__move_to)  # move canvas to the new position
        self.canvas.bind('<MouseWheel>', self.__wheel)  # zoom for Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.__wheel)  # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.__wheel)  # zoom for Linux, wheel scroll up
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # when too many key stroke events in the same time
        self.canvas.bind('<Key>', lambda event: self.canvas.after_idle(self.__keystroke, event))

    def smaller(self):
        """ Resize image proportionally and return smaller image """
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__class__.huge_size), float(self.__class__.huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2  # it equals to 1.0
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(w2)  # band length
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1  # compression ratio
            w = int(w2)  # band length
        else:  # aspect_ratio1 < aspect_ration2
            image = Image.new('RGB', (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(h2 * aspect_ratio1)  # band length
        i, j, n = 0, 1, round(0.5 + self.imheight / self.__class__.band_width)
        while i < self.imheight:
            # print('\rOpening image: {j} from {n}'.format(j=j, n=n), end='')
            band = min(self.__class__.band_width, self.imheight - i)  # width of the tile band
            self.__tile[1][3] = band  # set band width
            self.__tile[2] = self.__offset + self.imwidth * i * 3  # tile offset (3 bytes per pixel)
            self.__image.close()
            self.__image = self.__raw_image  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]  # set tile
            cropped = self.__image.crop((0, 0, self.imwidth, band))  # crop tile band
            image.paste(cropped.resize((w, int(band * k)+1), self.__class__.filter), (0, int(i * k)))
            i += band
            j += 1
        # print('\r' + 30*' ' + '\r', end='')  # hide printed string
        return image

    def redraw_figures(self):
        """ Dummy function to redraw figures in the children classes """
        pass

    def grid(self, **kw):
        """ Put CanvasImage widget on the parent widget """
        self.__imframe.grid(**kw)  # place CanvasImage widget on the grid
        self.__imframe.grid(sticky='nswe')  # make frame container sticky
        self.__imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """ Exception: cannot use pack with this widget """
        raise Exception('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        """ Exception: cannot use place with this widget """
        raise Exception('Cannot use place with the widget ' + self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def show_image(self, width, height):
        # This is for show image quickly. when user try to scroll or zoom, then __show_image will be called.
        try:
            self.fit_to_size(width, height)
            image: Image.Image = self.__raw_image.copy()
            image.thumbnail((width, height), Image.Resampling.NEAREST)
            imagetk = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, anchor='nw', image=imagetk)
            self.canvas.imagetk = imagetk
        except AttributeError:
            self.__show_image()

    def __show_image(self):
        """ Show image on the Canvas. Implements correct image zoom almost like in Google Maps """
        box_image = self.canvas.coords(self.container)  # get image area
        # get visible area of the canvas
        box_canvas = (
            self.canvas.canvasx(0),  self.canvas.canvasy(0),
            self.canvas.canvasx(self.canvas.winfo_width()), self.canvas.canvasy(self.canvas.winfo_height())
        )
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [
            min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
            max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])
        ]
        # Horizontal part of the image is in the visible area
        if  box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0]  = box_img_int[0]
            box_scroll[2]  = box_img_int[2]
        # Vertical part of the image is in the visible area
        if  box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1]  = box_img_int[1]
            box_scroll[3]  = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            if self.__huge and self.__curr_img < 0:  # show huge image
                h = int((y2 - y1) / self.imscale)  # height of the tile band
                self.__tile[1][3] = h  # set the tile band height
                self.__tile[2] = self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                self.__image.close()
                self.__image = self.__raw_image  # reopen / reset image
                self.__image.size = (self.imwidth, h)  # set size of the tile band
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:  # show normal image
                image = self.__pyramid[max(0, self.__curr_img)].crop(  # crop current img from pyramid
                                    (int(x1 / self.__scale), int(y1 / self.__scale),
                                     int(x2 / self.__scale), int(y2 / self.__scale)))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__class__.filter))
            imageid = self.canvas.create_image(
                max(box_canvas[0], box_img_int[0]), max(box_canvas[1], box_img_int[1]),
                anchor='nw', image=imagetk
            )
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

    def __move_from(self, event):
        """ Remember previous coordinates for scrolling with the mouse """
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        """ Drag (move) canvas to the new position """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # zoom tile and show it on the canvas

    def outside(self, x, y):
        """ Checks if the point (x,y) is outside the image area """
        bbox = self.canvas.coords(self.container)  # get image area
        # judge if point (x,y) is inside the image area
        return not (bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3])

    def __wheel(self, event):
        """ Zoom with mouse wheel """
        cls = self.__class__
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y):
            return
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta < 0:  # scroll down, smaller
            # if round(self.__min_side * self.imscale) < 30: return  # image is less than 30 pixels
            if self.imscale / cls.delta < self.__class__.min_scale:
                return
            self.imscale /= cls.delta
            scale        /= cls.delta
        if event.num == 4 or event.delta > 0:  # scroll up, bigger
            if self.imscale > self.__class__.max_scale:
                return
            self.imscale *= cls.delta
            scale *= cls.delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__class__.reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__class__.reduction, max(0, self.__curr_img))
        self.canvas.scale('all', x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes
        self.__show_image()

    def __keystroke(self, event):
        """ Scrolling with the keyboard.
            Independent from the language of the keyboard, CapsLock, <Ctrl>+<key>, etc. """
        if event.state - self.__previous_state == 4:  # means that the Control key is pressed
            pass  # do nothing if Control key is pressed
        else:
            self.__previous_state = event.state  # remember the last keystroke state
            # Up, Down, Left, Right keystrokes
            if event.keycode in [68, 39, 102]:  # scroll right, keys 'd' or 'Right'
                self.__scroll_x('scroll',  1, 'unit', event=event)
            elif event.keycode in [65, 37, 100]:  # scroll left, keys 'a' or 'Left'
                self.__scroll_x('scroll', -1, 'unit', event=event)
            elif event.keycode in [87, 38, 104]:  # scroll up, keys 'w' or 'Up'
                self.__scroll_y('scroll', -1, 'unit', event=event)
            elif event.keycode in [83, 40, 98]:  # scroll down, keys 's' or 'Down'
                self.__scroll_y('scroll',  1, 'unit', event=event)

    def crop(self, bbox):
        """ Crop rectangle from the image and return it """
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3  # set offset of the band
            self.__image.close()
            self.__image = self.__raw_image  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # image is totally in RAM
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ ImageFrame destructor """
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # close all pyramid images
        del self.__pyramid[:]  # delete pyramid list
        del self.__pyramid  # delete pyramid variable
