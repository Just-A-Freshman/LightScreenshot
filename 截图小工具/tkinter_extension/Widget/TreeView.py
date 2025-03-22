from ..Command.FileCommand import FileJudgement
from os import path, scandir
from PIL import ImageTk
from tkinter import ttk
import tkinter as tk
import re


class FileTreeView(ttk.Treeview):
    _style_map = {
        "background": ("background", "fieldbackground", "lightcolor", "bordercolor"),
        "foreground": "foreground",
        "font": "font",
        "rowheight": "rowheight",
        "relief": "relief"
    }
    root_path = path.join(path.dirname(path.dirname(__file__)), "resources", "TreeView")
    folder_ico = None
    ico_dict = None

    @classmethod
    def load_ico_img(cls):
        cls.folder_ico = ImageTk.PhotoImage(file=path.join(cls.root_path, "folder.png"))
        cls.ico_dict = {
            r".*?\.(jpg|png|jpeg)": ImageTk.PhotoImage(file=path.join(cls.root_path, "image.png")),
            r".*": ImageTk.PhotoImage(file=path.join(cls.root_path, "unknown.png"))
        }

    def __init__(
            self,
            master,
            background: str = "#3B3B3B",
            foreground: str = "#FCFCFC",
            font: tuple[str, int] = ("微软雅黑", 12),
            rowheight=23,
            *args,
            **kwargs
    ):
        super().__init__(master, show="tree", *args, **kwargs)
        self.__style = ttk.Style()
        self.__style.theme_use("clam")
        self.config(relief="flat", background=background, foreground=foreground, font=font, rowheight=rowheight)
        self.__open_nodes = []
        self.column("#0", minwidth=1200, width=1200)
        self.bind("<<TreeviewOpen>>", self.__lazy_load_file)
        self.bind("<<TreeviewClose>>", self.__clear_memory)

    def cget(self, key) -> str:
        return self.__style.lookup("Treeview", key)

    def config(self, **kwargs):
        style_dict = {}
        for prop, value in kwargs.items():
            if prop not in FileTreeView._style_map.keys():
                continue
            style_keys = self._style_map.get(prop)
            if style_keys:
                if isinstance(style_keys, tuple):
                    for style_key in style_keys:
                        style_dict[style_key] = value
                else:
                    style_dict[style_keys] = value
            else:
                style_dict[prop] = value
            self.__style.configure("Treeview", **style_dict)

    def build_catalog_tree(self, base_folder, root=None):
        cls = FileTreeView
        if not root:
            self.delete(*self.get_children())
            root = self.insert("", 0, text=base_folder, open=True, image=cls.folder_ico)
            self.__open_nodes.clear()
            self.__open_nodes.append(root)

        for file in scandir(base_folder):
            if path.isdir(file.path):
                dir_node = self.insert(root, 0, text=file.name, image=cls.folder_ico)
                if not FileJudgement.is_empty_dir(file.path):
                    self.insert(dir_node, 0)
                continue
            for k, v in cls.ico_dict.items():
                if re.match(k, file.name, re.I):
                    self.insert(root, 0, text=file.name, image=v)

    def get_selected_abs_path(self, item):
        parent_id = super().parent(item)
        base_name = self.item(item)["text"]
        dir_name = self.item(parent_id)["text"]
        while dir_name != "":
            base_name = path.join(dir_name, base_name)
            parent_id = super().parent(parent_id)
            dir_name = self.item(parent_id)["text"]
        return base_name

    def __lazy_load_file(self, _):
        item = self.selection()[0]
        self.delete(*self.get_children(item))
        base_name = self.get_selected_abs_path(item)
        self.build_catalog_tree(base_name, item)
        self.__open_nodes.append(item)

    def __clear_memory(self, _):
        item = self.selection()[0]
        self.delete(*self.get_children(item))
        self.insert(item, 0)
        self.__open_nodes.remove(item)

    def search_node(self, key: str):
        results = []
        for open_node in self.__open_nodes:
            try:
                for child in self.get_children(open_node):
                    if re.search(key, self.item(child, "text")):
                        results.append(child)
            except tk.TclError:
                continue

        return results
