import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import subprocess
import pyautogui
import cv2
import numpy as np
from threading import Thread
import pyperclip
import json
from abc import ABC, abstractmethod
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)

# 必须用 SendInput 结构体（MuMu 只吃这个）
class MOUSEINPUT(ctypes.Structure): _fields_ = []
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]
class HARDWAREINPUT(ctypes.Structure): _fields_ = []

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ki", KEYBDINPUT),
                ("padding", ctypes.c_byte * 8)]

INPUT_KEYBOARD = 1
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

# 扫描码（MuMu 实测有效）
SCAN_CODES = {
    'a': 0x1E, 'b':0x30, 'c':0x2E, 'd':0x20, 'e':0x12, 'f':0x21, 'g':0x22,
    'h':0x23, 'i':0x17, 'j':0x24, 'k':0x25, 'l':0x26, 'm':0x32, 'n':0x31,
    'o':0x18, 'p':0x19, 'q':0x10, 'r':0x13, 's':0x1F, 't':0x14, 'u':0x16,
    'v':0x2F, 'w':0x11, 'x':0x2D, 'y':0x15, 'z':0x2C,
    '0':0x0B, '1':0x02, '2':0x03, '3':0x04, '4':0x05, '5':0x06,
    '6':0x07, '7':0x08, '8':0x09, '9':0x0A, '`': 0x29,
    'enter':0x1C, 'space':0x39, 'esc':0x01, 'backspace':0x0E,
    'shift':0x2A, 'ctrl':0x1D, 'alt':0x38,
    'up':0x48, 'down':0x50, 'left':0x4B, 'right':0x4D
}

# 真正底层按下/释放
def send_key_scan(scan, press):
    extra = ctypes.c_ulong(0)
    flags = KEYEVENTF_SCANCODE
    if not press:
        flags |= KEYEVENTF_KEYUP
    ki = KEYBDINPUT(0, scan, flags, 0, ctypes.pointer(extra))
    inp = INPUT(INPUT_KEYBOARD, ki)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


class BaseStep(ABC):
    def __init__(self, step_type, name="新步骤"):
        self.step_type = step_type
        self.name = name
        self.delay = 0
        self.enabled = True  # 步骤启用状态
        self.execution = "单次执行"  # 执行方式：单次执行，多次执行，持续执行
        self.execution_count = 1  # 执行次数
        self.execution_interval = 1000  # 执行间隔(ms)
        self.duration = 1  # 持续时间
        self.duration_unit = "分钟"  # 持续时间单位
        self.continuous_interval = 1000  # 持续执行间隔(ms)
        self.stop_on_success = True  # 成功执行一次后停止
        self.stop_on_error = False  # 全错时停止执行
    
    @abstractmethod
    def execute(self, app):
        """执行步骤功能"""
        pass

class ProgramStep(BaseStep):
    def __init__(self, name="程序运行"):
        super().__init__("program", name)
        self.program_path = ""  # 程序路径
    
    def execute(self, app):
        if not self.program_path:
            app.log("请选择程序路径", level="错误")
            return False
        
        try:
            app.log(f"启动程序：{self.program_path}")
            subprocess.Popen(self.program_path)
            app.log("程序启动成功")
            return True
        except Exception as e:
            app.log(f"程序启动失败：{str(e)}", level="错误")
            return False

class TextInputStep(BaseStep):
    def __init__(self, name="文本输入"):
        super().__init__("text_input", name)
        self.text = ""  # 输入文本
    
    def execute(self, app):
        if not self.text:
            app.log("请输入文本", level="错误")
            return False
        
        try:
            app.log(f"输入文本：{self.text}")
            # 将文本复制到剪贴板
            pyperclip.copy(self.text)
            # 等待一小段时间
            time.sleep(0.1)
            # 使用快捷键粘贴文本
            pyautogui.hotkey('ctrl', 'v')
            app.log("文本输入成功")
            return True
        except Exception as e:
            app.log(f"文本输入失败：{str(e)}", level="错误")
            return False

class KeyInputStep(BaseStep):
    def __init__(self, name="按键输入"):
        super().__init__("key_input", name)
        self.keys = ""

    def execute(self, app):
        if not self.keys:
            app.log("请输入按键", level="错误")
            return False

        try:
            key_sequence = self.keys.strip().lower()
            app.log(f"底层按键输入：{key_sequence}")

            if "+" in key_sequence:
                keys = key_sequence.split("+")
                # 按下
                for k in keys:
                    scan = SCAN_CODES.get(k)
                    if scan:
                        send_key_scan(scan, True)
                        time.sleep(0.03)
                time.sleep(0.05)
                # 释放
                for k in reversed(keys):
                    scan = SCAN_CODES.get(k)
                    if scan:
                        send_key_scan(scan, False)
                        time.sleep(0.03)
                app.log(f"组合按键 {key_sequence} 完成")
            else:
                scan = SCAN_CODES.get(key_sequence)
                if not scan:
                    app.log(f"不支持按键：{key_sequence}", level="错误")
                    return False
                send_key_scan(scan, True)
                time.sleep(0.05)
                send_key_scan(scan, False)
                app.log(f"按键 {key_sequence} 完成")

            return True

        except Exception as e:
            app.log(f"按键失败：{e}", level="错误")
            return False

class ImageRecognitionStep(BaseStep):
    def __init__(self, name="图像识别"):
        super().__init__("image_recognition", name)
        self.image_path = ""  # 图片路径
        self.fuzzy = True  # 是否支持模糊识别
        self.region = "全屏"  # 识别区域
        self.region_x = 0  # 自定义区域X坐标
        self.region_y = 0  # 自定义区域Y坐标
        self.region_width = 1920  # 自定义区域宽度
        self.region_height = 1080  # 自定义区域高度
        self.accuracy = 0.8  # 识别精度
        self.click_type = "左键单击"  # 点击方式
        self.mouse_speed = 0.5  # 鼠标速度
        self.click_offset_x = 0  # 点击偏移X
        self.click_offset_y = 0  # 点击偏移Y
    
    def execute(self, app):
        if not self.image_path:
            app.log("请选择图片路径", level="错误")
            return False
        
        try:
            target = cv2.imread(self.image_path)
            if target is None:
                app.log("图片加载失败", level="错误")
                return False
            
            if self.region == "全屏":
                screenshot = pyautogui.screenshot()
            else:
                screenshot = pyautogui.screenshot(region=(self.region_x, self.region_y, self.region_width, self.region_height))
            
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            if self.fuzzy:
                # 使用边缘检测进行模糊匹配
                screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
                
                # 边缘检测
                screenshot_edges = cv2.Canny(screenshot_gray, 100, 200)
                target_edges = cv2.Canny(target_gray, 100, 200)
                
                # 模板匹配
                result = cv2.matchTemplate(screenshot_edges, target_edges, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            else:
                # 常规模板匹配
                method = cv2.TM_CCORR_NORMED
                result = cv2.matchTemplate(screenshot, target, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val < self.accuracy:
                app.log(f"未找到匹配图片，相似度：{max_val:.2f}", level="错误")
                return False
            
            h, w = target.shape[:2]
            if self.region == "全屏":
                center_x = max_loc[0] + w // 2 + self.click_offset_x
                center_y = max_loc[1] + h // 2 + self.click_offset_y
            else:
                center_x = self.region_x + max_loc[0] + w // 2 + self.click_offset_x
                center_y = self.region_y + max_loc[1] + h // 2 + self.click_offset_y
            
            pyautogui.moveTo(center_x, center_y, duration=self.mouse_speed)
            
            if self.click_type == "左键单击":
                pyautogui.click()
            elif self.click_type == "左键双击":
                pyautogui.doubleClick()
            elif self.click_type == "右键单击":
                pyautogui.rightClick()
            
            app.log(f"成功点击位置：({center_x}, {center_y})，相似度：{max_val:.2f}")
            return True
        except Exception as e:
            app.log(f"图片识别失败：{str(e)}", level="错误")
            return False


class GameAutoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏自动化工具")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        style = ttk.Style()
        style.configure("TNotebook", padding=5)
        style.configure("TFrame", padding=10)
        style.configure("TLabelFrame", padding=10)
        
        # 添加选中步骤的样式
        style.configure("Selected.TLabel", foreground="#0066cc", font=("Arial", 10, "bold"))
        style.configure("TLabel", foreground="#333333")
        
        self.steps = []
        self.current_step_index = None
        self.running = False
        self.log_level = "信息"  # 全局日志级别
        
        # 存储步骤项的引用，用于高效更新
        self.step_items = []
        
        # 创建菜单栏
        self.create_menu()
        
        self.create_main_ui()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 操作菜单
        operation_menu = tk.Menu(menubar, tearoff=0)
        operation_menu.add_command(label="导出配置", command=self.export_config)
        operation_menu.add_command(label="导入配置", command=self.import_config)
        menubar.add_cascade(label="导入/导出", menu=operation_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_ui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        step_list_frame = ttk.LabelFrame(left_frame, text="步骤列表")
        step_list_frame.pack(fill=tk.BOTH, expand=True)
        
        toolbar = ttk.Frame(step_list_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="添加程序运行", command=lambda: self.add_step(ProgramStep())).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="添加文本输入", command=lambda: self.add_step(TextInputStep())).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="添加按键输入", command=lambda: self.add_step(KeyInputStep())).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="添加图像识别", command=lambda: self.add_step(ImageRecognitionStep())).pack(side=tk.LEFT, padx=2)
        # ttk.Button(toolbar, text="添加点击+文本", command=lambda: self.add_step(ImageClickTextStep())).pack(side=tk.LEFT, padx=2)
        
        # 添加滚动功能
        self.steps_canvas = tk.Canvas(step_list_frame)
        self.steps_scrollbar = ttk.Scrollbar(step_list_frame, orient="vertical", command=self.steps_canvas.yview)
        self.steps_container = ttk.Frame(self.steps_canvas)
        
        self.steps_container.bind(
            "<Configure>",
            lambda e: self.steps_canvas.configure(scrollregion=self.steps_canvas.bbox("all"))
        )
        
        # 添加鼠标滚轮支持
        self.steps_canvas.bind("<MouseWheel>", lambda e: self.steps_canvas.yview_scroll(int(-e.delta/120), "units"))
        
        self.steps_canvas.create_window((0, 0), window=self.steps_container, anchor="nw")
        self.steps_canvas.configure(yscrollcommand=self.steps_scrollbar.set)
        
        self.steps_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.steps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.step_config_frame = ttk.LabelFrame(right_frame, text="步骤配置")
        self.step_config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 步骤保存按钮
        config_toolbar = ttk.Frame(self.step_config_frame)
        config_toolbar.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(config_toolbar, text="保存步骤配置", command=self.save_step_config).pack(side=tk.LEFT, padx=2)
        
        self.canvas = tk.Canvas(self.step_config_frame)
        self.scrollbar = ttk.Scrollbar(self.step_config_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.create_step_config_ui()
        
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 全局日志设置
        log_frame = ttk.Frame(control_frame)
        log_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(log_frame, text="日志级别：").pack(side=tk.LEFT, padx=5)
        self.log_level_var = tk.StringVar(value=self.log_level)
        log_options = ["静默", "错误", "信息", "详细"]
        ttk.Combobox(log_frame, textvariable=self.log_level_var, values=log_options, state="readonly", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_frame, text="应用", command=self.save_log_level).pack(side=tk.LEFT, padx=5)
        
        self.start_button = ttk.Button(control_frame, text="开始执行", command=self.start_execution)
        self.start_button.pack(side=tk.LEFT, padx=10)
        self.stop_button = ttk.Button(control_frame, text="停止执行", command=self.stop_execution, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # 添加上移下移按钮
        ttk.Button(control_frame, text="上移", command=self.move_step_up).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="下移", command=self.move_step_down).pack(side=tk.LEFT, padx=10)
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(control_frame, textvariable=self.status_var, font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=10)
        
        self.update_step_config_ui()
    
    def create_step_config_ui(self):
        # 步骤基本设置
        name_frame = ttk.LabelFrame(self.scrollable_frame, text="步骤基本设置")
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 名称设置
        name_row = ttk.Frame(name_frame)
        name_row.pack(fill=tk.X, pady=5)
        ttk.Label(name_row, text="名称：").pack(side=tk.LEFT, padx=5)
        self.step_name_var = tk.StringVar()
        ttk.Entry(name_row, textvariable=self.step_name_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 全错时停止执行设置
        error_stop_row = ttk.Frame(name_frame)
        error_stop_row.pack(fill=tk.X, pady=5)
        ttk.Label(error_stop_row, text="全错时停止执行：").pack(side=tk.LEFT, padx=5)
        self.stop_on_error_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(error_stop_row, variable=self.stop_on_error_var).pack(side=tk.LEFT, padx=5)
        
        delay_frame = ttk.LabelFrame(self.scrollable_frame, text="延迟执行")
        delay_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(delay_frame, text="延迟执行 (ms)：").pack(side=tk.LEFT, padx=5, pady=5)
        self.delay_var = tk.StringVar(value="0")
        ttk.Entry(delay_frame, textvariable=self.delay_var).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 执行设置
        execution_frame = ttk.LabelFrame(self.scrollable_frame, text="执行设置")
        execution_frame.pack(fill=tk.X, padx=10, pady=5)
        
        exec_type_frame = ttk.Frame(execution_frame)
        exec_type_frame.pack(fill=tk.X, pady=2)
        ttk.Label(exec_type_frame, text="执行方式：").pack(side=tk.LEFT, padx=5)
        self.execution_var = tk.StringVar(value="单次执行")
        execution_options = ["单次执行", "多次执行", "持续执行"]
        self.execution_combobox = ttk.Combobox(exec_type_frame, textvariable=self.execution_var, values=execution_options, state="readonly", width=10)
        self.execution_combobox.pack(side=tk.LEFT, padx=5)
        self.execution_combobox.bind("<<ComboboxSelected>>", self.on_execution_change)
        
        self.multiple_execution_frame = ttk.Frame(execution_frame)
        ttk.Label(self.multiple_execution_frame, text="执行次数：").pack(side=tk.LEFT, padx=5)
        self.execution_count_var = tk.StringVar(value="1")
        ttk.Entry(self.multiple_execution_frame, textvariable=self.execution_count_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.multiple_execution_frame, text="间隔(ms)：").pack(side=tk.LEFT, padx=5)
        self.execution_interval_var = tk.StringVar(value="1000")
        ttk.Entry(self.multiple_execution_frame, textvariable=self.execution_interval_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.multiple_execution_frame, text="成功后停止：").pack(side=tk.LEFT, padx=5)
        self.stop_on_success_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.multiple_execution_frame, variable=self.stop_on_success_var).pack(side=tk.LEFT, padx=5)
        
        self.continuous_execution_frame = ttk.Frame(execution_frame)
        ttk.Label(self.continuous_execution_frame, text="持续时间：").pack(side=tk.LEFT, padx=5)
        self.duration_var = tk.StringVar(value="1")
        ttk.Entry(self.continuous_execution_frame, textvariable=self.duration_var, width=8).pack(side=tk.LEFT, padx=5)
        self.duration_unit_var = tk.StringVar(value="分钟")
        duration_options = ["秒", "分钟"]
        ttk.Combobox(self.continuous_execution_frame, textvariable=self.duration_unit_var, values=duration_options, state="readonly", width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.continuous_execution_frame, text="间隔(ms)：").pack(side=tk.LEFT, padx=5)
        self.continuous_interval_var = tk.StringVar(value="1000")
        ttk.Entry(self.continuous_execution_frame, textvariable=self.continuous_interval_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.continuous_execution_frame, text="成功后停止：").pack(side=tk.LEFT, padx=5)
        self.stop_on_success_continuous_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.continuous_execution_frame, variable=self.stop_on_success_continuous_var).pack(side=tk.LEFT, padx=5)
        
        # 程序运行设置
        self.program_frame = ttk.LabelFrame(self.scrollable_frame, text="程序运行设置")
        ttk.Label(self.program_frame, text="程序路径：").pack(side=tk.LEFT, padx=5, pady=5)
        self.program_path_var = tk.StringVar()
        ttk.Entry(self.program_frame, textvariable=self.program_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        ttk.Button(self.program_frame, text="浏览", command=self.browse_program).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 文本输入设置
        self.text_frame = ttk.LabelFrame(self.scrollable_frame, text="文本输入设置")
        ttk.Label(self.text_frame, text="输入文本：").pack(side=tk.LEFT, padx=5, pady=5)
        self.text_var = tk.StringVar()
        ttk.Entry(self.text_frame, textvariable=self.text_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # 按键输入设置
        self.key_frame = ttk.LabelFrame(self.scrollable_frame, text="按键输入设置")
        ttk.Label(self.key_frame, text="按键序列：").pack(side=tk.LEFT, padx=5, pady=5)
        self.keys_var = tk.StringVar()
        ttk.Entry(self.key_frame, textvariable=self.keys_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # 图片识别设置
        self.image_frame = ttk.LabelFrame(self.scrollable_frame, text="图片识别设置")
        
        image_path_frame = ttk.Frame(self.image_frame)
        image_path_frame.pack(fill=tk.X, pady=2)
        ttk.Label(image_path_frame, text="图片路径：").pack(side=tk.LEFT, padx=5)
        self.image_path_var = tk.StringVar()
        ttk.Entry(image_path_frame, textvariable=self.image_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(image_path_frame, text="浏览", command=self.browse_image).pack(side=tk.LEFT, padx=5)
        
        fuzzy_frame = ttk.Frame(self.image_frame)
        fuzzy_frame.pack(fill=tk.X, pady=2)
        ttk.Label(fuzzy_frame, text="模糊识别：").pack(side=tk.LEFT, padx=5)
        self.fuzzy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(fuzzy_frame, variable=self.fuzzy_var).pack(side=tk.LEFT, padx=5)
        
        region_frame = ttk.Frame(self.image_frame)
        region_frame.pack(fill=tk.X, pady=2)
        ttk.Label(region_frame, text="屏幕区域：").pack(side=tk.LEFT, padx=5)
        self.region_var = tk.StringVar(value="全屏")
        region_options = ["全屏", "自定义区域"]
        self.region_combobox = ttk.Combobox(region_frame, textvariable=self.region_var, values=region_options, state="readonly", width=10)
        self.region_combobox.pack(side=tk.LEFT, padx=5)
        self.region_combobox.bind("<<ComboboxSelected>>", self.on_region_change)
        
        self.custom_region_frame = ttk.Frame(self.image_frame)
        ttk.Label(self.custom_region_frame, text="X：").pack(side=tk.LEFT, padx=2)
        self.region_x_var = tk.StringVar(value="0")
        ttk.Entry(self.custom_region_frame, textvariable=self.region_x_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.custom_region_frame, text="Y：").pack(side=tk.LEFT, padx=2)
        self.region_y_var = tk.StringVar(value="0")
        ttk.Entry(self.custom_region_frame, textvariable=self.region_y_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.custom_region_frame, text="宽：").pack(side=tk.LEFT, padx=2)
        self.region_width_var = tk.StringVar(value="1920")
        ttk.Entry(self.custom_region_frame, textvariable=self.region_width_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.custom_region_frame, text="高：").pack(side=tk.LEFT, padx=2)
        self.region_height_var = tk.StringVar(value="1080")
        ttk.Entry(self.custom_region_frame, textvariable=self.region_height_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # 高级设置
        self.advanced_frame = ttk.LabelFrame(self.scrollable_frame, text="高级设置")
        
        accuracy_frame = ttk.Frame(self.advanced_frame)
        accuracy_frame.pack(fill=tk.X, pady=2)
        ttk.Label(accuracy_frame, text="识别精度：").pack(side=tk.LEFT, padx=5)
        self.accuracy_var = tk.StringVar(value="0.8")
        ttk.Entry(accuracy_frame, textvariable=self.accuracy_var, width=8).pack(side=tk.LEFT, padx=5)
        
        click_frame = ttk.Frame(self.advanced_frame)
        click_frame.pack(fill=tk.X, pady=2)
        ttk.Label(click_frame, text="点击方式：").pack(side=tk.LEFT, padx=5)
        self.click_type_var = tk.StringVar(value="左键单击")
        click_options = ["左键单击", "左键双击", "右键单击"]
        ttk.Combobox(click_frame, textvariable=self.click_type_var, values=click_options, state="readonly", width=10).pack(side=tk.LEFT, padx=5)
        
        speed_frame = ttk.Frame(self.advanced_frame)
        speed_frame.pack(fill=tk.X, pady=2)
        ttk.Label(speed_frame, text="鼠标速度：").pack(side=tk.LEFT, padx=5)
        self.mouse_speed_var = tk.StringVar(value="0.5")
        ttk.Entry(speed_frame, textvariable=self.mouse_speed_var, width=8).pack(side=tk.LEFT, padx=5)
        
        offset_frame = ttk.Frame(self.advanced_frame)
        offset_frame.pack(fill=tk.X, pady=2)
        ttk.Label(offset_frame, text="点击偏移：").pack(side=tk.LEFT, padx=5)
        ttk.Label(offset_frame, text="X：").pack(side=tk.LEFT, padx=2)
        self.click_offset_x_var = tk.StringVar(value="0")
        ttk.Entry(offset_frame, textvariable=self.click_offset_x_var, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(offset_frame, text="Y：").pack(side=tk.LEFT, padx=2)
        self.click_offset_y_var = tk.StringVar(value="0")
        ttk.Entry(offset_frame, textvariable=self.click_offset_y_var, width=6).pack(side=tk.LEFT, padx=2)
    
    def add_step(self, step):
        self.steps.append(step)
        self.update_step_list()
        self.select_step(len(self.steps) - 1)
    
    def update_step_list(self):
        # 清空容器
        for widget in self.steps_container.winfo_children():
            widget.destroy()
        
        # 清空步骤项引用
        self.step_items = []
        
        # 重新创建步骤项
        for i, step in enumerate(self.steps):
            step_frame = ttk.Frame(self.steps_container)
            step_frame.pack(fill=tk.X, pady=2)
            
            # 启用/停用复选框
            var = tk.BooleanVar(value=step.enabled)
            def on_toggle(*args, idx=i, v=var):
                self.steps[idx].enabled = v.get()
                # 只更新当前步骤的状态，不重建整个列表
                if idx < len(self.step_items):
                    # 这里可以添加更细粒度的更新，目前保持简单
                    pass
            var.trace_add("write", on_toggle)
            checkbutton = ttk.Checkbutton(step_frame, variable=var)
            checkbutton.pack(side=tk.LEFT, padx=5)
            
            # 步骤名称，点击可选择
            label = ttk.Label(step_frame, text=f"{i + 1}. {step.name}", cursor="hand2")
            label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            label.bind("<Button-1>", lambda e, idx=i: self.select_step(idx))
            
            # 操作按钮
            button_frame = ttk.Frame(step_frame)
            button_frame.pack(side=tk.RIGHT, padx=5)
            
            # 单独执行按钮
            execute_btn = ttk.Button(button_frame, text="执行", width=5, command=lambda idx=i: self.execute_single_step_by_index(idx))
            execute_btn.pack(side=tk.LEFT, padx=2)
            
            # 删除按钮
            delete_btn = ttk.Button(button_frame, text="删除", width=5, command=lambda idx=i: self.delete_step_by_index(idx))
            delete_btn.pack(side=tk.LEFT, padx=2)
            
            # 选中指示灯
            indicator = ttk.Label(step_frame, width=2)
            if i == self.current_step_index:
                indicator.config(background="#4CAF50", relief="solid", borderwidth=1)
            else:
                indicator.config(background="#E0E0E0", relief="solid", borderwidth=1)
            indicator.pack(side=tk.RIGHT, padx=5)
            
            # 存储步骤项引用
            self.step_items.append((step_frame, indicator, label, checkbutton))
    
    def select_step(self, index):
        # 保存之前的选中索引
        prev_index = self.current_step_index
        self.current_step_index = index
        
        # 只更新指示灯状态，不重建整个列表
        if self.step_items:
            # 更新之前选中的步骤指示灯
            if prev_index is not None and prev_index < len(self.step_items):
                _, indicator, _, _ = self.step_items[prev_index]
                indicator.config(background="#E0E0E0")
            
            # 更新当前选中的步骤指示灯
            if index < len(self.step_items):
                _, indicator, _, _ = self.step_items[index]
                indicator.config(background="#4CAF50")
        else:
            # 如果步骤项引用为空，重建整个列表
            self.update_step_list()
        
        self.load_step_to_ui()
    
    def load_step_to_ui(self):
        if self.current_step_index is None or self.current_step_index >= len(self.steps):
            self.update_step_config_ui()
            return
        
        step = self.steps[self.current_step_index]
        
        # 加载基本设置
        self.step_name_var.set(step.name)
        self.delay_var.set(str(step.delay))
        self.execution_var.set(step.execution)
        self.execution_count_var.set(str(step.execution_count))
        self.execution_interval_var.set(str(step.execution_interval))
        self.duration_var.set(str(step.duration))
        self.duration_unit_var.set(step.duration_unit)
        self.continuous_interval_var.set(str(step.continuous_interval))
        self.stop_on_success_var.set(step.stop_on_success)
        self.stop_on_success_continuous_var.set(step.stop_on_success)
        self.stop_on_error_var.set(step.stop_on_error)
        
        # 加载程序运行设置
        if hasattr(step, 'program_path'):
            self.program_path_var.set(step.program_path)
        else:
            self.program_path_var.set("")
        
        # 加载文本输入设置
        if hasattr(step, 'text'):
            self.text_var.set(step.text)
        else:
            self.text_var.set("")
        
        # 加载按键输入设置
        if hasattr(step, 'keys'):
            self.keys_var.set(step.keys)
        else:
            self.keys_var.set("")
        
        # 加载图片识别设置
        if hasattr(step, 'image_path'):
            self.image_path_var.set(step.image_path)
            self.fuzzy_var.set(step.fuzzy)
            self.region_var.set(step.region)
            self.region_x_var.set(str(step.region_x))
            self.region_y_var.set(str(step.region_y))
            self.region_width_var.set(str(step.region_width))
            self.region_height_var.set(str(step.region_height))
            self.accuracy_var.set(str(step.accuracy))
            self.click_type_var.set(step.click_type)
            self.mouse_speed_var.set(str(step.mouse_speed))
            self.click_offset_x_var.set(str(step.click_offset_x))
            self.click_offset_y_var.set(str(step.click_offset_y))
        else:
            self.image_path_var.set("")
            self.fuzzy_var.set(True)
            self.region_var.set("全屏")
            self.region_x_var.set("0")
            self.region_y_var.set("0")
            self.region_width_var.set("1920")
            self.region_height_var.set("1080")
            self.accuracy_var.set("0.8")
            self.click_type_var.set("左键单击")
            self.mouse_speed_var.set("0.5")
            self.click_offset_x_var.set("0")
            self.click_offset_y_var.set("0")
        
        self.update_step_config_ui()
    
    def update_step_config_ui(self):
        if self.current_step_index is None or self.current_step_index >= len(self.steps):
            # 隐藏所有面板
            self.program_frame.pack_forget()
            self.text_frame.pack_forget()
            self.key_frame.pack_forget()
            self.image_frame.pack_forget()
            self.advanced_frame.pack_forget()
            self.multiple_execution_frame.pack_forget()
            self.continuous_execution_frame.pack_forget()
            return
        
        step = self.steps[self.current_step_index]
        
        # 隐藏所有面板
        self.program_frame.pack_forget()
        self.text_frame.pack_forget()
        self.key_frame.pack_forget()
        self.image_frame.pack_forget()
        self.advanced_frame.pack_forget()
        self.multiple_execution_frame.pack_forget()
        self.continuous_execution_frame.pack_forget()
        
        # 根据步骤类型显示相应的面板
        if step.step_type == "program":
            self.program_frame.pack(fill=tk.X, padx=10, pady=5)
        elif step.step_type == "text_input":
            self.text_frame.pack(fill=tk.X, padx=10, pady=5)
        elif step.step_type == "key_input":
            self.key_frame.pack(fill=tk.X, padx=10, pady=5)
        elif step.step_type == "image_recognition":
            self.image_frame.pack(fill=tk.X, padx=10, pady=5)
            self.advanced_frame.pack(fill=tk.X, padx=10, pady=5)
        elif step.step_type == "image_click_text":
            self.image_frame.pack(fill=tk.X, padx=10, pady=5)
            self.text_frame.pack(fill=tk.X, padx=10, pady=5)
            self.advanced_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 根据执行方式显示相应的面板
        self.on_execution_change(None)
        # 根据区域设置显示相应的面板
        self.on_region_change(None)
    
    def on_execution_change(self, event):
        execution = self.execution_var.get()
        self.multiple_execution_frame.pack_forget()
        self.continuous_execution_frame.pack_forget()
        
        if execution == "多次执行":
            self.multiple_execution_frame.pack(fill=tk.X, pady=2)
        elif execution == "持续执行":
            self.continuous_execution_frame.pack(fill=tk.X, pady=2)
    
    def on_region_change(self, event):
        if self.region_var.get() == "自定义区域":
            self.custom_region_frame.pack(fill=tk.X, pady=2)
        else:
            self.custom_region_frame.pack_forget()
    
    def save_step_config(self):
        """保存当前步骤的所有配置"""
        if self.current_step_index is not None:
            step = self.steps[self.current_step_index]
            
            # 保存基本设置
            step.name = self.step_name_var.get()
            try:
                step.delay = int(self.delay_var.get())
            except ValueError:
                step.delay = 0
            
            # 保存执行设置
            step.execution = self.execution_var.get()
            try:
                step.execution_count = int(self.execution_count_var.get())
                step.execution_interval = int(self.execution_interval_var.get())
                step.duration = float(self.duration_var.get())
                step.continuous_interval = int(self.continuous_interval_var.get())
            except ValueError:
                pass
            step.duration_unit = self.duration_unit_var.get()
            step.stop_on_success = self.stop_on_success_var.get() if step.execution == "多次执行" else self.stop_on_success_continuous_var.get()
            step.stop_on_error = self.stop_on_error_var.get()
            
            # 保存程序运行设置
            if hasattr(step, 'program_path'):
                step.program_path = self.program_path_var.get()
            
            # 保存文本输入设置
            if hasattr(step, 'text'):
                step.text = self.text_var.get()
            
            # 保存按键输入设置
            if hasattr(step, 'keys'):
                step.keys = self.keys_var.get()
            
            # 保存图片识别设置
            if hasattr(step, 'image_path'):
                step.image_path = self.image_path_var.get()
                step.fuzzy = self.fuzzy_var.get()
                step.region = self.region_var.get()
                try:
                    step.region_x = int(self.region_x_var.get())
                    step.region_y = int(self.region_y_var.get())
                    step.region_width = int(self.region_width_var.get())
                    step.region_height = int(self.region_height_var.get())
                    step.accuracy = float(self.accuracy_var.get())
                    step.mouse_speed = float(self.mouse_speed_var.get())
                    step.click_offset_x = int(self.click_offset_x_var.get())
                    step.click_offset_y = int(self.click_offset_y_var.get())
                except ValueError:
                    pass
                step.click_type = self.click_type_var.get()
            
            # 更新步骤列表
            self.update_step_list()
            messagebox.showinfo("成功", "步骤配置已保存")
    
    def delete_step(self):
        if self.current_step_index is not None and self.current_step_index < len(self.steps):
            del self.steps[self.current_step_index]
            self.current_step_index = None
            self.update_step_list()
            self.update_step_config_ui()
    
    def delete_step_by_index(self, index):
        if 0 <= index < len(self.steps):
            del self.steps[index]
            if self.current_step_index == index:
                self.current_step_index = None
                self.update_step_config_ui()
            elif self.current_step_index > index:
                self.current_step_index -= 1
            self.update_step_list()
    
    def move_step_up(self):
        if self.current_step_index is not None and self.current_step_index > 0:
            self.steps[self.current_step_index], self.steps[self.current_step_index - 1] = \
                self.steps[self.current_step_index - 1], self.steps[self.current_step_index]
            self.current_step_index -= 1
            self.update_step_list()
            self.select_step(self.current_step_index)
    
    def move_step_down(self):
        if self.current_step_index is not None and self.current_step_index < len(self.steps) - 1:
            self.steps[self.current_step_index], self.steps[self.current_step_index + 1] = \
                self.steps[self.current_step_index + 1], self.steps[self.current_step_index]
            self.current_step_index += 1
            self.update_step_list()
            self.select_step(self.current_step_index)
    
    def execute_single_step(self):
        if self.current_step_index is None or self.current_step_index >= len(self.steps):
            messagebox.showwarning("警告", "请先选择一个步骤")
            return
        
        if self.running:
            return
        
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("执行中...")
        
        thread = Thread(target=self.execute_single_step_thread)
        thread.daemon = True
        thread.start()
    
    def execute_single_step_by_index(self, index):
        if 0 <= index < len(self.steps):
            self.current_step_index = index
            self.execute_single_step()
    
    def execute_single_step_thread(self):
        try:
            step = self.steps[self.current_step_index]
            self.status_var.set(f"执行步骤：{step.name}")
            
            if step.delay > 0:
                self.log(f"步骤：延迟 {step.delay} ms 执行")
                time.sleep(step.delay / 1000)
            
            # 处理执行方式
            if step.execution == "单次执行":
                step.execute(self)
            elif step.execution == "多次执行":
                count = 0
                while count < step.execution_count and self.running:
                    success = step.execute(self)
                    
                    # 如果成功且设置了成功后停止，则退出循环
                    if success and step.stop_on_success:
                        break
                    
                    count += 1
                    
                    # 如果不是最后一次执行，添加间隔
                    if count < step.execution_count:
                        time.sleep(step.execution_interval / 1000)
            elif step.execution == "持续执行":
                start_time = time.time()
                duration_seconds = step.duration * 60 if step.duration_unit == "分钟" else step.duration
                
                while time.time() - start_time < duration_seconds and self.running:
                    success = step.execute(self)
                    
                    # 如果成功且设置了成功后停止，则退出循环
                    if success and step.stop_on_success:
                        break
                    
                    # 添加间隔
                    time.sleep(step.continuous_interval / 1000)
            
            if self.running:
                self.status_var.set("步骤执行完成")
        except Exception as e:
            self.log(f"执行错误：{str(e)}", level="错误")
            self.status_var.set(f"执行错误：{str(e)}")
        finally:
            if self.running:
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.running = False
    
    def start_execution(self):
        if not self.steps:
            messagebox.showwarning("警告", "请先添加步骤")
            return
        
        if self.running:
            return
        
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("执行中...")
        
        thread = Thread(target=self.execute_steps)
        thread.daemon = True
        thread.start()
    
    def stop_execution(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("已停止")
    
    def execute_steps(self):
        try:
            enabled_steps = [step for step in self.steps if step.enabled]
            total_enabled = len(enabled_steps)
            executed_count = 0
            
            for i, step in enumerate(self.steps):
                if not self.running:
                    break
                
                if not step.enabled:
                    self.log(f"步骤 {i + 1}: {step.name} (已停用，跳过)")
                    continue
                
                executed_count += 1
                self.status_var.set(f"执行步骤 {executed_count}/{total_enabled}: {step.name}")
                
                if step.delay > 0:
                    self.log(f"步骤 {i + 1}: 延迟 {step.delay} ms 执行")
                    time.sleep(step.delay / 1000)
                
                # 记录执行结果
                has_success = False
                
                # 处理执行方式
                if step.execution == "单次执行":
                    has_success = step.execute(self)
                elif step.execution == "多次执行":
                    count = 0
                    while count < step.execution_count and self.running:
                        success = step.execute(self)
                        if success:
                            has_success = True
                        
                        # 如果成功且设置了成功后停止，则退出循环
                        if success and step.stop_on_success:
                            break
                        
                        count += 1
                        
                        # 如果不是最后一次执行，添加间隔
                        if count < step.execution_count:
                            time.sleep(step.execution_interval / 1000)
                elif step.execution == "持续执行":
                    start_time = time.time()
                    duration_seconds = step.duration * 60 if step.duration_unit == "分钟" else step.duration
                    
                    while time.time() - start_time < duration_seconds and self.running:
                        success = step.execute(self)
                        if success:
                            has_success = True
                        
                        # 如果成功且设置了成功后停止，则退出循环
                        if success and step.stop_on_success:
                            break
                        
                        # 添加间隔
                        time.sleep(step.continuous_interval / 1000)
                
                # 检查是否需要在全错时停止执行
                if step.stop_on_error and not has_success:
                    self.log(f"步骤 {i + 1}: {step.name} 执行失败，且设置了全错时停止执行，停止整个执行流程", level="错误")
                    self.status_var.set(f"执行失败：步骤 {i + 1} {step.name} 执行失败")
                    self.running = False
                    break
            
            if self.running:
                self.status_var.set("所有步骤执行完成")
        except Exception as e:
            self.log(f"执行错误：{str(e)}", level="错误")
            self.status_var.set(f"执行错误：{str(e)}")
        finally:
            if self.running:
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.running = False
    
    def browse_program(self):
        file_path = filedialog.askopenfilename(filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")])
        if file_path:
            self.program_path_var.set(file_path)
    
    def browse_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")])
        if file_path:
            self.image_path_var.set(file_path)
    
    def save_log_level(self):
        self.log_level = self.log_level_var.get()
    
    def export_config(self):
        if not self.steps:
            messagebox.showwarning("警告", "没有步骤可导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导出配置"
        )
        
        if file_path:
            try:
                # 将步骤对象转换为字典列表
                steps_data = []
                for step in self.steps:
                    step_dict = {
                        "step_type": step.step_type,
                        "name": step.name,
                        "delay": step.delay,
                        "enabled": step.enabled,
                        "execution": step.execution,
                        "execution_count": step.execution_count,
                        "execution_interval": step.execution_interval,
                        "duration": step.duration,
                        "duration_unit": step.duration_unit,
                        "continuous_interval": step.continuous_interval,
                        "stop_on_success": step.stop_on_success,
                        "stop_on_error": step.stop_on_error
                    }
                    
                    # 添加步骤特定的属性
                    if hasattr(step, 'program_path'):
                        step_dict["program_path"] = step.program_path
                    if hasattr(step, 'text'):
                        step_dict["text"] = step.text
                    if hasattr(step, 'keys'):
                        step_dict["keys"] = step.keys
                    if hasattr(step, 'image_path'):
                        step_dict["image_path"] = step.image_path
                        step_dict["fuzzy"] = step.fuzzy
                        step_dict["region"] = step.region
                        step_dict["region_x"] = step.region_x
                        step_dict["region_y"] = step.region_y
                        step_dict["region_width"] = step.region_width
                        step_dict["region_height"] = step.region_height
                        step_dict["accuracy"] = step.accuracy
                        step_dict["click_type"] = step.click_type
                        step_dict["mouse_speed"] = step.mouse_speed
                        step_dict["click_offset_x"] = step.click_offset_x
                        step_dict["click_offset_y"] = step.click_offset_y
                    
                    steps_data.append(step_dict)
                
                # 保存到JSON文件
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(steps_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"配置已导出到：{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def import_config(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导入配置"
        )
        
        if file_path:
            try:
                # 读取JSON文件
                with open(file_path, "r", encoding="utf-8") as f:
                    steps_data = json.load(f)
                
                # 清空当前步骤
                self.steps = []
                
                # 创建新的步骤对象
                for step_dict in steps_data:
                    step_type = step_dict["step_type"]
                    if step_type == "program":
                        step = ProgramStep(step_dict["name"])
                    elif step_type == "text_input":
                        step = TextInputStep(step_dict["name"])
                    elif step_type == "key_input":
                        step = KeyInputStep(step_dict["name"])
                    elif step_type == "image_recognition":
                        step = ImageRecognitionStep(step_dict["name"])
                    # elif step_type == "image_click_text":
                    #     step = ImageClickTextStep(step_dict["name"])
                    else:
                        continue
                    
                    # 设置基本属性
                    step.delay = step_dict.get("delay", 0)
                    step.enabled = step_dict.get("enabled", True)
                    step.execution = step_dict.get("execution", "单次执行")
                    step.execution_count = step_dict.get("execution_count", 1)
                    step.execution_interval = step_dict.get("execution_interval", 1000)
                    step.duration = step_dict.get("duration", 1)
                    step.duration_unit = step_dict.get("duration_unit", "分钟")
                    step.continuous_interval = step_dict.get("continuous_interval", 1000)
                    step.stop_on_success = step_dict.get("stop_on_success", True)
                    step.stop_on_error = step_dict.get("stop_on_error", False)
                    
                    # 设置步骤特定的属性
                    if hasattr(step, 'program_path'):
                        step.program_path = step_dict.get("program_path", "")
                    if hasattr(step, 'text'):
                        step.text = step_dict.get("text", "")
                    if hasattr(step, 'keys'):
                        step.keys = step_dict.get("keys", "")
                    if hasattr(step, 'image_path'):
                        step.image_path = step_dict.get("image_path", "")
                        step.fuzzy = step_dict.get("fuzzy", True)
                        step.region = step_dict.get("region", "全屏")
                        step.region_x = step_dict.get("region_x", 0)
                        step.region_y = step_dict.get("region_y", 0)
                        step.region_width = step_dict.get("region_width", 1920)
                        step.region_height = step_dict.get("region_height", 1080)
                        step.accuracy = step_dict.get("accuracy", 0.8)
                        step.click_type = step_dict.get("click_type", "左键单击")
                        step.mouse_speed = step_dict.get("mouse_speed", 0.5)
                        step.click_offset_x = step_dict.get("click_offset_x", 0)
                        step.click_offset_y = step_dict.get("click_offset_y", 0)
                    
                    self.steps.append(step)
                
                # 更新UI
                self.update_step_list()
                self.current_step_index = None
                self.update_step_config_ui()
                
                messagebox.showinfo("成功", f"配置已从：{file_path} 导入")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败：{str(e)}")
    
    def log(self, message, level="信息"):
        if self.log_level == "静默":
            return
        elif self.log_level == "错误" and level != "错误":
            return
        elif self.log_level == "信息" and level == "详细":
            return
        
        print(f"[{level}] {message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GameAutoApp(root)
    root.mainloop()