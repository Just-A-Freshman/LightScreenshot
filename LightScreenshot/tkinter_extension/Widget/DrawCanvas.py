import math
import time

from threading import Thread
import tkinter as tk

from PIL import Image, ImageTk

from .Scrollbar import AutoBorderlessScrollbar


class ImageCanvas(object):
    delta = 1.2
    filter = Image.Resampling.LANCZOS
    huge_size = 14000  # define size of the huge image
    band_width = 1024
    reduction = 2
    max_scale = 16
    min_scale = 0.3

    def __init__(self, image: Image.Image):
        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes
        self.__raw_image = image  # raw image, public for outer classes
        self.__previous_state = 0  # previous state of the keyboard
        self.__huge = False     # Decide if this image huge or not
        self.__image = self.__raw_image  # open image, but down't load it
        self.container = None
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

    def raw_image(self) -> Image.Image:
        return self.__raw_image

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

    def set_basic_canvas(self, master, bg: str):
        self.__imframe = tk.Frame(master, bg=bg)
        hbar = AutoBorderlessScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoBorderlessScrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we', ipadx=10)
        vbar.grid(row=0, column=1, sticky='ns')
        self.canvas = tk.Canvas(
            self.__imframe, highlightthickness=0, bg=bg,
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
        """ Put CanvasImage widget on the master widget """
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
        self.fit_to_size(width, height)
        image: Image.Image = self.__raw_image.copy()
        image.thumbnail((width, height), Image.Resampling.NEAREST)
        imagetk = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor='nw', image=imagetk)
        self.canvas.imagetk = imagetk

    def __show_image(self):
        if self.container is None:
            return
        """ Show image on the Canvas. Implements correct image zoom almost like in Google Maps """
        box_image = self.canvas.coords(self.container)  # get image area
        # get visible area of the canvas
        box_canvas = (
            self.canvas.canvasx(0),  self.canvas.canvasy(0),
            self.canvas.canvasx(self.canvas.winfo_width()), self.canvas.canvasy(self.canvas.winfo_height())
        )
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly
        # Get scroll region box
        if len(box_img_int) != 4:
            return
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



class DrawingCanvas(tk.Canvas):
    DOUBLE_CLICK_INTERVAL: float = 0.3
    LINE_MERGE_SLOPE_THRESHOLD: float = 0.05
    PEN_SIZE_RANGE: tuple[int, int] = (1, 124)
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._bind_events()
        self.focus_set()
        self.__stroke_history: list[list[str]] = list()
        self.__current_stroke: list[str] = list()
        self.__preview_item: str = None
        self.pen_color: str = 'red'
        self.drawing_mode: bool = False
        self.last_ctrl_press: float = 0.0
        self.pen_size: int = 8
        self.last_x: int = None
        self.last_y: int = None

    def _bind_events(self) -> None:
        # 控制键监听
        self.bind('<Control_L>', self.__start_drawing)
        self.bind('<Control-KeyRelease>', self.__stop_drawing)
        # 鼠标监听
        self.bind('<B1-Motion>', self._draw_continuous)
        self.bind('<Motion>', self.__move_brush_preview)
        self.bind('<Button-1>', self._draw_single_point)
        self.bind("<ButtonRelease-1>", self._finalize_stroke)
        # 功能快捷键
        self.bind('<Control-MouseWheel>', self.__adjust_pen_size)
        self.bind("<Control-z>", self.undo_last_stroke)

    def stroke_history(self) -> list[str]:
        return [item for stroke in self.__stroke_history for item in stroke]

    def __start_drawing(self, event) -> None:
        if self._is_double_ctrl_click():
            return self.__change_pen_color(event)
        self.drawing_mode = True
        self.config(cursor='pencil')
        self.__update_brush_preview(event)

    def __stop_drawing(self, event) -> None:
        self.drawing_mode = False
        self.config(cursor='')
        self.delete(self.__preview_item)
        self.__preview_item = None

    def _finalize_stroke(self, event) -> None:
        self.last_x = self.last_y = None
        self.__stroke_history.append(self.__current_stroke)
        self.__current_stroke = []

    def __change_pen_color(self, event) -> None:
        from tkinter import colorchooser
        color = colorchooser.askcolor()[1]
        if color:
            self.pen_color = color
        del colorchooser

    def __adjust_pen_size(self, event) -> None:
        min_size, max_size = self.PEN_SIZE_RANGE
        if event.delta > 0:
            self.pen_size = min(max_size, self.pen_size + 1)
        else:
            self.pen_size = max(min_size, self.pen_size - 1)
        self.__update_brush_preview(event)

    def __move_brush_preview(self, event) -> None:
        try:
            x1, y1, x2, y2 = self.coords(self.__preview_item)
            self.move(self.__preview_item, event.x - (x1 + x2) / 2, event.y - (y1 + y2) / 2)
        except Exception:
            pass

    def __update_brush_preview(self, event) -> None:
        self.delete(self.__preview_item)
        self.__preview_item = self._draw_single_point(event, record=False)

    def _is_double_ctrl_click(self) -> bool:
        current_time = time.time()
        is_double_click = (current_time - self.last_ctrl_press) < self.DOUBLE_CLICK_INTERVAL
        self.last_ctrl_press = current_time
        return is_double_click

    def _is_collineation(self, line1_coords: tuple[int], line2_coords: tuple[int]) -> bool:
        x1, y1, x2, y2 = line1_coords
        x3, y3, x4, y4 = line2_coords

        dx1 = x2 - x1
        dy1 = y2 - y1
        dx2 = x4 - x3
        dy2 = y4 - y3
        
        if dx1 == 0 or dx2 == 0:
            return x1 == x3

        if abs(dy1 / dx1 - dy2 / dx2) < self.LINE_MERGE_SLOPE_THRESHOLD:
            return (dx1 * dx2 >= 0) and (dy1 * dy2 >= 0)
        return False
    
    def _collineation_merge(self, event) -> tuple[int]:
        current_line_coords = (self.last_x, self.last_y, event.x, event.y)
        if len(self.__current_stroke) < 2:
            return current_line_coords
        last_line_id = self.__current_stroke[-1]
        last_line_coords = self.coords(last_line_id)
        if len(last_line_coords) != 4:
            return current_line_coords
        if self._is_collineation(last_line_coords, current_line_coords):
            self.delete(last_line_id)
            self.__current_stroke.pop()
            return (last_line_coords[0], last_line_coords[1], event.x, event.y)
        return current_line_coords

    def _draw_continuous(self, event, record: bool = True) -> str:
        line = ""
        if not self.drawing_mode:
            return line
        if self.last_x and self.last_y:
            line_coords = self._collineation_merge(event)
            line = self.create_line(
                *line_coords, fill=self.pen_color, width=self.pen_size,
                capstyle=tk.ROUND, joinstyle=tk.ROUND
            )
            if record:
                self.__current_stroke.append(line)
        self.last_x = event.x
        self.last_y = event.y
        return line

    def _draw_single_point(self, event, record: bool = True) -> str:
        point = ""
        if not self.drawing_mode:
            return point
        radius = self.pen_size / 2
        point = self.create_oval(
            event.x - radius, event.y - radius,
            event.x + radius, event.y + radius,
            fill=self.pen_color, outline=self.pen_color, 
        )
        self.last_x = event.x
        self.last_y = event.y
        if record:
            self.__current_stroke.append(point)
        return point

    def undo_last_stroke(self, event) -> None:
        if len(self.__stroke_history) == 0:
            return
        last_draw = self.__stroke_history.pop()
        for item in last_draw:
            self.delete(item)

