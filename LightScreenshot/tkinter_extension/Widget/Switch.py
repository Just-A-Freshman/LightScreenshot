import tkinter as tk
from typing import Callable


class EllipseSwitch(tk.Canvas):
    MOVE_STEP = 6
    def __init__(
            self, 
            master: tk.Widget, 
            size: int = 40, 
            bg_off="#cccccc", 
            bg_on="#0066cc", 
            btn_off="#333333", 
            btn_on="#ffffff",
            state_changed_callback: Callable = None, 
            *args, **kwargs
        ):
        super().__init__(master, *args, **kwargs)
        self.size = size
        self.padding = size // 5
        self.bg_off = bg_off
        self.bg_on = bg_on
        self.button_off = btn_off
        self.button_on = btn_on
        self.callback = state_changed_callback
        self.__enter: bool = False
        self.__moving: bool = False
        self.__state: bool = False
        self.configure(
            width=self.size * 2, height=self.size, highlightthickness=0,
            bd=0, bg=self.master.cget("background")
        )
        self._draw_background()
        self.__create_switch_btn()
        self.__bind_event()
        
    def __bind_event(self):
        self.bind("<ButtonPress-1>", self.__on_click)
        self.bind("<ButtonRelease-1>", lambda _: self.toggle())
        self.bind("<Enter>", lambda _: self.__update_switch_btn(True))
        self.bind("<Leave>", lambda _: self.__update_switch_btn(False))

    def __on_click(self, event):
        if self.__moving:
            return
        self.coords("switch_button", *self.__switch_btn_coords(stretch=True))

    def __switch_btn_coords(self, stretch: bool=False) -> tuple[int, int, int, int]:
        y1 = self.padding
        y2 = self.size - self.padding
        if self.__state:
            x1 = self.size if stretch else self.size + self.padding
            x2 = self.size * 2 - self.padding
        else:
            x1 = self.padding
            x2 = self.size if stretch else self.size - self.padding
        return x1, y1, x2, y2

    def __update_switch_btn(self, active: bool):
        if self.__moving:
            return
        self.__enter = active
        self.padding = self.size // 6 if active else self.size // 5
        self.coords("switch_button", *self.__switch_btn_coords())
            
    def __create_switch_btn(self, stretch: bool=False) -> str:
        return self.create_oval(
            *self.__switch_btn_coords(stretch),
            fill=self.button_on if self.__state else self.button_off, 
            outline="", tag="switch_button"
        )

    def _draw_background(self):
        r = self.size // 2
        self.create_arc(
            0, 0, 2 * r, self.size, start=90, extent=180, fill=self.bg_off, 
            outline="", tags="bg"
        )
        self.create_arc(
            self.size * 2 - 2 * r, 0, self.size * 2, self.size, start=270, extent=180,
            fill=self.bg_off, outline="", tags="bg"
        )
        self.create_rectangle(
            r, 0, self.size * 2 - r, self.size, fill=self.bg_off,
            outline="", tags="bg"
        )

    def toggle(self, state: bool = None, animation: bool = True):
        if state is None:
            if self.__moving or not self.__enter:
                return
            self.__state = not self.__state
        else:
            self.__state = state
        bg_color = self.bg_on if self.__state else self.bg_off
        btn_color = self.button_on if self.__state else self.button_off
        if animation:
            self.__moving = True
            self.__move_switch_button(
                self.padding if self.__state else self.size + self.padding,
                self.size + self.padding if self.__state else self.padding
            )
        else:
            self.coords("switch_button", *self.__switch_btn_coords())
        self.itemconfig("switch_button", fill=btn_color)
        self.itemconfig("bg", fill=bg_color)
        if self.callback:
            self.callback(self.__state)
        self.configure(bg=self.master.cget("background"))

    def __move_switch_button(self, current_x: int, target_x: int):
        if self.__state and current_x <= target_x:
            self.move("switch_button", self.MOVE_STEP, 0)
            self.after(10, lambda: self.__move_switch_button(current_x + self.MOVE_STEP, target_x))
        elif not self.__state and current_x >= target_x:
            self.move("switch_button", -self.MOVE_STEP, 0)
            self.after(10, lambda: self.__move_switch_button(current_x - self.MOVE_STEP, target_x))
        else:
            self.coords("switch_button", target_x, self.padding, target_x + self.size - 2 * self.padding, self.padding + self.size - 2 * self.padding)
            self.__moving = False

    @property
    def state(self) -> bool:
        return self.__state
