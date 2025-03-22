from tkinter import Label


class Progressbar:
    def __init__(
            self,
            parent,
            borderwidth=2,
            bar_bg="orange",
            background="white",
            highlightcolor="black"
    ):
        self.parent = parent
        self.borderwidth = borderwidth
        self.highlight_color = highlightcolor
        self.bar_bg = bar_bg
        self.background = background
        self.__bar = None
        self.__step: float = 1.0
        self.__current_length = 0
        self.__start_x = 0
        self.__start_y = 0
        self.__bar_height = 0

    def place(self, x, y, width, height):
        self.__step = (width - self.borderwidth*2) / 100
        self.__start_x = x + self.borderwidth
        self.__start_y = y + self.borderwidth
        self.__bar_height = height - self.borderwidth * 2
        self.__drawing(x, y, width, height)

    def __drawing(self, x, y, width, height):
        self.border = Label(self.parent, bg=self.highlight_color)
        self.border.place(x=x, y=y, width=width, height=height)  # 进度条外框
        self.inner = Label(self.parent, bg=self.background)
        self.inner.place(
            x=self.__start_x, y=self.__start_y,
            width=width-self.borderwidth*2, height=height-self.borderwidth*2
        )
        self.__bar = Label(self.parent, bg=self.bar_bg)

    def config(self, **kwargs):
        for k, v in kwargs.items():
            match k:
                case 'highlightcolor': self.border.config(bg=v)
                case 'background': self.inner.config(bg=v)
                case 'bar_bg': self.__bar.config(bg=v)
                case _: continue

    def step(self, value):
        width = self.__bar.winfo_width()
        new_width = width + value * self.__step
        if new_width > self.inner.winfo_width():
            self.set(100)
        else:
            self.__bar.place(width=new_width)

    def set(self, value):
        self.__bar.place(
            x=self.__start_x, y=self.__start_y,
            width=value * self.__step, height=self.__bar_height
        )  # 进度条内部
