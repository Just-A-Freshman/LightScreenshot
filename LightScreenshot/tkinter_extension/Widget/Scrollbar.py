from tkinter import ttk
from typing import Literal, Callable
from pathlib import Path
import json




class BorderlessScrollbar(ttk.Scrollbar):
    def __init__(
            self, 
            master, 
            background: str = "#5F5F5F", 
            troughcolor: str = "#202020", 
            active_color: str = "#737373", 
            orient: Literal["horizontal", "vertical"] = "vertical",
            command: Callable[..., tuple[float, float] | None] | str = ""
        ):
        super().__init__(master=master, orient=orient, command=command)
        self.background = background
        self.troughcolor = troughcolor
        self.active_color = active_color
        self.set_scrollbar_style()

    def set_scrollbar_style(self):
        style = ttk.Style()
        style.theme_use("classic")
        current_path = Path(__file__).resolve()
        config_path = current_path.parent.parent / 'Style' / 'Scrollbar.json'
        with open(config_path, "r", encoding="utf-8") as file:
            scrollbar_style_template: dict = json.load(file)
        scrollbar_style_sheet = dict()
        for key, value in scrollbar_style_template.items():
            if value == "background":
                scrollbar_style_sheet[key] = self.background
            elif value == "troughcolor":
                scrollbar_style_sheet[key] = self.troughcolor
            else:
                scrollbar_style_sheet[key] = value
        style.map("TScrollbar", background=[('active', self.active_color)])
        style.configure("Vertical.TScrollbar", **scrollbar_style_sheet)
        style.configure("Horizontal.TScrollbar", **scrollbar_style_sheet)



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


class AutoBorderlessScrollbar(BorderlessScrollbar, AutoScrollbar):
    pass




if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    root.title("单独配置的 Scrollbar 示例")
    text_box = tk.Text(root, width=40, height=10)
    text_box.grid(row=0, column=0, sticky="nsew")
    scrollbar = AutoBorderlessScrollbar(root, command=text_box.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    text_box.config(yscrollcommand=scrollbar.set)
    for i in range(20):
        text_box.insert(tk.END, f"这是第 {i + 1} 行文本。\n")

    root.mainloop()
