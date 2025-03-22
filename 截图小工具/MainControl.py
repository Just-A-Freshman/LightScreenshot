from threading import Thread
from weakref import WeakMethod
from typing import Literal
from pathlib import Path
from tkinter import filedialog, ttk, messagebox
from subprocess import Popen
from typing import Literal

import tkinter as tk
import os
import gc

from Setting import Window, File, Env, Shortcuts
from Utils import OCRUtils, ImageUtils
from MainUI import MainUI, SettingUI, CharacterButton, Tray, NailImageCanvas

from PIL import Image
import keyboard



class ScreenshotTool(MainUI):
    def __init__(self):
        super().__init__()
        self.env = Env()
        self.ocr_utils = OCRUtils(self.env)
        self.tray = Tray(self)
        Thread(target=self.tray.run, daemon=True).start()
        self.after(100, self._add_command)
        self.after(150, self._bind_event)
        self.after(200, self._add_keyboard_event)

    def _add_command(self):
        self.cut_btn.config(command=self.start_capture)
        self.edit_in_file_btn.config(command=self.edit_image)
        self.load_image_btn.config(command=self.load_image)
        self.nail_btn.config(command=lambda: self.nail_image_to_desktop(self.screenshot.final_images[self.screenshot.page_index]))
        self.setting_btn.config(command=self.show_setting)
        
    def _bind_event(self):
        self.bind("<Left>", lambda _: self.turn_page("left"))
        self.bind("<Left>", lambda _: self.turn_page("left"))
        self.bind("<Right>", lambda _: self.turn_page("right"))
        self.protocol("WM_DELETE_WINDOW", self.exit)

    def _add_keyboard_event(self):
        self._add_shortcuts(0)
        self._add_shortcuts(1)

    def _add_shortcuts(self, id: int):
        try:
            shortcuts = [self.env.capture_shortcuts, self.env.call_shortcuts, self.env.exit_shortcuts]
            events = [self.start_capture, self.toggle_ui, self.confirm_capture]
            self.env.shortcuts_id[id] = keyboard.add_hotkey("+".join(shortcuts[id]), events[id])
        except ValueError:
            return

    def _bind_screenshot_canvas(self):
        self.capture_win.focus_set()
        self.capture_win.bind("<Shift_L>", lambda _: self.screenshot_tip.toggle_rgb_state())
        self.capture_win.bind("<Shift_R>", lambda _: self.screenshot_tip.toggle_rgb_state())
        self.capture_win.bind("<space>", lambda _: self.get_current_color())
        self.capture_win.bind("<Button-1>", self.on_press)
        self.capture_win.bind("<Motion>", lambda _: self.update_screenshot_area())
        self.capture_win.bind("<ButtonRelease-1>", self.on_release)
        self.capture_win.bind("<B1-Motion>", self.on_drag)
        self.capture_win.bind("<Up>", lambda _: self.fine_tuning_coords("up"))
        self.capture_win.bind("<Down>", lambda _: self.fine_tuning_coords("down"))
        self.capture_win.bind("<Left>", lambda _: self.fine_tuning_coords("left"))
        self.capture_win.bind("<Right>", lambda _: self.fine_tuning_coords("right"))

    def _unbind_all(self):
        events = (
            "<Button-1>", "<Motion>", "<ButtonRelease-1>", "<B1-Motion>",
            "<Shift_L>", "<Shift_R>", "<Up>", "<Down>", "<Left>", "<Right>", "<space>"
        )
        for event in events:
            self.full_screenshot_canvas.unbind(event)

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
        commands = [
            self.clear_capture_info, self.confirm_capture, 
            self.get_ocr_result, self.nail_image_to_desktop
        ]
        self.after(100, self.edit_bar._bind_command, commands)
        self.screenshot.initialize_coords()
        self.update_screenshot_area()
        self._bind_screenshot_canvas()
        
    def start_capture(self):
        keyboard.remove_hotkey(self.env.shortcuts_id[0])
        keyboard.remove_hotkey(self.env.shortcuts_id[1])
        self._add_shortcuts(2)
        self.attributes('-alpha', 0)
        self.after(0, self._start_capture)

    def on_press(self, event) -> None:
        self.full_screenshot_canvas.on_press()
        self.adjust_rect.on_press(event)

    def on_drag(self, event) -> None:
        self.adjust_rect.rect_adjust(event)
        self.update_screenshot_area()

    def on_release(self, event, resize=True) -> None:
        underupdated = self.screenshot.coords_underupdated
        if underupdated:
            self.screenshot.get_default_screenshot_coords()
            self.adjust_rect.update_rect()
        self._unbind_all()
        self.adjust_rect.on_release(event)
        self.capture_win.bind("<B1-Motion>", self.rect_adjust)
        self.capture_win.bind("<ButtonRelease-1>", lambda e: self.on_release(e, False))
        self.capture_win.bind("<Button-1>", self.enter_adjust_mode)
        self.capture_win.bind("<Motion>", self.adjust_rect.on_hover)
        self.edit_bar.toggle_edit_bar(conceal=False)
        if resize and not underupdated:
            self.screenshot.end_x, self.screenshot.end_y = event.x_root, event.y_root
        self.magnifer.toggle_magnifier(conceal=True)
        self.screenshot_tip.toggle_pointer_tip(conceal=True)
        self.screenshot_tip.delete_shelter_item()
        self.screenshot_tip.update_rect_size_tip()

    def rect_adjust(self, event) -> None:
        self.adjust_rect.rect_adjust(event)
        if self.adjust_rect.anchor_id != 8 and self.adjust_rect.anchor_id != -1:
            self.update_screenshot_area()

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
        self.adjust_rect.update_rect()
        self.screenshot_tip.update_rect_size_tip()
        self.edit_bar.toggle_edit_bar(conceal=False)

    def update_screenshot_area(self) -> None:
        x, y = self.capture_win.winfo_pointerxy()
        self.magnifer.update_magnifier(x, y)
        self.screenshot_tip.update_pointer_tip(x, y)
        self.screenshot_tip.update_rect_size_tip()

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
        self.screenshot.initialize_temp_variables()
        self.capture_win = None
        self.full_screenshot_canvas = None
        self.adjust_rect = None
        self.magnifer = None
        self.screenshot_tip = None
        self.edit_bar = None
        gc.collect()
        self.attributes('-alpha', 1)
        self._add_keyboard_event()

    def confirm_capture(self) -> None:
        x1, y1, x2, y2 = self.adjust_rect.rect_coords()
        if x2 - x1 == 0 or y2 - y1 == 0:
            return
        image = self.screenshot.current_image.crop((x1, y1, x2, y2))
        self.screenshot.final_images.append(image)
        self.show_image_canvas.show_image(image)
        self.screenshot.page_index = len(self.screenshot.final_images) - 1
        self.auto_operation()
        self.attributes('-topmost', 1)
        keyboard.remove_hotkey(self.env.shortcuts_id[2])
        self.clear_capture_info()

    def load_image(self) -> None:
        image = ImageUtils.load_image()
        if not image:
            return
        self.show_image_canvas.show_image(image)
        self.screenshot.final_images.append(image)
        self.screenshot.page_index = len(self.screenshot.final_images) - 1
        self.auto_operation()

    def edit_image(self) -> None:
        if len(self.screenshot.final_images) == 0:
            return self.bell()
        save_path = self.save_image(no_default=False)
        if self.env.edit_exe_path == "":
            return os.startfile(save_path)
        try:
            Popen([self.env.edit_exe_path, save_path])
        except FileNotFoundError as e:
            messagebox.showerror(
                f"""Cannot open: {self.env.edit_exe_path}, 
                Please check your edit_exe_path in src/settings.json!"""
            )
        except Exception as e:
            messagebox.showerror(e)

    def show_setting(self) -> None:
        keyboard.unhook_all()
        setting_win = SettingControl(self, self.env)
        setting_win.load_setting_to_widget()
        self.after(100, setting_win._bind_command)

    def copy_image(self, image: Image.Image = None) -> None:
        if not image:
            image = self.screenshot.final_images[self.screenshot.page_index]
        self.title("复制成功!")
        self.after(1000, lambda: self.title(Window.window_title))
        Thread(target=ImageUtils.copy_image, args=(image, ), daemon=True).start()

    def save_image(self, no_default=True, image: Image.Image = None) -> Path:
        if not image:
            image: Image.Image = self.screenshot.final_images[self.screenshot.page_index]
        random_suffix = int.from_bytes(os.urandom(4), byteorder='big')
        initialfile = f"{image.width}x{image.height}_{random_suffix}.png"
        if no_default:
            filename = filedialog.asksaveasfilename(
                defaultextension=".png", initialfile=initialfile,
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")],
            )
            if not filename:
                return
            filename = Path(filename)
        else:
            auto_save_dir = Path(self.env.auto_save_path)
            if auto_save_dir.is_dir():
                filename = auto_save_dir / initialfile
            else:
                filename = File.default_save_dir / initialfile
        image.save(filename)
        return filename.resolve()

    def turn_page(self, direction: Literal["left", "right"]) -> None:
        if len(self.screenshot.final_images) == 0:
            return self.bell()
        if direction == "left":
            if self.screenshot.page_index == 0:
                return self.bell()
            self.screenshot.page_index -= 1
        else:
            if self.screenshot.page_index == len(self.screenshot.final_images) - 1:
                return self.bell()
            self.screenshot.page_index += 1
        self.show_image_canvas.show_image(self.screenshot.final_images[self.screenshot.page_index])

    def delete_image(self) -> None:
        if len(self.screenshot.final_images) == 0:
            return self.bell()
        self.screenshot.final_images.pop(self.screenshot.page_index)
        if self.screenshot.page_index == len(self.screenshot.final_images):
            self.screenshot.page_index -= 1
        if len(self.screenshot.final_images) == 0:
            self.show_image_canvas.destroy()
            self.geometry(f"{Window.window_width}x{Window.window_height}")
        else:
            self.show_image_canvas.show_image(self.screenshot.final_images[self.screenshot.page_index])

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
            self.save_image(False)
        if self.env.auto_delete and len(self.screenshot.final_images) > self.env.auto_delete_upper:
            self.screenshot.final_images.pop(0)
            self.screenshot.page_index -= 1

    def get_ocr_result(self):
        image = self.screenshot.current_image.crop(self.adjust_rect.rect_coords())
        self.ocr_utils.get_ocr_result(image)

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
            return
        self.deiconify()

    def exit(self):
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
            self.exit_shortcut_entry: "exit_shortcuts"
        }

    def _bind_command(self):
        weak_callback = WeakMethod(self.__on_mouse_wheel)
        entries = [self.capture_shortcuts_entry, self.call_shortcuts_entry, self.exit_shortcut_entry]
        restore_btns = [self.capture_entry_restore_btn, self.call_entry_restore_btn, self.exit_entry_restore_btn]
        for entry, restore_btn in zip(entries, restore_btns):
            entry.bind("<Key>", self.edit_entry)
            restore_btn.config(command=lambda entry=entry: self.restore_default_shortcuts(entry)) 
        self.basic_canvas.bind("<Configure>", self.update_window_size)
        self.master.bind("<MouseWheel>", lambda e: weak_callback() and weak_callback()(e))
        self.back_btn.config(command=self.save_setting)
        self.browse_auto_save_path_btn.config(command=self.browse_auto_save_path)
        self.open_auto_save_path_btn.config(command=self.open_auto_save_path)

    def restore_default_shortcuts(self, entry: ttk.Entry):
        default_content = self.env.get_default_info(self.default_settings[entry])
        shortcuts = " + ".join(default_content)
        self.insert_into_entry(entry, shortcuts)

    def update_window_size(self, event):
        new_width = event.width
        self.basic_canvas.itemconfig(self.window_id, width=new_width)

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
        self.basic_canvas.itemconfig(self.window_id, width=self.master.winfo_width() - 40)
        self.insert_into_entry(self.capture_shortcuts_entry, " + ".join(self.env.capture_shortcuts))
        self.insert_into_entry(self.call_shortcuts_entry, " + ".join(self.env.call_shortcuts))
        self.insert_into_entry(self.exit_shortcut_entry, " + ".join(self.env.exit_shortcuts))
        self.insert_into_entry(self.auto_save_path_entry, self.env.auto_save_path)
        self.auto_delete_spinbox.insert(0, self.env.auto_delete_upper)
        self.auto_save_switch.toggle(self.env.auto_save, animation=False)
        self.auto_copy_switch.toggle(self.env.auto_copy, animation=False)
        self.auto_delete_switch.toggle(self.env.auto_delete, animation=False)

    def _save_setting(self):
        self.env.capture_shortcuts = self.capture_shortcuts_entry.get().split(" + ")
        self.env.call_shortcuts = self.call_shortcuts_entry.get().split(" + ")
        self.env.exit_shortcuts = self.exit_shortcut_entry.get().split(" + ")
        self.env.auto_copy = self.auto_copy_switch.state
        self.env.auto_save = self.auto_save_switch.state
        self.env.auto_save_path = self.auto_save_path_entry.get()
        self.env.auto_delete = self.auto_delete_switch.state
        self.env.auto_delete_upper = int(self.auto_delete_spinbox.get())
        Shortcuts.clear(self.env.capture_shortcuts)
        Shortcuts.clear(self.env.call_shortcuts)
        Shortcuts.clear(self.env.exit_shortcuts)
        self.master.unbind("<MouseWheel>")
        self.capture_shortcuts_entry.unbind("<Key>")
        self.call_shortcuts_entry.unbind("<Key>")
        self.exit_shortcut_entry.unbind("<Key>")
        keyboard.unhook_all()
        self.env.save_to_file()
        self.master._add_keyboard_event()
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

    def open_auto_save_path(self):
        path_str: str = self.auto_save_path_entry.get()
        path = Path(path_str) if path_str else Path.cwd()
        if path.is_dir():
            os.startfile(path)

    def destroy(self) -> None:
        self.basic_frame.destroy()
        for attr_name in self.__dict__:
            setattr(self, attr_name, None)
