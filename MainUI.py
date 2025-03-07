import tkinter as tk
from tkinter import ttk
from Utils import ScreenshotUtils
from Widgets import *
from Setting import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainControl import ScreenshotTool



class MainUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.screenshot = ScreenshotUtils()
        self.set_window()
        self.menu_bar: tk.Frame = self.set_menubar()
        self.cut_btn: FlatButton = self.set_cut_btn()
        self.load_image_btn: FlatButton = self.set_load_image_btn()
        self.copy_btn: FlatButton = self.set_copy_btn()
        self.save_btn: FlatButton = self.set_save_btn()
        self.turn_left_btn: FlatButton = self.set_turn_left_btn()
        self.turn_right_btn: FlatButton = self.set_turn_right_btn()
        self.delete_btn: FlatButton = self.set_delete_btn()
        self.setting_btn: FlatButton = self.set_setting_btn()
        self.show_image_canvas: ShowImageCanvas = self.set_show_image_canvas()
        self.capture_win: tk.Toplevel = None
        self.full_screenshot_canvas: ScreenshotCanvas = None
        self.magnifer: Magnifier = None
        self.adjust_rect: AdjustableRect = None
        self.screenshot_tip: ScreenshotTip = None
        self.edit_bar: EditBar = None

    def set_window(self):
        self.title("截图工具")
        self.minsize(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)  # 这里可以根据需要调整最小宽高
        Thread(target=self.iconbitmap, args=(ICON_FILE, ), daemon=True).start()
        self.attributes("-topmost", True)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        style = ttk.Style()
        style.theme_use("classic")

    def set_menubar(self) -> tk.Frame:
        menubar = tk.Frame(self, bg="#FFFFFF", height=TkS(30))
        menubar.pack(side=tk.TOP, fill=tk.X)
        menubar.rowconfigure(0, weight=1)
        menubar.grid_propagate(False)
        return menubar

    def set_cut_btn(self) -> FlatButton:
        btn_cut = FlatButton(
            self.menu_bar, text="✂", 
            bg="#FFFFFF", font=("Segoe UI Emoji", 18),
        )
        btn_cut.grid(row=0, column=0)
        return btn_cut
    
    def set_load_image_btn(self) -> FlatButton:
        btn_load = FlatButton(
            self.menu_bar, text="📤︎", bg="#FFFFFF",
            font=("Segoe UI Symbol", 19), anchor=tk.W, width=2
        )
        btn_load.grid(row=0, column=1)
        return btn_load
    
    def set_copy_btn(self) -> FlatButton:
        btn_copy = FlatButton(
            self.menu_bar, text="⎘", bg="#FFFFFF", font=("Segoe UI Symbol", 26),
        )
        btn_copy.grid(row=0, column=2)
        return btn_copy

    def set_save_btn(self) -> FlatButton:
        btn_save = FlatButton(
            self.menu_bar, text="💾", bg="#FFFFFF", font=("Segoe UI Emoji", 18),
        )
        btn_save.grid(row=0, column=3)
        return btn_save

    def set_turn_left_btn(self) -> FlatButton:
        turn_left_btn = FlatButton(
            self.menu_bar, text="\u25C0", bg="#FFFFFF", font=("Segoe UI Emoji", 18),
        )
        turn_left_btn.grid(row=0, column=4)
        return turn_left_btn
 
    def set_turn_right_btn(self) -> FlatButton:
        turn_page_btn = FlatButton(
            self.menu_bar, text="\u25B6", bg="#FFFFFF", font=("Segoe UI Emoji", 18),
        )
        turn_page_btn.grid(row=0, column=5)
        return turn_page_btn

    def set_delete_btn(self) -> FlatButton:
        delete_btn = FlatButton(
            self.menu_bar, text="🗑", bg="#FFFFFF", font=("Segoe UI Symbol", 26, "bold"),
        )
        delete_btn.grid(row=0, column=6)
        return delete_btn
    
    def set_setting_btn(self) -> FlatButton:
        setting_btn = FlatButton(
            self.menu_bar, text="⚙", bg="#FFFFFF", font=("Segoe UI Emoji", 18),
        )
        setting_btn.grid(row=0, column=7)
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
        self.orig_pos: tuple[int, int] = self.update_parent_attr()
        self.basic_frame: tk.Frame = self.set_basic_frame()
        self.inner_frame: tk.Frame = self.set_inner_scrollable_frame()
        self.back_btn: FlatButton = self.set_back_btn()
        self.shortcuts_labelframe: tk.LabelFrame = self.set_shortcut_labelframe()
        self.auto_operation_labelframe: tk.LabelFrame = self.set_auto_operation_labelframe()
        self.capture_shortcuts_entry: ttk.Entry = self.set_capture_shortcuts_entry()
        self.call_shortcuts_entry: ttk.Entry = self.set_call_shortcuts_entry()
        self.exit_shortcut_entry: ttk.Entry = self.set_exit_shortcuts_entry()
        self.capture_entry_edit_btn: FlatButton = self.set_capture_entry_edit_btn()
        self.call_entry_edit_btn: FlatButton = self.set_call_entry_edit_btn()
        self.exit_entry_edit_btn: FlatButton = self.set_exit_entry_edit_btn()
        self.auto_copy_var: tk.BooleanVar = self.set_auto_copy_checkbox()
        self.auto_save_var: tk.BooleanVar = self.set_auto_save_checkbox()
        self.auto_delete_var: tk.BooleanVar = self.set_auto_delete_checkbox()
        self.auto_save_path_entry: tk.Entry = self.set_auto_save_path_entry()
        self.browse_auto_save_path_btn: FlatButton = self.set_browse_auto_save_path_btn()
        self.open_auto_save_path_btn: FlatButton = self.set_open_auto_save_path_btn()
        self.auto_delete_spinbox: tk.Spinbox = self.set_auto_delete_spinbox()
        self.update_scrollbar()

    def set_basic_frame(self) -> tk.Frame:
        basic_frame = tk.Frame(self.parent, bg=Style.bg2)
        basic_frame.place(x=0, y=0, relwidth=1, relheight=1)
        return basic_frame
    
    def set_inner_scrollable_frame(self) -> tk.Frame:
        self.basic_canvas = tk.Canvas(self.basic_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.basic_frame, command=self.basic_canvas.yview, width=40)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.basic_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.basic_canvas.configure(yscrollcommand=scrollbar.set)
        inner_frame = tk.Frame(self.basic_canvas, bg=Style.bg2, highlightthickness=0)
        self.window_id = self.basic_canvas.create_window((0, 0), window=inner_frame, anchor='nw', width=self.orig_pos[0] - 40)
        return inner_frame

    def set_back_btn(self):
        back_btn = FlatButton(self.inner_frame, text="←", bg=Style.bg2, font=("楷体", 18))
        back_btn.place(x=0, y=0, width=50)
        info = tk.Label(self.inner_frame, text="设置", font=("微软雅黑", 12), bg=Style.bg2)
        info.place(x=60, y=0)
        return back_btn

    def set_shortcut_labelframe(self) -> tk.LabelFrame:
        frame = tk.LabelFrame(self.inner_frame, text="快捷方式", font=Style.head1, bg=Style.bg2, borderwidth=4)
        frame.pack(padx=10, pady=(60, 20), side=tk.TOP, fill=tk.X, expand=True)
        return frame

    def set_auto_operation_labelframe(self) -> tk.LabelFrame:
        frame = tk.LabelFrame(self.inner_frame, text="自动操作", font=Style.head1, bg=Style.bg2, borderwidth=4)
        frame.pack(padx=10, side=tk.TOP, fill=tk.X, expand=True)
        return frame

    def set_capture_shortcuts_entry(self) -> ttk.Entry:
        tip = tk.Label(self.shortcuts_labelframe, text="启动截图:", font=Style.head2)
        tip.grid(row=0, column=0, ipady=5, pady=5)
        capture_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe, state="readonly")
        capture_shortcuts_entry.grid(row=0, column=1, sticky=tk.EW, ipady=5, pady=5, padx=(0, 10))
        self.shortcuts_labelframe.columnconfigure(1, weight=1)
        return capture_shortcuts_entry
    
    def set_capture_entry_edit_btn(self) -> FlatButton:
        edit_btn = FlatButton(self.shortcuts_labelframe, text="编辑")
        edit_btn.grid(row=0, column=2, sticky=tk.E, pady=15, ipady=5, padx=(0, 10))
        return edit_btn

    def set_call_shortcuts_entry(self) -> ttk.Entry:
        tip = tk.Label(self.shortcuts_labelframe, text="唤起窗口:", font=Style.head2)
        tip.grid(row=1, column=0, sticky=tk.W, pady=15, ipady=5)
        call_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe, state="readonly")
        call_shortcuts_entry.grid(row=1, column=1, sticky=tk.EW, ipady=5, padx=(0, 10))
        self.shortcuts_labelframe.columnconfigure(1, weight=1)
        return call_shortcuts_entry
    
    def set_call_entry_edit_btn(self) -> FlatButton:
        edit_btn = FlatButton(self.shortcuts_labelframe, text="编辑")
        edit_btn.grid(row=1, column=2, sticky=tk.E, pady=15, ipady=5, padx=(0, 10))
        return edit_btn
    
    def set_exit_shortcuts_entry(self) -> ttk.Entry:
        tip = tk.Label(self.shortcuts_labelframe, text="确定裁剪:", font=Style.head2)
        tip.grid(row=2, column=0, sticky=tk.W, pady=15, ipady=5)
        exit_shortcuts_entry = ttk.Entry(self.shortcuts_labelframe, state="readonly")
        exit_shortcuts_entry.grid(row=2, column=1, sticky=tk.EW, ipady=5, padx=(0, 10))
        self.shortcuts_labelframe.columnconfigure(1, weight=1)
        return exit_shortcuts_entry
    
    def set_exit_entry_edit_btn(self) -> FlatButton:
        edit_btn = FlatButton(self.shortcuts_labelframe, text="编辑")
        edit_btn.grid(row=2, column=2, sticky=tk.E, pady=15, ipady=5, padx=(0, 10))
        return edit_btn
    
    def set_auto_copy_checkbox(self) -> tk.BooleanVar:
        tip_label = tk.Label(self.auto_operation_labelframe, text="自动复制截图", font=Style.head2)
        tip_label.grid(row=0, column=0, sticky=tk.W, ipady=5)
        auto_copy_var = tk.BooleanVar(value=True)
        chekc_btn = ttk.Checkbutton(self.auto_operation_labelframe, variable=auto_copy_var)
        chekc_btn.grid(row=0, column=1)
        return auto_copy_var

    def set_auto_save_checkbox(self) -> tk.BooleanVar:
        tip_label = tk.Label(self.auto_operation_labelframe, text="自动保存截图", font=Style.head2)
        tip_label.grid(row=1, column=0, sticky=tk.W, ipady=5, pady=(15, 0))
        auto_save_var = tk.BooleanVar(value=True)
        check_btn = ttk.Checkbutton(self.auto_operation_labelframe, variable=auto_save_var)
        check_btn.grid(row=1, column=1, pady=(15, 0))
        return auto_save_var

    def set_auto_save_path_entry(self) -> ttk.Entry:
        auto_save_path_entry = ttk.Entry(self.auto_operation_labelframe)
        auto_save_path_entry.grid(row=4, column=0, sticky=tk.W + tk.E, pady=5, ipady=5, padx=5)
        auto_save_path_entry.config(state="readonly")
        self.auto_operation_labelframe.columnconfigure(0, weight=1)
        self.auto_operation_labelframe.columnconfigure(1, weight=0)
        return auto_save_path_entry
    
    def set_auto_delete_checkbox(self) -> tk.BooleanVar:
        tip_label = tk.Label(self.auto_operation_labelframe, text="自动删除截图", font=Style.head2)
        tip_label.grid(row=5, column=0, sticky=tk.W, ipady=5, pady=(25, 0))
        auto_delete_var = tk.BooleanVar(value=True)
        check_btn = ttk.Checkbutton(self.auto_operation_labelframe, variable=auto_delete_var)
        check_btn.grid(row=5, column=1, pady=(25, 0))
        return auto_delete_var
    
    def set_auto_delete_spinbox(self) -> ttk.Spinbox:
        tip_label = tk.Label(self.auto_operation_labelframe, text="截图数上限, 超过自动删首图", font=Style.head3)
        tip_label.grid(row=6, column=0, sticky=tk.W, pady=0)
        auto_delete_spinbox = tk.Spinbox(
            self.auto_operation_labelframe, values=list(range(3, 31)), width=2,
            state="readonly", bd=0
        )
        auto_delete_spinbox.grid(row=6, column=1, pady=0)
        return auto_delete_spinbox
    
    def set_browse_auto_save_path_btn(self) -> FlatButton:
        browse_btn = FlatButton(self.auto_operation_labelframe, text="更改")
        browse_btn.grid(row=4, column=1, sticky=tk.E, pady=(5, 10), ipady=5)
        return browse_btn
    
    def set_open_auto_save_path_btn(self) -> FlatButton:
        open_btn = FlatButton(self.auto_operation_labelframe, text="打开")
        open_btn.grid(row=4, column=2, sticky=tk.E, pady=(5, 10), ipady=5)
        return open_btn
    
    def update_parent_attr(self) -> tuple[int, int]:
        window_width, window_height = self.parent.geometry().split("x")
        window_height = window_height.split("+")[0]
        setting_window_height = WINDOW_HEIGHT * 8 if int(window_height) < WINDOW_HEIGHT * 8 else window_height
        self.parent.geometry(f"{window_width}x{setting_window_height}")
        self.parent.unbind_keyboard_event()
        style = Style()
        style.set_checkbox_style()
        return int(window_width), int(window_height)
    
    def update_scrollbar(self):
        self.basic_frame.update()
        self.basic_canvas.configure(scrollregion=self.basic_canvas.bbox("all"))
