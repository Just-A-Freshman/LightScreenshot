import tkinter as tk


class CustomEntry(tk.Entry):
    frame_style = {
        "borderwidth": 1,
        "highlightthickness": 1,
        "relief": "flat"
    }

    def __init__(self, master, highlight_color="#007FD4", start_pos=0, **kwargs):
        self.__start_pos = start_pos
        self.base_frame = tk.Frame(master, **CustomEntry.frame_style)
        super().__init__(self.base_frame, relief="flat", **kwargs)
        bg = self.cget("bg")
        self.base_frame.config(bg=bg, highlightbackground=bg)
        self.bind("<FocusIn>", self.base_frame.config(highlightcolor=highlight_color))

    def place(self, x, y, width, height, **kwargs):
        self.base_frame.place(x=x, y=y, width=width, height=height)
        super().place(x=self.__start_pos-1, y=-1, width=width-self.__start_pos-2, height=height-2, **kwargs)

    def config(self, *args, **kwargs):
        if "bg" in kwargs:
            bg = kwargs["bg"]
            self.base_frame.config(bg=bg, highlightbackground=bg)
        super().config(*args, **kwargs)


class ReadOnlyEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config(relief="flat", state="readonly")
        self.bind("<Enter>", self.set_enter_mouse_state)

    def refresh(self, content: str):
        self.config(state="normal")
        self.delete(0, "end")
        self.insert(0, content)
        self.config(state="readonly")

    def set_enter_mouse_state(self, _):
        content = self.get()
        if len(content) == 0:
            self.config(cursor="arrow")
        else:
            self.config(cursor="ibeam")


if __name__ == "__main__":
    import tkinter as tk

    style_dict = dict()

    style_dict["Entry-1"] = {
        "bg": "#666666",
        "highlightbackground": "#7A7A7A",
        "foreground": "#E8E8E8",
        "insertbackground": "#E8E8E8"
    }
    root = tk.Tk()
    root.config(bg="red")
    root.geometry("100x100+100+100")
    entry = CustomEntry(root, start_pos=10, **style_dict["Entry-1"])
    entry.place(x=0, y=0, width=100, height=30)
    root.mainloop()
