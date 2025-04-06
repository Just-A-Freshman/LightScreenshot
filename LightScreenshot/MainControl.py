from threading import Thread
from weakref import WeakMethod
from typing import Literal
from pathlib import Path
from tkinter import filedialog, ttk
from subprocess import Popen
from typing import Literal

import tkinter as tk

from Utils import *
from Setting import Window, File, Env, Shortcuts, State
from MainUI import MainUI, SettingUI, CharacterButton, Tray, NailImageCanvas

from PIL import Image


class ScreenshotTool(MainUI):
    def __init__(self):
        super().__init__()
        self.env = Env()
        self.ocr_utils = OCRUtils(self.env)
        self.tray = Tray(self)
        if self.env.auto_conceal:
            self.withdraw()
        Thread(target=self.tray.run, daemon=True).start()
        self.after(100, self._add_command)
        self.after(150, self._add_shortcuts)
        self.load_from_history()

    def load_from_history(self):
        HistoryRecord.load_from_dir()
        HistoryRecord.turn_last_page()
        if not HistoryRecord.empty():
            self.show_image_canvas.show_image(HistoryRecord.current_image())

    def _add_command(self):
        self.cut_btn.config(command=self.start_capture)
        self.edit_in_file_btn.config(command=self.edit_image)
        self.load_image_btn.config(command=self.load_image)
        self.nail_btn.config(command=lambda: self.nail_image_to_desktop(self.show_image_canvas.current_show_image()))
        self.setting_btn.config(command=self.show_setting)
        
    def _add_shortcuts(self):
        # 窗口级的快捷键
        self.bind("<Left>", lambda _: self.turn_page(is_left=True))
        self.bind("<Right>", lambda _: self.turn_page(is_left=False))
        self.bind("<Control-s>", lambda _: self.save_image())
        self.bind("<Control-c>", lambda _: self.copy_image())
        self.bind("<Delete>", lambda _: self.delete_image())
        self.protocol("WM_DELETE_WINDOW", self.exit)
        # 全局快键键
        ShortcutsUtils.add_shortcuts(["shift"], self.toggle_rgb_state, lambda: State.is_capturing)
        ShortcutsUtils.add_shortcuts(["space"], self.get_current_color, lambda: State.is_capturing)
        ShortcutsUtils.add_shortcuts(["alt"], self.force_toggle_magnifier, lambda: State.is_capturing)
        # 用户控制的全局快键键选项
        ShortcutsUtils.add_shortcuts(self.env.capture_shortcuts, self.start_capture, lambda: not State.is_capturing)
        ShortcutsUtils.add_shortcuts(self.env.call_shortcuts, self.toggle_ui, lambda: not State.is_capturing)
        ShortcutsUtils.add_shortcuts(
            self.env.nail_shortcuts, self.nail_image_to_desktop, 
            lambda: State.is_capturing and State.is_resizing
        )

    def _bind_screenshot_canvas(self):
        self.capture_win.bind("<Button-1>", self.on_press)
        self.capture_win.bind("<Motion>", self.on_motion)
        self.capture_win.bind("<B1-Motion>", self.on_drag)
        self.capture_win.bind("<ButtonRelease-1>", self.on_release)
        self.capture_win.bind("<Up>", lambda _: self.fine_tuning_coords("up"))
        self.capture_win.bind("<Down>", lambda _: self.fine_tuning_coords("down"))
        self.capture_win.bind("<Left>", lambda _: self.fine_tuning_coords("left"))
        self.capture_win.bind("<Right>", lambda _: self.fine_tuning_coords("right"))
        self.capture_win.bind("<Double-Button-1>", lambda _: self.fast_save())

    def _start_capture(self):
        self.capture_win = tk.Toplevel()
        self.capture_win.attributes("-topmost", True)
        self.capture_win.geometry(f"{Window.screen_width}x{Window.screen_height}+0+0")
        self.capture_win.overrideredirect(True)
        self.full_screenshot_canvas = self.set_screenshot_canvas(self.capture_win)
        self.full_screenshot_canvas.make_screenshot()
        self.adjust_rect = self.set_adjust_rect(self.full_screenshot_canvas)
        self.magnifer = self.set_magnifier(self.full_screenshot_canvas)
        self.screenshot_tip = self.set_screenshot_tip(self.full_screenshot_canvas)
        self.edit_bar = self.set_edit_bar(self.full_screenshot_canvas)
        State.is_capturing = True
        commands = [
            self.clear_capture_info, self.confirm_capture,   
            self.get_ocr_result, self.nail_image_to_desktop
        ]
        self.after(100, self.edit_bar._bind_command, commands)
        self.screenshot.initialize_coords()
        self.update_screenshot_area()
        self._bind_screenshot_canvas()
        
    def start_capture(self):
        self.attributes('-alpha', 0)
        self.after(0, self._start_capture)

    def on_press(self, event) -> None:
        if State.is_resizing:
            self.enter_adjust_mode(event)
        else:
            self.full_screenshot_canvas.on_press()
            self.adjust_rect.on_press(event)

    def on_motion(self, event) -> None:
        if State.is_resizing:
            self.adjust_rect.on_motion(event)
            if not State.force_show_magnifier:
                return
        self.update_screenshot_area()

    def on_drag(self, event) -> None:
        State.is_resizing = True
        self.adjust_rect.on_drag(event)
        if self.adjust_rect.anchor_id != 8 and self.adjust_rect.anchor_id != -1:
            self.update_screenshot_area()

    def on_release(self, event) -> None:
        if not State.is_resizing:
            self.screenshot.get_default_screenshot_coords()
            State.is_resizing = True
            self.adjust_rect.resize_rect()
        self.adjust_rect.on_release()
        self.edit_bar.toggle_edit_bar(conceal=False)
        self.magnifer.toggle_magnifier(conceal=True)
        self.screenshot_tip.toggle_pointer_tip(conceal=True)
        self.screenshot_tip.update_rect_size_tip()
        RedrawUtils.redraw()

    def fine_tuning_coords(self, direction: Literal["up", "down", "left", "right"]) -> None:
        if direction == "up":
            if self.screenshot.start_y - 1 < 0:
                return
            self.screenshot.start_y -= 1
            self.screenshot.end_y -= 1
        elif direction == "down":
            if self.screenshot.end_y + 1 > Window.screen_height:
                return
            self.screenshot.start_y += 1
            self.screenshot.end_y += 1
        elif direction == "left":
            if self.screenshot.start_x - 1 < 0:
                return
            self.screenshot.start_x -= 1
            self.screenshot.end_x -= 1
        else:
            if self.screenshot.end_x + 1 > Window.screen_width:
                return
            self.screenshot.start_x += 1
            self.screenshot.end_x += 1
        self.adjust_rect.resize_rect()
        self.screenshot_tip.update_rect_size_tip()
        self.edit_bar.toggle_edit_bar(conceal=False)

    def force_toggle_magnifier(self):
        new_state = not State.force_show_magnifier
        State.force_show_magnifier = new_state
        self.magnifer.toggle_magnifier(conceal=new_state)
        self.screenshot_tip.toggle_pointer_tip(conceal=new_state)
        RedrawUtils.redraw()

    def toggle_rgb_state(self):
        if self.screenshot_tip is None:
            return
        self.screenshot_tip.toggle_rgb_state()

    def update_screenshot_area(self) -> None:
        x, y = self.capture_win.winfo_pointerxy()
        self.magnifer.update_magnifier(x, y)
        self.screenshot_tip.update_pointer_tip(x, y)
        self.screenshot_tip.update_rect_size_tip()
        RedrawUtils.redraw()

    def enter_adjust_mode(self, event) -> None:
        self.screenshot.move_start_x = event.x_root
        self.screenshot.move_start_y = event.y_root
        self.screenshot_tip.toggle_pointer_tip(conceal=True)
        self.screenshot_tip.toggle_rect_size_tip(conceal=True)
        pointer_widget = self.winfo_containing(event.x_root, event.y_root)
        if isinstance(pointer_widget, CharacterButton):
            return
        self.edit_bar.toggle_edit_bar(conceal=True)
        
    def clear_capture_info(self) -> None:
        self.capture_win.destroy()
        self.capture_win = None
        self.full_screenshot_canvas = None
        self.adjust_rect = None
        self.magnifer = None
        self.screenshot_tip = None
        self.edit_bar = None
        State.restore_default()
        RedrawUtils.destroy_redraw_info()
        self.screenshot.initialize_temp_variables()
        self.attributes('-alpha', 1)

    def confirm_capture(self) -> None:
        x1, y1, x2, y2 = self.adjust_rect.rect_coords()
        if x2 - x1 < 2 or y2 - y1 < 2:
            return
        image = self.screenshot.current_image.crop((x1, y1, x2, y2))
        HistoryRecord.append(image)
        HistoryRecord.turn_last_page()
        self.show_image_canvas.show_image(image)
        self.auto_operation()
        self.attributes('-topmost', 1)
        self.clear_capture_info()

    def load_image(self) -> None:
        image = ImageUtils.load_image()
        if not image:
            return
        HistoryRecord.append(image)
        HistoryRecord.turn_last_page()
        self.show_image_canvas.show_image(image)
        self.auto_operation()

    def edit_image(self) -> None:
        if HistoryRecord.empty():
            return self.bell()
        image_path: Path = HistoryRecord.current_image_path()
        if not image_path.exists():
            self.show_image_canvas.current_show_image().save(image_path)
        if not Path(self.env.edit_exe_path).exists():
            FileUtils.open_file_path(image_path)
        else:
            Popen([self.env.edit_exe_path, image_path])

    def show_setting(self) -> None:
        setting_win = SettingControl(self, self.env)
        setting_win.load_setting_to_widget()
        self.after(100, setting_win._bind_command)

    def copy_image(self, image: Image.Image = None) -> None:
        if not image:
            image = HistoryRecord.current_image()
        self.title("复制成功!")
        self.after(1000, lambda: self.title(Window.window_title))
        Thread(target=ImageUtils.copy_image, args=(image, ), daemon=True).start()

    def save_image(self, save_window=True, image: Image.Image = None) -> Path | None:
        if not image:
            image = HistoryRecord.current_image()
            if image is None:
                return None
        initialfile = ImageUtils.get_random_image_name(image)
        if save_window:
            filename = ImageUtils.ask_save_image(initialfile)
            if not filename:
                return None
            filename = Path(filename)
        else:
            auto_save_dir = Path(self.env.auto_save_path)
            auto_save_dir = auto_save_dir if auto_save_dir.is_dir() else File.default_save_dir
            filename = auto_save_dir / initialfile
        image.save(filename)
        return filename.resolve()
    
    def fast_save(self) -> None:
        if State.is_saving:
            WindowUtils.SetWindowToTop("另存为")
            return
        image = self.screenshot.current_image.crop(self.adjust_rect.rect_coords())
        path = self.save_image(save_window=True, image=image)
        if path:
            self.clear_capture_info()

    def turn_page(self, is_left: bool) -> None:
        if not HistoryRecord.turn_page(is_left):
            return self.bell()
        self.show_image_canvas.show_image(HistoryRecord.current_image())

    def delete_image(self) -> None:
        if not HistoryRecord.remove_current_image():
            return
        if HistoryRecord.empty():
            self.show_image_canvas.destroy()
            self.geometry(f"{Window.window_width}x{Window.window_height}")
        else:
            self.show_image_canvas.show_image(HistoryRecord.current_image())

    def nail_image_to_desktop(self, image: Image.Image = None) -> None:
        if not image:
            image = self.screenshot.current_image.crop(self.adjust_rect.rect_coords())
            x, y = self.adjust_rect.rect_coords()[:2]
            self.confirm_capture()
        else:
            x, y = (Window.screen_width - image.width) // 2, (Window.screen_height - image.height) // 2
        nail_canvas = NailImageCanvas(image)
        if nail_canvas is not None:
            nail_canvas.set_nail_canvas(x, y)

    def auto_operation(self):
        if self.env.auto_copy:
            self.copy_image()
        if self.env.auto_save:
            self.save_image(save_window=False)

    def get_ocr_result(self):
        self.ocr_utils.get_ocr_result(self.screenshot.current_image.crop(self.adjust_rect.rect_coords()))

    def get_current_color(self):
        color = self.screenshot_tip.current_color()
        ImageUtils.copy_rgb_color(color)
        self.clear_capture_info()

    def clear_snail_image(self):
        for child in self.winfo_children():
            if isinstance(child, NailImageCanvas):
                child.call("kill")

    def toggle_ui(self):
        if self.state() != "withdrawn":
            self.attributes('-alpha', 1)
            self.withdraw()
        else:
            self.deiconify()

    def exit(self):
        if self.env.auto_clear:
            Thread(target=FileUtils.remove_files, args=(File.history_dir, )).start()
        self.tray.stop()
        self.destroy()



class SettingControl(SettingUI):
    def __init__(self, master: ScreenshotTool, env: Env):
        super().__init__(master)
        self.master: ScreenshotTool = master
        self.env: Env = env
        self.default_settings = {
            self.capture_shortcuts_entry: "capture_shortcuts",
            self.call_shortcuts_entry: "call_shortcuts",
            self.exit_shortcuts_entry: "exit_shortcuts"
        }

    def _bind_command(self):
        weak_callback = WeakMethod(self.__on_mouse_wheel)
        entries = [self.capture_shortcuts_entry, self.call_shortcuts_entry, self.exit_shortcuts_entry]
        restore_btns = [self.capture_entry_restore_btn, self.call_entry_restore_btn, self.exit_entry_restore_btn]
        for entry, restore_btn in zip(entries, restore_btns):
            entry.bind("<Key>", self.edit_entry)
            restore_btn.config(command=lambda entry=entry: self.restore_default_shortcuts(entry)) 
        self.basic_canvas.bind("<Configure>", self.update_window_size)
        self.master.bind("<MouseWheel>", lambda e: weak_callback() and weak_callback()(e))
        self.back_btn.config(command=self.save_setting)
        self.browse_auto_save_path_btn.config(command=self.browse_auto_save_path)
        self.open_auto_save_path_btn.config(command=lambda: FileUtils.open_file_path(self.auto_save_path_entry.get()))
        self.open_help_btn.config(command=lambda: FileUtils.open_file_path(File.help_file))
        self.open_config_file_btn.config(command=lambda: FileUtils.open_file_path(File.setting_config))
        self.open_style_file_btn.config(command=lambda: FileUtils.open_file_path(File.style_config))

    def restore_default_shortcuts(self, entry: ttk.Entry):
        default_content = self.env.get_default_info(self.default_settings[entry])
        shortcuts = " + ".join(default_content)
        self.insert_into_entry(entry, shortcuts)

    def update_window_size(self, event):
        new_width = event.width
        self.basic_canvas.itemconfig("content_frame", width=new_width)

    def __on_mouse_wheel(self, event):
        canvas_height = self.basic_canvas.winfo_height()
        bbox = self.basic_canvas.bbox("all")
        if not bbox:
            return
        frame_height = bbox[3] - bbox[1]
        if canvas_height > frame_height:
            return "break"
        self.basic_canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def insert_into_entry(self, entry: ttk.Entry, text: str = "") -> None:
        entry.delete(0, tk.END)
        entry.insert(0, text)
        entry.xview_moveto(1.0)

    def load_setting_to_widget(self):
        self.basic_canvas.itemconfig("content_frame", width=self.master.winfo_width() - 40)
        self.insert_into_entry(self.capture_shortcuts_entry, " + ".join(self.env.capture_shortcuts))
        self.insert_into_entry(self.call_shortcuts_entry, " + ".join(self.env.call_shortcuts))
        self.insert_into_entry(self.exit_shortcuts_entry, " + ".join(self.env.nail_shortcuts))
        self.insert_into_entry(self.auto_save_path_entry, self.env.auto_save_path)
        self.auto_save_switch.toggle(self.env.auto_save, animation=False)
        self.auto_copy_switch.toggle(self.env.auto_copy, animation=False)
        self.auto_conceal_switch.toggle(self.env.auto_conceal, animation=False)
        self.auto_clear_switch.toggle(self.env.auto_clear, animation=False)

    def _save_setting(self):
        self.env.capture_shortcuts = self.capture_shortcuts_entry.get().split(" + ")
        self.env.call_shortcuts = self.call_shortcuts_entry.get().split(" + ")
        self.env.nail_shortcuts = self.exit_shortcuts_entry.get().split(" + ")
        self.env.auto_save_path = self.auto_save_path_entry.get()
        self.env.auto_copy = self.auto_copy_switch.state
        self.env.auto_save = self.auto_save_switch.state
        self.env.auto_conceal = self.auto_conceal_switch.state
        self.env.auto_clear = self.auto_clear_switch.state
        Shortcuts.clear(self.env.capture_shortcuts)
        Shortcuts.clear(self.env.call_shortcuts)
        Shortcuts.clear(self.env.nail_shortcuts)
        self.master.unbind("<MouseWheel>")
        self.capture_shortcuts_entry.unbind("<Key>")
        self.call_shortcuts_entry.unbind("<Key>")
        self.exit_shortcuts_entry.unbind("<Key>")
        self.env.save_to_file()
        self.destroy()

    def save_setting(self):
        style = ttk.Style()
        style.theme_use("classic")
        w, h, _, _ = self.orig_geometry
        x, y = self.parent.winfo_x(), self.parent.winfo_y()
        self.parent.geometry(f"{w}x{h}+{x}+{y}")
        self.basic_frame.place_forget()
        self.parent.after(100, self._save_setting)

    def edit_entry(self, event):
        entry: ttk.Entry = event.widget
        tmp_shortcuts: list = entry.get().split(" + ")
        key = Shortcuts.key_tranform.get(event.keysym, event.keysym)
        if key == "??":
            return
        if len(key) == 1:
            key = key.upper()
        elif key == "BackSpace" and len(tmp_shortcuts) > 0:
            tmp_shortcuts.pop()
        if key in Shortcuts.valid_shortcuts and key not in tmp_shortcuts:
            if len(tmp_shortcuts) == 3:
                tmp_shortcuts.pop()
            tmp_shortcuts.append(key)
        self.insert_into_entry(entry, " + ".join(tmp_shortcuts))
        return "break"

    def browse_auto_save_path(self):
        path = filedialog.askdirectory()
        if not path:
            return
        self.insert_into_entry(self.auto_save_path_entry, path)

    def destroy(self) -> None:
        self.basic_frame.destroy()
        for attr_name in self.__dict__:
            setattr(self, attr_name, None)
