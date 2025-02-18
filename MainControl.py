import tkinter as tk
from tkinter import ttk
import keyboard
import win32clipboard
import os
from io import BytesIO
from threading import Thread
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, UnidentifiedImageError
from Setting import *
from Widgets import AdjustableRect
from Utils import ScreenshotUtils, Event
from MainUI import MainUI, SettingUI




class ScreenshotTool(MainUI):
    def __init__(self):
        super().__init__()
        self.env = Env()
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

    def initialize_screenshot_coords(self):
        self.screenshot.start_x = self.screenshot.start_y = 0
        self.screenshot.end_x = SCREEN_WIDTH
        self.screenshot.end_y = SCREEN_HEIGHT

    def start_capture(self, _=None):
        def __start_capture():
            self.capture_win = tk.Toplevel()
            self.capture_win.attributes("-topmost", True)
            self.capture_win.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+0+0")
            self.capture_win.overrideredirect(True)
            self.full_screenshot_canvas = self.set_full_screenshot_canvas(self.capture_win)
            self.adjust_rect = AdjustableRect(self.full_screenshot_canvas, self.screenshot)
            event = Event(*self.capture_win.winfo_pointerxy())
            self.initialize_screenshot_coords()
            self.adjust_rect.create_rect()
            self.set_magnifier_frame(event)
            self.update_magnifier(event)
            self.set_adjust_bar()
            self.full_screenshot_canvas.bind("<Button-1>", self.on_press)
            self.full_screenshot_canvas.bind("<Motion>", self.update_magnifier)
            self.full_screenshot_canvas.bind("<ButtonRelease-1>", self.on_release)
        keyboard.remove_hotkey(self.env.shortcuts_id[0])
        keyboard.remove_hotkey(self.env.shortcuts_id[1])
        self.add_shortcuts(2)
        self.attributes('-alpha', 0)
        self.after(0, __start_capture)

    def on_press(self, event) -> None:
        self.adjust_rect.on_press(event)
        self.full_screenshot_canvas.unbind("<Motion>")
        self.full_screenshot_canvas.bind("<Motion>", self.on_drag)

    def on_drag(self, event) -> None:
        self.adjust_rect.rect_adjust(event)
        self.update_magnifier(event)

    def on_release(self, event, resize=True) -> None:
        self.unbind_all()
        self.adjust_rect.on_release(event)
        self.full_screenshot_canvas.bind("<Button-1>", self.enter_adjust_mode)
        self.full_screenshot_canvas.bind("<Motion>", self.adjust_rect.on_hover)
        self.adjust_bar.place(
            x=min(self.screenshot.end_x - 300, SCREEN_WIDTH - 300), width=300,
            y=max(min(self.screenshot.end_y + 10, SCREEN_HEIGHT - TkS(40)), 0),
        )
        if resize:
            self.screenshot.end_x, self.screenshot.end_y = event.x, event.y
        self.conceal_move_widget()
        self.update_width_height_info(event)

    def rect_adjust(self, event) -> None:
        self.adjust_rect.rect_adjust(event)
        if self.adjust_rect.anchor_id != 8 or self.adjust_rect.anchor_id == -1:
            self.update_magnifier(event)

    def unbind_all(self):
        events = ("<Button-1>", "<Motion>", "<ButtonRelease-1>")
        for event in events:
            self.full_screenshot_canvas.unbind(event)

    def clear_redraw_widget(self) -> None:
        for redraw_widget in self.screenshot.screenshot_redraw_widget:
            self.full_screenshot_canvas.delete(redraw_widget)
        self.screenshot.screenshot_redraw_widget.clear()

    def conceal_move_widget(self):
        for widget in self.screenshot.screenshot_move_widget:
            self.full_screenshot_canvas.tag_lower(widget)

    def update_width_height_info(self, event) -> None:
        self.clear_redraw_widget()
        w, h = self.adjust_rect.rect_width_height()
        coord = self.screenshot.redraw_widget_coords(event.x, event.y)[1]
        wh_info_widget = self.full_screenshot_canvas.create_text(*coord, anchor=tk.NW, fill="white", text=f"{w} × {h}")
        self.screenshot.screenshot_redraw_widget = [wh_info_widget]

    def update_magnifier(self, event, ) -> None:
        x, y = event.x, event.y
        size = ScreenshotUtils.ZOOM_WIDTH
        img = self.screenshot.current_image.crop((x - size//2, y - size//2, x + size//2, y + size//2))
        img = img.resize((ScreenshotUtils.ZOOM_SCREEN_SIZE, ScreenshotUtils.ZOOM_SCREEN_SIZE))
        photo = ImageTk.PhotoImage(img)
        self.full_screenshot_canvas.image2 = photo
        w, h = self.adjust_rect.rect_width_height()
        self.clear_redraw_widget()
        redraw_widget_coords = self.screenshot.redraw_widget_coords(x, y)
        magnifier_coord, width_height_info, pos_coord, rgb_coord = redraw_widget_coords
        zoom_img = self.full_screenshot_canvas.create_image(*magnifier_coord, anchor=tk.NW, image=photo)
        wh_info_widget = self.full_screenshot_canvas.create_text(
            *width_height_info, anchor=tk.NW, fill="white", text=f"{w} × {h}"
        )
        pos_rgb_info = self.config_pos_rgb_info(
            self.full_screenshot_canvas, f"POS: ({x}, {y})", 
            f"RGB: {self.screenshot.pixel_reader.getpixel((x, y))}", pos_coord, rgb_coord
        )
        self.screenshot.screenshot_redraw_widget = [zoom_img, wh_info_widget, *pos_rgb_info]
        self.update_magnifier_frame(*self.full_screenshot_canvas.coords(zoom_img))

    def update_magnifier_frame(self, x, y) -> None:
        coords = self.screenshot.move_widget_coords(x, y)
        for widget, coord in zip(self.screenshot.screenshot_move_widget, coords):
            self.full_screenshot_canvas.coords(widget, *coord)
            self.full_screenshot_canvas.tag_raise(widget)

    def enter_adjust_mode(self, event) -> None:
        self.screenshot.move_start_x = event.x
        self.screenshot.move_start_y = event.y
        self.adjust_bar.place_forget()
        for widget in self.screenshot.screenshot_redraw_widget:
            self.full_screenshot_canvas.delete(widget)
        for widget in self.screenshot.screenshot_move_widget:
            self.full_screenshot_canvas.tag_lower(widget)
        self.full_screenshot_canvas.bind("<B1-Motion>", self.rect_adjust)
        self.full_screenshot_canvas.bind("<ButtonRelease-1>", lambda e: self.on_release(e, False))

    def clear_capture_info(self, _) -> None:
        self.capture_win.destroy()
        self.full_screenshot_canvas.destroy()
        self.attributes('-alpha', 1)
        self.screenshot.screenshot_move_widget.clear()
        self.add_keyboard_event()
        
    def confirm_capture(self, event=None) -> None:
        x1, y1, x2, y2 = self.adjust_rect.rect_coords()
        self.clear_capture_info(event)
        if x2 - x1 == 0 or y2 - y1 == 0:
            return
        image = self.screenshot.current_image.crop((x1, y1, x2, y2))
        self.screenshot.final_images.append(image)
        self.show_image_canvas.show_image(image)
        self.screenshot.page_index = len(self.screenshot.final_images) - 1
        self.auto_operation(event)
        self.attributes('-topmost', 1)
        keyboard.remove_hotkey(self.env.shortcuts_id[2])

    def load_image(self, event) -> None:
        file_types = (("Image files", "*.jpg *.png *.jpeg"), )
        img_path = filedialog.askopenfilename(filetypes=file_types)
        if not img_path:
            return
        try:
            image: Image.Image = Image.open(img_path)
            if image in self.screenshot.final_images:
                return messagebox.showinfo("提示", "该图片已存在!")
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
        initialfile = f"{image.width}x{image.height}.png"
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
        # 动态更新窗口宽度
        new_width = event.width - 40
        self.basic_canvas.itemconfig(self.window_id, width=new_width)

    def on_mouse_wheel(self, event):
        # 获取窗口高度和框架高度
        canvas_height = self.basic_canvas.winfo_height()
        bbox = self.basic_canvas.bbox("all")
        if bbox:
            frame_height = bbox[3] - bbox[1]
            # 如果窗口高度大于框架高度，阻止滚动
            if canvas_height > frame_height:
                return "break"
            # 正常处理滚动事件
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

