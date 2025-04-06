import tkinter as tk
from tkinter import ttk

import pystray

from Utils import ScreenshotUtils, FileUtils
from tkinter_extension.Widget.Switch import EllipseSwitch
from Widgets import *


if TYPE_CHECKING:
    from MainControl import ScreenshotTool




class MainUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.screenshot = ScreenshotUtils()
        self.menu_bar: tk.Frame = self._set_menubar()
        self.cut_btn: CharacterButton = self._set_character_btn("✂")
        self.load_image_btn: CharacterButton = self._set_character_btn("📤︎")
        self.edit_in_file_btn: CharacterButton = self._set_character_btn("🎨")
        self.nail_btn: CharacterButton = self._set_character_btn("📌")
        self.setting_btn: CharacterButton = self._set_character_btn("⚙")
        self.show_image_canvas: ShowImageCanvas = ShowImageCanvas(self)
        self.capture_win: tk.Toplevel = None
        self.full_screenshot_canvas: ScreenshotCanvas = None
        self.magnifer: Magnifier = None
        self.adjust_rect: AdjustableRect = None
        self.screenshot_tip: ScreenshotTip = None
        self.edit_bar: EditBar = None
        self._set_window()

    def _set_window(self):
        self.title(Window.window_title)
        window_width = Window.TKS(self.winfo_reqwidth()) + Size.num[5]
        window_height = Window.window_height
        self.minsize(width=window_width, height=window_height)
        self.after(100, self.iconbitmap, File.icon_file)
        self.attributes("-topmost", True)
        self.geometry(f"{window_width}x{window_height}")

    def _set_menubar(self) -> tk.Frame:
        menubar = tk.Frame(self, height=Window.window_height, **Style.get("Frame"))
        menubar.pack(side=tk.TOP, fill=tk.X)
        menubar.rowconfigure(0, weight=1)
        menubar.grid_propagate(False)
        return menubar
    
    def _set_character_btn(self, text: str) -> CharacterButton:
        normal_style = Style.get("Button", "designs")
        special_style = Style.get("Button", "special")
        if text in special_style:
            normal_style = normal_style | special_style[text]
        btn = CharacterButton(self.menu_bar, text=text, **normal_style)
        btn.pack(side=tk.LEFT, padx=Size.num[1])
        return btn

    def set_show_image_canvas(self) -> ShowImageCanvas:
        return ShowImageCanvas(self)

    def set_adjust_rect(self, parent) -> AdjustableRect:
        return AdjustableRect(parent, self.screenshot)
 
    def set_magnifier(self, parent) -> Magnifier:
        return Magnifier(parent, self.screenshot)
    
    def set_screenshot_tip(self, parent) -> ScreenshotTip:
        return ScreenshotTip(parent, self.screenshot)

    def set_screenshot_canvas(self, parent) -> ScreenshotCanvas:
        return ScreenshotCanvas(parent, self.screenshot)
    
    def set_edit_bar(self, parent) -> EditBar:
        return EditBar(parent)


class SettingUI(object):
    def __init__(self, parent: 'ScreenshotTool'):
        self.parent: 'ScreenshotTool' = parent
        self.orig_geometry: tuple[int, int, int, int] = self.update_parent_attr()
        self._set_all_frame()
        self._set_all_tip_label()
        self._set_all_entry()
        self._set_all_btn()
        self._set_all_switch()
        self.update_scrollbar()
    
    def _set_character_btn(self, text: str, master: tk.Widget) -> CharacterButton:
        normal_style = Style.get("Button", "characters")
        special_style = Style.get("Button", "special")
        if text in special_style:
            normal_style = normal_style | special_style[text]
        return CharacterButton(master, text=text, **normal_style)
    
    def _set_labelframe(self, text: str, pady: int | tuple[int, int], weight_column: int = 1) -> tk.LabelFrame:
        label_frame = tk.LabelFrame(
            self._content_frame, borderwidth=Size.num[1], 
            text=text, **Style.get("LabelFrame")
        )
        label_frame.columnconfigure(weight_column, weight=1)
        label_frame.pack(padx=Size.num[3], pady=pady, side=tk.TOP, fill=tk.X, expand=True)
        return label_frame
    
    def _set_inner_scrollable_frame(self) -> tk.Frame:
        self.basic_canvas = tk.Canvas(self.basic_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.basic_frame, command=self.basic_canvas.yview, width=Size.num[8])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.basic_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.basic_canvas.configure(yscrollcommand=scrollbar.set)
        content_frame = tk.Frame(self.basic_canvas, **Style.get("Frame"))
        self.basic_canvas.create_window((0, 0), window=content_frame, anchor=tk.NW, tags="content_frame")
        return content_frame
    
    def _set_all_frame(self) -> None:
        self.basic_frame = tk.Frame(self.parent, **Style.get("Frame"))
        self.basic_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self._content_frame = self._set_inner_scrollable_frame()
        self.shortcuts_labelframe = self._set_labelframe("快捷方式", pady=(Size.num[10], Size.num[5]))
        self.auto_operation_labelframe = self._set_labelframe("自动选项", pady=0, weight_column=0)
        self.config_file_labelframe = self._set_labelframe("配置文件", pady=(Size.num[5], Size.num[3]))

    def _set_all_tip_label(self) -> None:
        def tip_label(text: str, master: tk.Widget) -> tk.Label:
            return tk.Label(master, text=text, **Style.get("Label"))
        same_grid_info = {"column": 0, "sticky": tk.W}
        tip_label("设置", self._content_frame).place(x=Size.num[10], y=0)
        tip_label("启动截图", self.shortcuts_labelframe).grid(row=0, pady=Size.num[2], **same_grid_info)
        tip_label("唤起窗口", self.shortcuts_labelframe).grid(row=1, pady=Size.num[4], **same_grid_info)
        tip_label("钉在桌面", self.shortcuts_labelframe).grid(row=2, **same_grid_info)
        tip_label("自动复制截图", self.auto_operation_labelframe).grid(row=0, **same_grid_info)
        tip_label("自动保存截图", self.auto_operation_labelframe).grid(row=1, pady=(Size.num[4], 0), **same_grid_info)
        tip_label("启动隐藏窗口", self.auto_operation_labelframe).grid(row=5, pady=(Size.num[4], 0), **same_grid_info)
        tip_label("关闭清空截图", self.auto_operation_labelframe).grid(row=6, pady=Size.num[6], **same_grid_info)
        tip_label("帮助文档", self.config_file_labelframe).grid(row=0, **same_grid_info)
        tip_label("配置文件", self.config_file_labelframe).grid(row=1, **same_grid_info)
        tip_label("主题文件", self.config_file_labelframe).grid(row=2, **same_grid_info)

    def _set_all_btn(self):
        def create_and_grid_btn(text, master, grid_options=None):
            all_grid_option = same_grid_option | grid_options
            btn = self._set_character_btn(text, master)
            btn.grid(**all_grid_option)
            return btn
        
        self.back_btn = self._set_character_btn("←", self._content_frame)
        self.back_btn.place(x=0, y=0, width=Size.num[9])
        self.browse_auto_save_path_btn = self._set_character_btn("…", self.auto_save_path_entry)
        self.browse_auto_save_path_btn.pack(side=tk.RIGHT, padx=(0, Size.num[2]), pady=0)
        same_grid_option = {"sticky": tk.E, 'padx': (0, Size.num[3]), "pady": Size.num[2], "ipady": Size.num[2]}

        btns_config = (
            ("重置", self.shortcuts_labelframe, {'row': 0, 'column': 2}),
            ("重置", self.shortcuts_labelframe, {'row': 1, 'column': 2}),
            ("重置", self.shortcuts_labelframe, {'row': 2, 'column': 2}),
            ("打开", self.auto_operation_labelframe, {'row': 3, 'column': 2, "pady": 0}),
            ("打开", self.config_file_labelframe, {'row': 0, 'column': 1}),
            ("打开", self.config_file_labelframe, {'row': 1, 'column': 1}),
            ("打开", self.config_file_labelframe, {'row': 2, 'column': 1}),
        )
        self.capture_entry_restore_btn = create_and_grid_btn(*btns_config[0])
        self.call_entry_restore_btn = create_and_grid_btn(*btns_config[1])
        self.exit_entry_restore_btn = create_and_grid_btn(*btns_config[2])
        self.open_auto_save_path_btn = create_and_grid_btn(*btns_config[3])
        self.open_help_btn = create_and_grid_btn(*btns_config[4])
        self.open_config_file_btn = create_and_grid_btn(*btns_config[5])
        self.open_style_file_btn = create_and_grid_btn(*btns_config[6])

    def _set_all_entry(self) -> None:
        same_grid_option = {"sticky": tk.EW, "padx": Size.num[2], "ipady": Size.num[2]}
        self.capture_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe)
        self.capture_shortcuts_entry.grid(row=0, column=1, pady=Size.num[2], **same_grid_option)
        
        self.call_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe)
        self.call_shortcuts_entry.grid(row=1, column=1, **same_grid_option)

        self.exit_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe)
        self.exit_shortcuts_entry.grid(row=2, column=1, **same_grid_option)
    
        self.auto_save_path_entry = ttk.Entry(self.auto_operation_labelframe)
        self.auto_save_path_entry.grid(row=3, column=0, pady=0, **same_grid_option)
    
    def _set_all_switch(self) -> None:
        self.auto_copy_switch = EllipseSwitch(self.auto_operation_labelframe, size=Size.num[8])
        self.auto_copy_switch.grid(row=0, column=2, padx=(0, Size.num[3]))
        self.auto_save_switch = EllipseSwitch(self.auto_operation_labelframe, size=Size.num[8])
        self.auto_save_switch.grid(row=1, column=2, padx=(0, Size.num[3]), pady=(Size.num[4], 0))
        self.auto_conceal_switch = EllipseSwitch(self.auto_operation_labelframe, size=Size.num[8])
        self.auto_conceal_switch.grid(row=5, column=2, padx=(0, Size.num[3]), pady=(Size.num[4], 0))
        self.auto_clear_switch = EllipseSwitch(self.auto_operation_labelframe, size=Size.num[8])
        self.auto_clear_switch.grid(row=6, column=2, padx=(0, Size.num[3]), pady=(Size.num[4], 0))
    
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
            pystray.MenuItem(text='菜单', action=self.main_control.toggle_ui, default=True),
            pystray.MenuItem(text='清空贴图', action=self.main_control.clear_snail_image),
            pystray.MenuItem(text='历史截图', action=lambda _: FileUtils.open_file_path(File.history_dir)),
            pystray.MenuItem(text='退出', action=self.main_control.exit),
        )
        return menu

    def run(self):
        self.icon = pystray.Icon(
            "lightScreenshot", 
            self.ico_image, 
            "单击显示/隐藏主窗口", 
            self.create_menu()
        )
        self.icon.run()

    def stop(self):
        self.icon.stop()
