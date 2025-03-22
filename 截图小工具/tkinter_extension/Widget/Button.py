import tkinter as tk
from PIL import ImageTk


class FlatButton(tk.Label):
    def __init__(
            self, 
            *args, 
            enter_bg="#99D9EA", 
            **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.image = ""
        self.__focus: bool = False
        self.__enter_bg = enter_bg
        self.__bg = self.cget("bg")
        self.bind('<Enter>', self.__enter)
        self.bind('<Leave>', self.__leave)
        self.bind('<Button-1>', self.__swap_color)

    def config_img(self, img_path):
        img = ImageTk.PhotoImage(file=img_path)
        self.image = img
        self.config(image=img)

    def __enter(self, _):
        super().config(bg=self.__enter_bg, cursor='hand2')
        self.__focus = True

    def __leave(self, _):
        super().config(bg=self.__bg)
        self.__focus = False

    def __swap_color(self, _):
        temp = self.__bg
        self.__bg = self.__enter_bg
        self.__enter_bg = temp
        super().config(bg=self.__enter_bg, cursor='hand2')

    def config(self, *args, **kwargs):
        if "command" in kwargs:
            self.bind("<ButtonRelease-1>", self.click_handle(kwargs["command"]))
            kwargs.pop("command")
        if "enter_bg" in kwargs:
            self.__enter_bg = kwargs["enter_bg"]
            kwargs.pop("enter_bg")
        if "bg" in kwargs:
            self.__bg = kwargs["bg"]
        super().config(*args, **kwargs)

    def click_handle(self, func):
        def inner(event, *args, **kwargs):
            self.__swap_color(0)
            if self.__focus:
                func(event, *args, **kwargs)
        return inner
    

class CharacterButton(tk.Label):
    def __init__(
            self, 
            parent, 
            fg: str = "#3B3B3B",
            enter_fg: str = "#000000", 
            click_fg: str = "#25C253", 
            *args, 
            **kwargs
        ):
        super().__init__(parent, *args, **kwargs)
        self.__fg = fg
        self.__enter_fg = enter_fg
        self.__click_fg = click_fg
        self.__command = None
        self.config(fg=self.__fg)
        if self.__fg == self.__enter_fg:
            raise ValueError("enter_fg must be different from fg")
        self._bind_event()

    def _bind_event(self):
        self.bind("<Enter>", lambda _: self.config(fg=self.__enter_fg, cursor="hand2"))
        self.bind("<Leave>", lambda _: self.config(fg=self.__fg, cursor=""))
        self.bind("<Button-1>", lambda _: self.config(fg=self.__click_fg))
        self.bind("<ButtonRelease-1>", self.__call)

    def __call(self, event):
        try:
            if self.cget("fg") in (self.__enter_fg, self.__click_fg):
                self.__command()
            self.config(fg=self.__fg)
        except tk.TclError:
            pass

    def config(self, *args, **kwargs):
        for attr in kwargs.copy():
            if attr in ("enter_fg", "click_fg", "command"):
                setattr(self, f"_{self.__class__.__name__}__{attr}", kwargs[attr])
                kwargs.pop(attr)
        super().config(*args, **kwargs)



if __name__ == "__main__":
    def click(event):
        print("click me!")
    root = tk.Tk()
    root.geometry("320x100+500+300")
    flat_btn = FlatButton(root, text="十 新建", fg="white", font=("微软雅黑", 13))
    flat_btn.config(command=click, bg="#1E5FC7", enter_bg="#1F69E0")
    flat_btn.place(x=40, y=30, width=230, height=30)
    root.mainloop()
