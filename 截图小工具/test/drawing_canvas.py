import time


import tkinter as tk
from tkinter import filedialog
from threading import Thread

from PIL import Image, ImageDraw


class DrawingCanvas(tk.Canvas):
    DOUBLE_CLICK_INTERVAL: float = 0.3
    LINE_MERGE_SLOPE_THRESHOLD: float = 0.05
    PEN_SIZE_RANGE: tuple[int, int] = (1, 124)
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._bind_events()
        self.focus_set()
        self.__stroke_history: list[list[str]] = list()
        self.__current_stroke: list[str] = list()
        self.__preview_item: str = None
        self.bg_image: Image.Image
        self.pen_color: str = 'black'
        self.drawing_mode: bool = False
        self.last_ctrl_press: float = 0.0
        self.pen_size: int = 3
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
        self.bind("<Control-s>", self.save_canvas_as_image)

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

    def save_canvas_as_image(self, event):
        self.delete(self.__preview_item)
        orig_bg_image = self.bg_image
        draw_thread = Thread(target=self.bg_image_griding)
        draw_thread.start()
        filename = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")],
            initialfile="canvas_image.png"
        )
        if not filename:
            return
        draw_thread.join()
        self.bg_image.save(filename)
        self.bg_image = orig_bg_image

    def bg_image_griding(self):
        if self.bg_image is None:
            width = self.winfo_width()
            height = self.winfo_height()
            bg = self.winfo_rgb(self.cget("background"))
            self.bg_image = Image.new('RGB', (width, height), bg)
        draw: ImageDraw.ImageDraw = ImageDraw.Draw(self.bg_image)
        for item in self.find_all():
            item_type = self.type(item)
            coords = self.coords(item)
            if item_type == 'line':
                self.draw_line_with_points(draw, coords, fill=self.itemcget(item, 'fill'), width=int(float(self.itemcget(item, 'width'))))
            elif item_type == 'oval':
                draw.ellipse(coords, fill=self.itemcget(item, 'fill'), outline=self.itemcget(item, 'outline'))

    def draw_line_with_points(self, draw: ImageDraw.ImageDraw, coords: tuple[int], fill: str, width: float):
        points = self.get_line_points(*coords)
        radius = width / 2
        for point in points:
            x, y = point
            coords = (x - radius, y - radius, x + radius, y + radius)
            draw.ellipse(coords, fill=fill)

    @staticmethod
    def get_line_points(x1, y1, x2, y2):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = -1 if x1 > x2 else 1
        sy = -1 if y1 > y2 else 1
        if dx > dy:
            err = dx / 2.0
            while x != x2:
                yield (x, y)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y2:
                yield (x, y)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        yield (x, y)



if __name__ == "__main__":
    import ctypes
    from PIL import ImageTk
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    image = Image.open(r"D:\PhotoDir\9\1904.jpeg")
    root = tk.Tk()
    root.geometry(f"{image.width}x{image.height}")
    canvas = DrawingCanvas(root)
    canvas.pack(expand=True, fill=tk.BOTH)
    imgtk = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
    canvas.bg_image = image
    canvas.imgtk = imgtk
    root.mainloop()
