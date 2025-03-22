import re
import tkinter as tk
from os import path, startfile, scandir
from subprocess import Popen, run, STARTUPINFO, STARTF_USESHOWWINDOW
from send2trash import send2trash
from tkinter import messagebox


class FileJudgement(object):
    @classmethod
    def is_empty_dir(cls, folder_path):
        if not path.isdir(folder_path):
            return True
        try:
            next(scandir(folder_path))
            return False
        except (StopIteration, FileNotFoundError, PermissionError):
            return True


class FileOperation(object):
    @classmethod
    def remove_file(cls, file_path):
        if not path.exists(file_path):
            tk.messagebox.showerror('提示', "原文件名已不存在!")
            return True
        str_dealing = StrDealing(file_path)
        request = messagebox.askokcancel(
            "提示", f"你确定要删除文件:\n{str_dealing.wrap_path(35)}吗?"
        )
        if not request:
            return False
        file_path = file_path.replace('/', '\\')
        send2trash(file_path)
        return True

    @classmethod
    def copy_file(cls, file_path):
        if not path.exists(file_path):
            return
        startupinfo = STARTUPINFO()
        startupinfo.dwFlags |= STARTF_USESHOWWINDOW
        args = ['powershell', f'Get-Item {file_path} | Set-Clipboard']
        Popen(args=args, startupinfo=startupinfo)

    @classmethod
    def copy_file_path(cls, file_path):
        if not path.exists(file_path):
            return
        file_path = path.abspath(file_path)
        startupinfo = STARTUPINFO()
        startupinfo.dwFlags |= STARTF_USESHOWWINDOW
        run(f'echo "{file_path}"| clip', startupinfo=startupinfo, shell=True)

    @classmethod
    def start_file(cls, file_path):
        try:
            startfile(file_path)
        except FileNotFoundError:
            messagebox.showerror("错误", "原文件被修改\n或移动,无法打开!")
        except OSError as e:
            messagebox.showerror("错误", str(e))


class StrDealing(object):
    def __init__(self, format_str):
        self.format_str = format_str

    def wrap_path(self, width):
        if len(self.format_str) < width:
            return self.format_str
        parts = re.split(r"[/\\]", self.format_str)
        parts = [part for part in parts if part]
        lines = []
        line_str = ""
        current_length = 0
        for part in parts:
            if current_length > width:
                lines.append(part)
                continue
            current_length += len(part)
            if current_length < width:
                line_str = f"{line_str}{part}/"
            else:
                lines.append(line_str)
                current_length = 0
                line_str = ""
        if line_str:
            lines.append(line_str)

        return '\n'.join(lines)


if __name__ == "__main__":
    # StrDealing有bug, 暂且不能用, 由于其基本逻辑并不复杂，待会用C++写一下
    text = StrDealing(r"D:\Users\pbl\Desktop\superFolder\GFPGAN3.2\tkinter_extension\resources\test\smack.jpg")
    print(text.wrap_path(5))
