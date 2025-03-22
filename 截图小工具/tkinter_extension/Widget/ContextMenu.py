from ..Command.FileCommand import FileOperation
from typing import Literal
import tkinter as tk
from os import path


class FileMenu(object):
    __instance = None
    root_path = path.join(path.dirname(path.dirname(__file__)), "resources", "ContextMenu")

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, *args, **kwargs):
        cls = FileMenu
        self.args = args
        self.kwargs = kwargs
        self.copy_ico = tk.PhotoImage(file=path.join(cls.root_path, "copy.png"))
        self.open_ico = tk.PhotoImage(file=path.join(cls.root_path, "open.png"))
        self.copy_path_ico = tk.PhotoImage(file=path.join(cls.root_path, "copy_path.png"))
        self.remove_ico = tk.PhotoImage(file=path.join(cls.root_path, "delete.png"))

    def create_menu(self, event, file_path: str = "", state: Literal["active", "disabled"] = "active"):
        menu = tk.Menu(tearoff=0, *self.args, **self.kwargs)
        labels = ("打开文件", "复制文件", "复制路径", "删除文件")
        ico_cites = (self.open_ico, self.copy_ico, self.copy_path_ico, self.remove_ico)
        commands = (
            lambda: FileOperation.start_file(file_path),
            lambda: FileOperation.copy_file(file_path),
            lambda: FileOperation.copy_file_path(file_path),
            lambda: FileOperation.remove_file(file_path)
        )
        for label, command, ico_cite in zip(labels, commands, ico_cites):
            menu.add_command(
                label=label, command=command, image=ico_cite,
                compound='left', state=state
            )
        menu.post(event.x_root, event.y_root)


