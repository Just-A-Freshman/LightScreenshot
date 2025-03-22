import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import pystray

from Utils import ScreenshotUtils
from tkinter_extension.Widget.Switch import EllipseSwitch
from Widgets import *


if TYPE_CHECKING:
    from MainControl import ScreenshotTool



class MainUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.screenshot = ScreenshotUtils()
        self.set_window()
        self.menu_bar: tk.Frame = self.set_menubar()
        self.cut_btn: CharacterButton = self.set_cut_btn()
        self.load_image_btn: CharacterButton = self.set_load_image_btn()
        self.edit_in_file_btn: CharacterButton = self.set_edit_in_file_btn()
        self.nail_btn: CharacterButton = self.set_nail_btn()
        self.setting_btn: CharacterButton = self.set_setting_btn()
        self.show_image_canvas: ShowImageCanvas = self.set_show_image_canvas()
        self.capture_win: tk.Toplevel = None
        self.full_screenshot_canvas: ScreenshotCanvas = None
        self.magnifer: Magnifier = None
        self.adjust_rect: AdjustableRect = None
        self.screenshot_tip: ScreenshotTip = None
        self.edit_bar: EditBar = None

    def set_window(self):
        self.title(Window.window_title)
        self.minsize(width=Window.window_width, height=Window.window_height)
        self.after(100, self.iconbitmap, File.icon_file)
        self.attributes("-topmost", True)
        self.geometry(f"{Window.window_width}x{Window.window_height}")

    def set_menubar(self) -> tk.Frame:
        menubar = tk.Frame(self, bg=Style.get("Color", 0), height=Window.TKS(30))
        menubar.pack(side=tk.TOP, fill=tk.X)
        menubar.rowconfigure(0, weight=1)
        menubar.grid_propagate(False)
        return menubar

    def set_cut_btn(self) -> CharacterButton:
        btn_cut = CharacterButton(
            self.menu_bar, text="✂", 
            bg=Style.get("Color", 0), font=(Style.get("fontFamily", 1), Style.get("fontSize", 3)),
        )
        btn_cut.grid(row=0, column=0, padx=3)
        return btn_cut
    
    def set_load_image_btn(self) -> CharacterButton:
        btn_load = CharacterButton(
            self.menu_bar, text="📤︎", bg=Style.get("Color", 0),
            font=(Style.get("fontFamily", 2), Style.get("fontSize", 3)), anchor=tk.W, width=2
        )
        btn_load.grid(row=0, column=1, padx=3)
        return btn_load
    
    def set_edit_in_file_btn(self) -> CharacterButton:
        btn_edit = CharacterButton(
            self.menu_bar, text="🎨", bg=Style.get("Color", 0),
            font=(Style.get("fontFamily", 1), Style.get("fontSize", 3)), anchor=tk.W
        )
        btn_edit.grid(row=0, column=2, padx=3)
        return btn_edit
    
    def set_nail_btn(self) -> CharacterButton:
        nail_btn = CharacterButton(
            self.menu_bar, text="📌", bg=Style.get("Color", 0), 
            font=(Style.get("fontFamily", 1), Style.get("fontSize", 3)),
        )
        nail_btn.grid(row=0, column=3, padx=3)
        return nail_btn
    
    def set_setting_btn(self) -> CharacterButton:
        setting_btn = CharacterButton(
            self.menu_bar, text="⚙", bg=Style.get("Color", 0), 
            font=(Style.get("fontFamily", 1), Style.get("fontSize", 3)),
        )
        setting_btn.grid(row=0, column=4, padx=3)
        return setting_btn
 
    def set_show_image_canvas(self) -> ShowImageCanvas:
        canvas = ShowImageCanvas(self)
        return canvas

    def set_adjust_rect(self, parent) -> None:
        self.adjust_rect = AdjustableRect(parent, self.screenshot)
        return self.adjust_rect
 
    def set_magnifier(self, parent) -> None:
        magnifier = Magnifier(parent, self.screenshot)
        return magnifier
    
    def set_screenshot_tip(self, parent) -> None:
        screenshot_tip = ScreenshotTip(parent, self.screenshot)
        return screenshot_tip

    def set_screenshot_canvas(self, parent):
        screenshot_canvas = ScreenshotCanvas(parent, self.screenshot)
        return screenshot_canvas
    
    def set_edit_bar(self, parent) -> None:
        edit_bar = EditBar(parent, self.screenshot)
        return edit_bar


class SettingUI(object):
    def __init__(self, parent: 'ScreenshotTool'):
        self.parent: 'ScreenshotTool' = parent
        self.window_id: int = 0
        self.orig_geometry: tuple[int, int, int, int] = self.update_parent_attr()
        self.basic_frame: tk.Frame = self.set_basic_frame()
        self.inner_frame: tk.Frame = self.set_inner_scrollable_frame()
        self.back_btn: CharacterButton = self.set_back_btn()
        self.shortcuts_labelframe: tk.LabelFrame = self.set_shortcut_labelframe()
        self.auto_operation_labelframe: tk.LabelFrame = self.set_auto_operation_labelframe()
        self.capture_shortcuts_entry: ttk.Entry = self.set_capture_shortcuts_entry()
        self.call_shortcuts_entry: ttk.Entry = self.set_call_shortcuts_entry()
        self.exit_shortcut_entry: ttk.Entry = self.set_exit_shortcuts_entry()
        self.capture_entry_restore_btn: CharacterButton = self.set_capture_entry_restore_btn()
        self.call_entry_restore_btn: CharacterButton = self.set_call_entry_restore_btn()
        self.exit_entry_restore_btn: CharacterButton = self.set_exit_entry_restore_btn()
        self.auto_copy_switch: EllipseSwitch = self.set_auto_copy_switch()
        self.auto_save_switch: EllipseSwitch = self.set_auto_save_switch()
        self.auto_delete_switch: EllipseSwitch = self.set_auto_delete_switch()
        self.auto_save_path_entry: tk.Entry = self.set_auto_save_path_entry()
        self.browse_auto_save_path_btn: CharacterButton = self.set_browse_auto_save_path_btn()
        self.open_auto_save_path_btn: CharacterButton = self.set_open_auto_save_path_btn()
        self.auto_delete_spinbox: tk.Spinbox = self.set_auto_delete_spinbox()
        self.update_scrollbar()

    def set_basic_frame(self) -> tk.Frame:
        basic_frame = tk.Frame(self.parent, bg=Style.get("Color", 2))
        basic_frame.place(x=0, y=0, relwidth=1, relheight=1)
        return basic_frame
    
    def set_inner_scrollable_frame(self) -> tk.Frame:
        self.basic_canvas = tk.Canvas(self.basic_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.basic_frame, command=self.basic_canvas.yview, width=40)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.basic_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.basic_canvas.configure(yscrollcommand=scrollbar.set)
        inner_frame = tk.Frame(self.basic_canvas, bg=Style.get("Color", 2), highlightthickness=0)
        self.window_id = self.basic_canvas.create_window((0, 0), window=inner_frame, anchor='nw')
        return inner_frame

    def set_back_btn(self):
        back_btn = CharacterButton(
            self.inner_frame, text="←", bg=Style.get("Color", 2), 
            font=(Style.get("fontFamily", 4), Style.get("fontSize", 3))
        )
        back_btn.place(x=0, y=0, width=50)
        info = tk.Label(
            self.inner_frame, text="设置", font=(Style.get("fontFamily", 0), 
            Style.get("fontSize", 1)), bg=Style.get("Color", 2)
        )
        info.place(x=60, y=0)
        return back_btn

    def set_shortcut_labelframe(self) -> tk.LabelFrame:
        frame = tk.LabelFrame(
            self.inner_frame, text="快捷方式", font=(Style.get("fontFamily", 0), 
            Style.get("fontSize", 2)), bg=Style.get("Color", 2), borderwidth=4
        )
        frame.pack(padx=10, pady=(60, 20), side=tk.TOP, fill=tk.X, expand=True)
        return frame

    def set_auto_operation_labelframe(self) -> tk.LabelFrame:
        frame = tk.LabelFrame(
            self.inner_frame, text="自动操作", 
            font=(Style.get("fontFamily", 0), Style.get("fontSize", 2)), 
            bg=Style.get("Color", 2), borderwidth=4
        )
        frame.pack(padx=10, side=tk.TOP, fill=tk.X, expand=True)
        return frame

    def set_capture_shortcuts_entry(self) -> ttk.Entry:
        tip = tk.Label(
            self.shortcuts_labelframe, text="启动截图:", 
            font=(Style.get("fontFamily", 0), Style.get("fontSize", 1))
        )
        tip.grid(row=0, column=0, ipady=5, pady=5)
        capture_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe)
        capture_shortcuts_entry.grid(row=0, column=1, sticky=tk.EW, ipady=5, pady=5, padx=(0, 10))
        self.shortcuts_labelframe.columnconfigure(1, weight=1)
        return capture_shortcuts_entry
    
    def set_capture_entry_restore_btn(self) -> CharacterButton:
        restore_btn = CharacterButton(self.shortcuts_labelframe, text="重置")
        restore_btn.grid(row=0, column=2, sticky=tk.E, pady=15, ipady=5, padx=(0, 10))
        return restore_btn

    def set_call_shortcuts_entry(self) -> ttk.Entry:
        tip = tk.Label(
            self.shortcuts_labelframe, text="唤起窗口:", 
            font=(Style.get("fontFamily", 0), Style.get("fontSize", 1))
        )
        tip.grid(row=1, column=0, sticky=tk.W, pady=15, ipady=5)
        call_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe)
        call_shortcuts_entry.grid(row=1, column=1, sticky=tk.EW, ipady=5, padx=(0, 10))
        self.shortcuts_labelframe.columnconfigure(1, weight=1)
        return call_shortcuts_entry
    
    def set_call_entry_restore_btn(self) -> CharacterButton:
        restore_btn = CharacterButton(self.shortcuts_labelframe, text="重置")
        restore_btn.grid(row=1, column=2, sticky=tk.E, pady=15, ipady=5, padx=(0, 10))
        return restore_btn
    
    def set_exit_shortcuts_entry(self) -> ttk.Entry:
        tip = tk.Label(self.shortcuts_labelframe, text="确定裁剪:", font=(Style.get("fontFamily", 0), Style.get("fontSize", 1)))
        tip.grid(row=2, column=0, sticky=tk.W, pady=15, ipady=5)
        exit_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe)
        exit_shortcuts_entry.grid(row=2, column=1, sticky=tk.EW, ipady=5, padx=(0, 10))
        self.shortcuts_labelframe.columnconfigure(1, weight=1)
        return exit_shortcuts_entry
    
    def set_exit_entry_restore_btn(self) -> CharacterButton:
        restore_btn = CharacterButton(self.shortcuts_labelframe, text="重置")
        restore_btn.grid(row=2, column=2, sticky=tk.E, pady=15, ipady=5, padx=(0, 10))
        return restore_btn
    
    def set_auto_copy_switch(self) -> EllipseSwitch:
        tip_label = tk.Label(self.auto_operation_labelframe, text="自动复制截图", font=(Style.get("fontFamily", 0), Style.get("fontSize", 1)))
        tip_label.grid(row=0, column=0, sticky=tk.W, ipady=5)
        auto_copy_switch = EllipseSwitch(self.auto_operation_labelframe)
        auto_copy_switch.grid(row=0, column=2)
        return auto_copy_switch

    def set_auto_save_switch(self) -> EllipseSwitch:
        tip_label = tk.Label(
            self.auto_operation_labelframe, text="自动保存截图", 
            font=(Style.get("fontFamily", 0), Style.get("fontSize", 1))
        )
        tip_label.grid(row=1, column=0, sticky=tk.W, ipady=5, pady=(15, 0))
        auto_save_switch = EllipseSwitch(self.auto_operation_labelframe)
        auto_save_switch.grid(row=1, column=2, pady=(15, 0))
        return auto_save_switch

    def set_auto_save_path_entry(self) -> ttk.Entry:
        auto_save_path_entry = ttk.Entry(self.auto_operation_labelframe)
        auto_save_path_entry.grid(row=4, column=0, sticky=tk.W + tk.E, pady=5, ipady=5, padx=5)
        self.auto_operation_labelframe.columnconfigure(0, weight=1)
        self.auto_operation_labelframe.columnconfigure(1, weight=0)
        return auto_save_path_entry
    
    def set_auto_delete_switch(self) -> EllipseSwitch:
        tip_label = tk.Label(
            self.auto_operation_labelframe, text="自动删除截图", 
            font=(Style.get("fontFamily", 0), Style.get("fontSize", 1))
        )
        tip_label.grid(row=5, column=0, sticky=tk.W, ipady=5, pady=(25, 0))
        auto_delete_switch = EllipseSwitch(self.auto_operation_labelframe)
        auto_delete_switch.grid(row=5, column=2, pady=(25, 0))
        return auto_delete_switch
    
    def set_auto_delete_spinbox(self) -> ttk.Spinbox:
        tip_label = tk.Label(
            self.auto_operation_labelframe, text="截图数上限", 
            font=(Style.get("fontFamily", 0), Style.get("fontSize", 0))
        )
        tip_label.grid(row=6, column=0, sticky=tk.W, pady=0)
        auto_delete_spinbox = tk.Spinbox(
            self.auto_operation_labelframe, values=list(range(3, 31)), 
            width=2, state="readonly", bd=0
        )
        auto_delete_spinbox.grid(row=6, column=2, pady=0)
        return auto_delete_spinbox
    
    def set_browse_auto_save_path_btn(self) -> CharacterButton:
        browse_btn = CharacterButton(self.auto_operation_labelframe, text="更改")
        browse_btn.grid(row=4, column=1, sticky=tk.E, pady=(5, 10), ipady=5)
        return browse_btn
    
    def set_open_auto_save_path_btn(self) -> CharacterButton:
        open_btn = CharacterButton(self.auto_operation_labelframe, text="打开")
        open_btn.grid(row=4, column=2, sticky=tk.E, pady=(5, 10), padx=(0, 40), ipady=5)
        return open_btn
    
    def update_parent_attr(self) -> tuple[int, int, int, int]:
        style = ttk.Style()
        style.theme_use("clam")
        tmp_x, tmp_y = self.parent.geometry().split("x")
        window_w = int(tmp_x)
        window_h, window_x, window_y = [int(i) for i in tmp_y.split("+")]
        self.parent.geometry(
            f"{max(Window.setting_window_width, window_w)}x{max(Window.window_height * 8, window_h)}"
        )
        return window_w, window_h, window_x, window_y
    
    def update_scrollbar(self):
        self.basic_frame.update()
        self.basic_canvas.configure(scrollregion=self.basic_canvas.bbox("all"))


class Tray(object):
    def __init__(self, main_control: 'ScreenshotTool'):
        self.main_control = main_control
        self.ico_image = Image.open(File.icon_file)
        self.icon = None

    def create_menu(self) -> pystray.MenuItem:
        menu = (
            pystray.MenuItem(text='截屏', action=self.main_control.start_capture, default=True),
            pystray.MenuItem(text='菜单', action=self.main_control.toggle_ui),
            pystray.MenuItem(text='清空贴图', action=self.main_control.clear_snail_image),
            pystray.MenuItem(text='退出', action=self.main_control.exit),
        )
        return menu

    def run(self):
        self.icon = pystray.Icon(
            "lightScreenshot", 
            self.ico_image, 
            "单击开始截图", 
            self.create_menu()
        )
        self.icon.run()

    def stop(self):
        self.icon.stop()
