from io import BytesIO
from threading import Thread
from PIL import Image, UnidentifiedImageError
from Setting import *
from Utils import Event, OCRUtils, Text
from MainUI import MainUI, SettingUI, FlatButton
from tkinter import messagebox, filedialog
from tkinter import ttk
from typing import Literal
import tkinter as tk
import keyboard
import win32clipboard
import os
import gc



class ScreenshotTool(MainUI):
    def __init__(self):
        super().__init__()
        self.env = Env()
        self.ocr_utils = OCRUtils(self.screenshot, self.env)
        Thread(target=self.add_command).start()
        Thread(target=self.add_keyboard_event).start()

    def add_command(self):
        self.cut_btn.command = self.start_capture
        self.load_image_btn.command = self.load_image
        self.copy_btn.command = self.copy_image
        self.save_btn.command = self.save_image
        self.turn_left_btn.command = self.turn_page
        self.turn_right_btn.command = self.turn_page
        self.delete_btn.command = self.delete_image
        self.setting_btn.command = lambda _: SettingControl(self, self.env)

    def add_keyboard_event(self):
        self.add_shortcuts(0)
        self.add_shortcuts(1)

    def add_shortcuts(self, id: int):
        try:
            shortcuts = [self.env.capture_shortcuts, self.env.call_shortcuts, self.env.exit_shortcuts]
            events = [self.start_capture, self.call_window, self.confirm_capture]
            self.env.shortcuts_id[id] = keyboard.add_hotkey("+".join(shortcuts[id]), events[id])
        except ValueError:
            return

    def unbind_keyboard_event(self):
        keyboard.unhook_all()
        self.unbind("<MouseWheel>")

    def bind_screenshot_canvas(self):
        self.capture_win.bind("<Button-1>", self.on_press)
        self.capture_win.bind("<Motion>", self.update_screenshot_area)
        self.capture_win.bind("<ButtonRelease-1>", self.on_release)
        self.capture_win.bind("<B1-Motion>", self.on_drag)
        self.capture_win.bind("<Up>", lambda _: self.fine_tuning_coords("up"))
        self.capture_win.bind("<Down>", lambda _: self.fine_tuning_coords("down"))
        self.capture_win.bind("<Left>", lambda _: self.fine_tuning_coords("left"))
        self.capture_win.bind("<Right>", lambda _: self.fine_tuning_coords("right"))

    def unbind_all(self):
        events = ("<Button-1>", "<Motion>", "<ButtonRelease-1>", "<B1-Motion>")
        for event in events:
            self.full_screenshot_canvas.unbind(event)

    def start_capture(self, _=None):
        def __start_capture():
            self.capture_win = tk.Toplevel()
            self.capture_win.attributes("-topmost", True)
            self.capture_win.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+0+0")
            self.capture_win.overrideredirect(True)
            self.full_screenshot_canvas = self.set_screenshot_canvas(self.capture_win)
            self.full_screenshot_canvas.make_screenshot()
            self.adjust_rect = self.set_adjust_rect(self.full_screenshot_canvas)
            self.magnifer = self.set_magnifier(self.full_screenshot_canvas)
            self.screenshot_tip = self.set_screenshot_tip(self.full_screenshot_canvas)
            self.edit_bar = self.set_edit_bar(self.full_screenshot_canvas)
            Thread(
                target=self.edit_bar.bind_command, 
                args=([self.clear_capture_info, self.confirm_capture, self.get_ocr_result], )
            ).start()
            event = Event(*self.capture_win.winfo_pointerxy())
            self.screenshot.initialize_coords()
            self.update_screenshot_area(event)
            self.bind_screenshot_canvas()
        keyboard.remove_hotkey(self.env.shortcuts_id[0])
        keyboard.remove_hotkey(self.env.shortcuts_id[1])
        self.add_shortcuts(2)
        self.attributes('-alpha', 0)
        self.after(0, __start_capture)

    def on_press(self, event) -> None:
        self.full_screenshot_canvas.on_press()
        self.adjust_rect.on_press(event)

    def on_drag(self, event) -> None:
        self.adjust_rect.rect_adjust(event)
        self.update_screenshot_area(event)

    def on_release(self, event, resize=True) -> None:
        underupdated = self.screenshot.coords_underupdated
        if underupdated:
            self.screenshot.get_default_screenshot_coords()
            self.adjust_rect.update_rect()
        self.unbind_all()
        self.adjust_rect.on_release(event)
        self.capture_win.bind("<B1-Motion>", self.rect_adjust)
        self.capture_win.bind("<ButtonRelease-1>", lambda e: self.on_release(e, False))
        self.capture_win.bind("<Button-1>", self.enter_adjust_mode)
        self.capture_win.bind("<Motion>", self.adjust_rect.on_hover)
        self.edit_bar.toggle_edit_bar(conceal=False)
        self.ocr_utils.toggle_ocr_result_text(conceal=False)
        if resize and not underupdated:
            self.screenshot.end_x, self.screenshot.end_y = event.x_root, event.y_root
        self.magnifer.toggle_magnifier(conceal=True)
        self.screenshot_tip.toggle_pointer_tip(conceal=True)
        self.screenshot_tip.delete_shelter_item()
        self.screenshot_tip.update_rect_size_tip(event)

    def rect_adjust(self, event) -> None:
        self.adjust_rect.rect_adjust(event)
        if self.adjust_rect.anchor_id != 8 and self.adjust_rect.anchor_id != -1:
            self.update_screenshot_area(event)
        if self.adjust_rect.anchor_id != -1:
            self.ocr_utils.destroy_ocr_result_text()

    def fine_tuning_coords(self, direction: Literal["up", "down", "left", "right"]) -> None:
        if direction == "up":
            if self.screenshot.start_y - 1 < 0:
                return
            self.screenshot.start_y -= 1
            self.screenshot.end_y -= 1
        elif direction == "down":
            if self.screenshot.end_y + 1 > SCREEN_HEIGHT:
                return
            self.screenshot.start_y += 1
            self.screenshot.end_y += 1
        elif direction == "left":
            if self.screenshot.start_x - 1 < 0:
                return
            self.screenshot.start_x -= 1
            self.screenshot.end_x -= 1
        else:
            if self.screenshot.end_x + 1 > SCREEN_WIDTH:
                return
            self.screenshot.start_x += 1
            self.screenshot.end_x += 1
        self.adjust_rect.update_rect()
        self.screenshot_tip.update_rect_size_tip(0)
        self.edit_bar.toggle_edit_bar(conceal=False)

    def update_screenshot_area(self, event) -> None:
        self.magnifer.update_magnifier(event)
        self.screenshot_tip.update_pointer_tip(event)
        self.screenshot_tip.update_rect_size_tip(event)

    def enter_adjust_mode(self, event) -> None:
        self.screenshot.move_start_x = event.x_root
        self.screenshot.move_start_y = event.y_root
        self.screenshot_tip.toggle_pointer_tip(conceal=True)
        self.screenshot_tip.toggle_rect_size_tip(conceal=True)
        pointer_widget = self.winfo_containing(event.x_root, event.y_root)
        if isinstance(pointer_widget, FlatButton) or isinstance(pointer_widget, Text):
            return
        self.edit_bar.toggle_edit_bar(conceal=True)
        self.ocr_utils.toggle_ocr_result_text(conceal=True)
        
    def clear_capture_info(self, _) -> None:
        self.capture_win.destroy()
        self.screenshot.initialize_temp_variables()
        self.capture_win = None
        self.full_screenshot_canvas = None
        self.adjust_rect = None
        self.magnifer = None
        self.screenshot_tip = None
        self.edit_bar = None
        self.ocr_utils.ocr_result_text = None
        gc.collect()
        self.attributes('-alpha', 1)
        self.add_keyboard_event()
        
    def confirm_capture(self, event=None) -> None:
        x1, y1, x2, y2 = self.adjust_rect.rect_coords()
        if x2 - x1 == 0 or y2 - y1 == 0:
            return
        image = self.screenshot.current_image.crop((x1, y1, x2, y2))
        self.screenshot.final_images.append(image)
        self.show_image_canvas.show_image(image)
        self.screenshot.page_index = len(self.screenshot.final_images) - 1
        self.auto_operation(event)
        self.attributes('-topmost', 1)
        keyboard.remove_hotkey(self.env.shortcuts_id[2])
        self.clear_capture_info(event)

    def load_image(self, event) -> None:
        file_types = (("Image files", "*.jpg *.png *.jpeg"), )
        img_path = filedialog.askopenfilename(filetypes=file_types)
        if not img_path:
            return
        try:
            image: Image.Image = Image.open(img_path)
            if image.width > SCREEN_WIDTH or image.height > SCREEN_HEIGHT:
                image.thumbnail((SCREEN_WIDTH, SCREEN_HEIGHT))
        except UnidentifiedImageError:
            return messagebox.showerror("错误", "无法识别该图片文件!")
        self.show_image_canvas.show_image(image)
        self.screenshot.final_images.append(image)
        self.screenshot.page_index = len(self.screenshot.final_images) - 1
        self.auto_operation(event)

    def copy_image(self, _) -> None:
        def __copy_image():
            image: Image.Image = self.screenshot.final_images[self.screenshot.page_index]
            output = BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            finally:
                win32clipboard.CloseClipboard()

        if len(self.screenshot.final_images) == 0:
            return messagebox.showerror("复制失败", "未检测到截取图像")
        self.title("复制成功!")
        self.after(1000, lambda: self.title("截图工具"))
        Thread(target=__copy_image, daemon=True).start()

    def save_image(self, no_default=True) -> None:
        if len(self.screenshot.final_images) == 0:
            return messagebox.showerror("保存失败", "未检测到截取图像")
        image = self.screenshot.final_images[self.screenshot.page_index]
        random_suffix = int.from_bytes(os.urandom(6), byteorder='big')
        initialfile = f"{image.width}x{image.height}_{random_suffix}.png"
        if no_default:
            filename = filedialog.asksaveasfilename(
                defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")],
                initialfile=initialfile
            )
            if not filename:
                return
        else:
            filename = os.path.join(self.env.auto_save_path, initialfile)
        image.save(filename)

    def turn_page(self, event) -> None:
        if len(self.screenshot.final_images) == 0:
            return messagebox.showinfo("提示", "暂无图片可切换!")
        if event.widget == self.turn_left_btn:
            if self.screenshot.page_index == 0:
                return messagebox.showinfo("提示", "已经是第一张图片!")
            self.screenshot.page_index -= 1
        else:
            if self.screenshot.page_index == len(self.screenshot.final_images) - 1:
                return messagebox.showinfo("提示", "已经是最后一张图片!")
            self.screenshot.page_index += 1
        self.show_image_canvas.show_image(self.screenshot.final_images[self.screenshot.page_index])

    def delete_image(self, _) -> None:
        if len(self.screenshot.final_images) == 0:
            return messagebox.showinfo("提示", "暂无图片可删除!")
        if not messagebox.askokcancel("提示", "确认删除当前图片?"):
            return
        self.screenshot.final_images.pop()
        if self.screenshot.page_index == len(self.screenshot.final_images):
            self.screenshot.page_index -= 1
        if len(self.screenshot.final_images) == 0:
            self.show_image_canvas.destroy()
            self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        else:
            self.show_image_canvas.show_image(self.screenshot.final_images[self.screenshot.page_index])

    def call_window(self):
        if self.state() == "iconic":
            self.attributes('-alpha', 1)
            self.attributes('-topmost', 1)
            self.deiconify()
        else:
            self.iconify()

    def auto_operation(self, event):
        if self.env.auto_copy:
            self.copy_image(event)
        if self.env.auto_save:
            self.save_image(False)
        if self.env.auto_delete and len(self.screenshot.final_images) > self.env.auto_delete_upper:
            self.screenshot.final_images.popleft()
            self.screenshot.page_index -= 1

    def get_ocr_result(self, _):
        image = self.screenshot.current_image.crop(self.adjust_rect.rect_coords())
        self.ocr_utils.get_ocr_result(self.full_screenshot_canvas, image)


class SettingControl(SettingUI):
    def __init__(self, master: ScreenshotTool, env: Env):
        super().__init__(master)
        self.master: ScreenshotTool = master
        self.env: Env = env
        Thread(target=self.bind_command).start()
        self.parent.after(100, self.load_setting_to_widget)

    def bind_command(self):
        def __bind_rel_command(entry, edit_btn):
            entry.bind("<FocusOut>", lambda e: e.widget.config(state="readonly"))
            entry.bind("<Key>", self.edit_entry)
            edit_btn.command = lambda _: self.active_entry(entry)
        self.basic_canvas.bind("<Configure>", self.update_window_size)
        self.basic_frame.bind_all("<MouseWheel>", self.on_mouse_wheel)
        __bind_rel_command(self.capture_shortcuts_entry, self.capture_entry_edit_btn)
        __bind_rel_command(self.call_shortcuts_entry, self.call_entry_edit_btn)
        __bind_rel_command(self.exit_shortcut_entry, self.exit_entry_edit_btn)
        self.back_btn.command = lambda _: self.save_setting()
        self.browse_auto_save_path_btn.command = self.browse_auto_save_path
        self.open_auto_save_path_btn.command = self.open_auto_save_path

    def update_window_size(self, event):
        new_width = event.width - 40
        self.basic_canvas.itemconfig(self.window_id, width=new_width)

    def on_mouse_wheel(self, event):
        canvas_height = self.basic_canvas.winfo_height()
        bbox = self.basic_canvas.bbox("all")
        if bbox:
            frame_height = bbox[3] - bbox[1]
            if canvas_height > frame_height:
                return "break"
            self.basic_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        return

    def insert_into_entry(self, entry: ttk.Entry, text: str = "") -> None:
        entry.config(state="active")
        entry.delete(0, tk.END)
        entry.insert(0, text)
        entry.xview_moveto(1.0)
        entry.config(state="readonly")

    def active_entry(self, entry: ttk.Entry):
        entry.config(state="active")
        entry.focus()

    def load_setting_to_widget(self):
        self.insert_into_entry(self.capture_shortcuts_entry, " + ".join(self.env.capture_shortcuts))
        self.insert_into_entry(self.call_shortcuts_entry, " + ".join(self.env.call_shortcuts))
        self.insert_into_entry(self.exit_shortcut_entry, " + ".join(self.env.exit_shortcuts))
        self.insert_into_entry(self.auto_save_path_entry, self.env.auto_save_path)
        self.auto_delete_spinbox.insert(0, self.env.auto_delete_upper)
        self.auto_save_var.set(self.env.auto_save)
        self.auto_copy_var.set(self.env.auto_copy)
        self.auto_delete_var.set(self.env.auto_delete)

    def save_setting(self):
        def __save_setting():
            self.env.capture_shortcuts = self.capture_shortcuts_entry.get().split(" + ")
            self.env.call_shortcuts = self.call_shortcuts_entry.get().split(" + ")
            self.env.exit_shortcuts = self.exit_shortcut_entry.get().split(" + ")
            self.env.auto_copy = self.auto_copy_var.get()
            self.env.auto_save = self.auto_save_var.get()
            self.env.auto_save_path = self.auto_save_path_entry.get()
            self.env.auto_delete = self.auto_delete_var.get()
            self.env.auto_delete_upper = int(self.auto_delete_spinbox.get())
            self.clear_invalid_shortcuts(self.env.capture_shortcuts)
            self.clear_invalid_shortcuts(self.env.call_shortcuts)
            self.clear_invalid_shortcuts(self.env.exit_shortcuts)
            self.env.save_to_file()
            self.basic_frame.unbind_all("<MouseWheel>")
            self.basic_frame.destroy()
            self.master.unbind_keyboard_event()
            self.master.add_keyboard_event()
        self.basic_frame.place_forget()
        current_x, current_y = self.master.winfo_x(), self.master.winfo_y()
        self.parent.geometry(f"{self.orig_pos[0]}x{self.orig_pos[1]}+{current_x}+{current_y}")
        Thread(target=__save_setting).start()

    def edit_entry(self, event):
        entry: ttk.Entry = event.widget
        state = entry.cget("state")
        if state == "readonly":
            return "break"
        if entry == self.capture_shortcuts_entry:
            tmp_shortcuts = self.env.capture_shortcuts
        elif entry == self.call_shortcuts_entry:
            tmp_shortcuts = self.env.call_shortcuts
        elif entry == self.exit_shortcut_entry:
            tmp_shortcuts = self.env.exit_shortcuts
        key = KEYS_TRANSFORM.get(event.keysym, event.keysym)
        if key == "??":
            return
        if len(key) == 1:
            key = key.upper()
        elif key == "BackSpace" and len(tmp_shortcuts) > 0:
            tmp_shortcuts.pop()
        if key in VALID_SHORTCUTS_KEYS and key not in tmp_shortcuts:
            if len(tmp_shortcuts) == 3:
                tmp_shortcuts.pop()
            tmp_shortcuts.append(key)
        entry.delete(0, tk.END)
        entry.insert(0, " + ".join(tmp_shortcuts))
        return "break"

    def browse_auto_save_path(self, _):
        path = filedialog.askdirectory()
        if not path:
            return
        self.insert_into_entry(self.auto_save_path_entry, path)

    def open_auto_save_path(self, _):
        path = self.auto_save_path_entry.get()
        path = os.getcwd() if path == "" else path
        if os.path.isdir(path):
            os.startfile(path)

    def disable_entry(self, event):
        entry: tk.Entry = event.widget
        entry.config(state="readonly")

    def clear_invalid_shortcuts(self, keys: list):
        for key in keys.copy():
            if key not in VALID_SHORTCUTS_KEYS:
                keys.remove(key)   

