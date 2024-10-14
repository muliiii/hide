import tkinter as tk
from tkinter import ttk
import ctypes
import win32gui
import win32con
import win32process
import keyboard
import json
import os
import sys
from collections import deque
import psutil
import requests  # 用于下载网络图片

cursor_path = "./cursor/cursor.cur"  # 鼠标
btn_path = "./cursor/hover.cur"  # hover
TITLE = "窗口隐藏工具"
current_version = '1.5'
update_version = ''  # 新版本
title_colors = {
    "错误": "#f56c6c", # 红
    "提示": "#67c23a", # 绿
    "警告": "#e6a23c", # 黄
    "信息": "#409eff", # 蓝
}
# 全局字典来存储不同的消息窗口
message_windows = {}
# 检查服务器是否有更新
def check_for_update(current_version):
    global update_version
    try:
        response = requests.get("https://my.youngreeds.com/version.json")
        response.raise_for_status()
        latest_version_data = response.json()
        latest_version = str(latest_version_data['version'])
        update_version = latest_version
        return latest_version > current_version
    except requests.RequestException as e:
        show_message({'title':"错误", 'message':f"检查更新失败: {e}" })
        return False
# 点击检查更新
isFirst = True
def check_and_update():
    global isFirst
    if check_for_update(current_version):
        notifier_path = os.path.join(get_application_path(), f"my_update.exe")
        if not os.path.exists(notifier_path):
            show_message({'title':"错误",'message': "检查更新失败，请检查文件完整性。"})
            return
        os.startfile(notifier_path)  # 启动更新提示程序
    else:
        if not isFirst:
            # 没有新版本
            show_message({'title':"提示",'message': "您的版本已经是最新版本！",'timeout':3})
    isFirst = False

# 获取当前根目录路径
def get_application_path():
    # 如果是打包后的应用，使用临时目录
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 获取前台窗口的句柄
def get_active_window():
    return win32gui.GetForegroundWindow()

# 隐藏窗口
def hide_window(hwnd):
    ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_HIDE)

# 最小化窗口并保留在任务栏
def minimize_window(hwnd):
    ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_MINIMIZE)

# 显示窗口
def show_window(hwnd):
    ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_SHOW)


def show_message(params):
    global message_windows  # 使用全局字典

    title = params.get("title", "提示")  # 获取标题，默认值为"提示"
    message = params.get("message", "")  # 获取消息内容
    timeout = params.get("timeout", 0)   # 获取超时时间，默认值为5秒

    # 如果这个消息的窗口不存在或已经被销毁，才创建新的窗口
    if message not in message_windows or not message_windows[message].winfo_exists():
        # 创建错误窗口
        message_windows[message] = tk.Toplevel()
        message_windows[message].config(cursor=f"@{cursor_path}")
        message_windows[message].title(title)

        # 根据错误类型设置标题颜色
        title_color = title_colors.get(title, "black")
        # 错误信息标签
        tk.Label(
            message_windows[message], 
            text=message, 
            wraplength=200, 
            fg=title_color  # 设置文字颜色
        ).pack(pady=10)

        # 确定按钮
        ok_button = tk.Button(
            message_windows[message], 
            text="关闭", 
            command=lambda: close_message_window(message),  # 使用lambda调用关闭函数
            cursor=f"@{btn_path}"
        )
        ok_button.pack(pady=5)

        # 根据 timeout 判断是否自动关闭窗口
        if timeout > 0:
            message_windows[message].after(timeout * 1000, lambda: close_message_window(message))  # 按指定的秒数关闭窗口

    
    # 如果窗口已经存在且有效，将其置于最上层
    message_windows[message].lift()
    message_windows[message].focus()

def close_message_window(message):
    """关闭并从字典中删除窗口"""
    if message in message_windows and message_windows[message].winfo_exists():
        message_windows[message].destroy()
    message_windows.pop(message, None)  # 从字典中删除已关闭的窗口

class WindowManager:
    def __init__(self, root):
        # 窗口标题
        self.TITLE = f"{TITLE} v{current_version} 最新版"
        # 定义窗口标题列表
        self.window_titles = [self.TITLE, "设置", "待恢复窗口列表", "打赏","错误","提示","警告","信息"]
        self.window_stack = deque()  # 栈用于管理窗口恢复顺序
        self.hide_key = "ctrl+alt+h"
        self.show_key = "ctrl+alt+s"
        self.self_key = "ctrl+alt+t"
        self.is_clear = False
        # 用于状态检测
        self.keys_pressed = set()
        self.selfVisibly = True # 隐藏此窗口
        self.config_file = "config.json"
        self.restore_on_exit = True  # 关闭程序前恢复所有窗口
        self.mode = False  # 切换指定模式
        self.minimize_on_show = False  # 控制是否在显示时最小化
        self.sync_self = False  # 控制是否同步隐藏/恢复本程序
        self.original_styles = {}  # 存储窗口原始样式的字典
        self.x = 778
        self.y = 449 
        self.load_config()  # 尝试加载配置
        # GUI窗口设置
        root.config(cursor=f"@{cursor_path}")
        root.title(self.TITLE)
        root.geometry("320x250")
        root.geometry(f"+{self.x}+{self.y}")
        # 设置窗口图标
        root.iconphoto(True, tk.PhotoImage(file='./icon/favicon.png'))
        # root.set_ui()
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10, padx=10)
        
        # 设置按钮
        self.settings_button = tk.Button(button_frame, text="设置", command=self.open_settings_window, cursor=f"@{btn_path}")
        self.settings_button.pack(side=tk.LEFT, padx=10) 
        
        # 打赏按钮
        self.donation_button = tk.Button(button_frame, text="打赏", command=self.show_code, cursor=f"@{btn_path}")
        self.donation_button.pack(side=tk.LEFT, padx=10) 

        # 隐藏数量标签
        self.hidden_count_label = tk.Label(root, text=f"当前隐藏窗口数量: {self.get_hidden_window_count()}")
        self.hidden_count_label.pack()

        # 显示列表按钮
        tk.Button(root, text="查看待恢复窗口", command=self.show_hidden_windows, cursor=f"@{btn_path}").pack(pady=5)

        

        # 显示时最小化选项
        self.change_mode = tk.BooleanVar(value=self.mode)  # 读取配置中的值
        self.minimize_check = tk.restore_focus_on_showCheckbutton(root, text="指定窗口 隐藏/恢复", variable=self.change_mode, command=self.toggle_mode)
        self.minimize_check.pack(pady=5)
        

        # # 创建进程选择标签
        self.process_label = tk.Label(root, text="请选择窗口:")
        self.process_label.pack()
        # 创建进程选择下拉列表
        self.process_dropdown = ttk.Combobox(root, state='readonly')
        self.process_dropdown.pack(fill='x', padx=50)
        self.update_process_list()  # 初始化时更新进程列表

        # 加载时打印可见进程()
        # self.print_all_window_handles()
        # 创建刷新进程列表按钮
        self.refresh_button = tk.Button(root, text="刷新窗口下拉列表", command=self.update_process_list, cursor=f"@{btn_path}")
        self.refresh_button.pack(pady=5)
        
        # 更新控件的显示状态
        self.update_visibility()
        # 绑定快捷键
        self.bind_hotkeys()
        # 监控按键状态
        self.monitor_keys()
        # 处理程序关闭事件
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def print_all_window_handles(self):
        def callback(hwnd, _):
            # 过滤掉最小化窗口
            if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                # 获取窗口标题
                window_title = win32gui.GetWindowText(hwnd)
                if window_title:  # 只打印有标题的窗口
                    try:
                        # 获取进程ID
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        proc = psutil.Process(pid)
                        process_name = proc.name()
                        # 打印窗口句柄和进程名称
                        print(f"窗口句柄: {hwnd}, 进程名称: {process_name}, 窗口标题: {window_title}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # 忽略无法访问的进程
                        pass

        # 枚举所有顶层窗口
        win32gui.EnumWindows(callback, None)

    # 切换模式 控制显示和隐藏进程
    def update_visibility(self):
        # 根据 mode 的值决定控件的可见性
        if self.mode:
            self.process_label.pack()
            self.process_dropdown.pack(fill='x', padx=50)
            self.refresh_button.pack(pady=5)
        else:
            self.process_label.pack_forget()
            self.process_dropdown.pack_forget()
            self.refresh_button.pack_forget()

    # 隐藏本程序窗口
    def hide_self_window(self):
        for title in self.window_titles:
            hwnd = win32gui.FindWindow(None, title)
            if hwnd:  # 找到窗口句柄才隐藏
                hide_window(hwnd)
    # 显示本程序窗口
    def show_self_window(self):
        for title in self.window_titles:
            hwnd = win32gui.FindWindow(None, title)
            if hwnd:  # 找到窗口句柄才显示
                if self.minimize_on_show:
                    minimize_window(hwnd)
                else:
                    show_window(hwnd)
        # 更新 GUI 和窗口列表
        self.update_hidden_count()

        self.getList()
    # 隐藏当前的窗口
    def hide_action(self):
        hwnd = get_active_window()
        if hwnd == 0:
            return

        # 当前是否已经隐藏该窗口
        if any(hidden_hwnd == hwnd for hidden_hwnd, _ in self.window_stack):
            return

        # 指定隐藏程序
        if self.mode:
            if not self.hide_process():
                return
        else:
            hide_window(hwnd)
            # 记录窗口信息
            process_name = self.get_process_name(hwnd)
            pid = win32process.GetWindowThreadProcessId(hwnd)[1]
            self.window_stack.append((hwnd, pid))
            
        # 是否同步隐藏本程序
        if self.sync_self:
            self.hide_self_window()
            self.selfVisibly = False
        # 更新 GUI 和窗口列表
        self.update_hidden_count()

        self.getList()
    # 显示之前隐藏的窗口
    def show_action(self):
        if self.window_stack:
            # 这里不立刻pop，先获取堆栈中的最后一个窗口句柄和进程名
            hwnd, process_name = self.window_stack[-1]  # 只取值不移除

            if hwnd == 0:
                show_message({'title':"错误",'message':f"无效窗口句柄"})
                return

            # 是否同步隐藏本程序
            if self.sync_self:
                self.show_self_window()
                self.selfVisibly = True
            # 指定显示程序
            if self.mode:
                self.restore_process()
            else:
                if self.minimize_on_show:
                    minimize_window(hwnd)
                else:
                    show_window(hwnd)

                # 成功显示后，再移除
                self.window_stack.pop()

            # 更新 GUI 和窗口列表
            self.update_hidden_count()
            self.getList()
    # 显示之前隐藏的窗口
    def self_action(self):
        if self.selfVisibly:
            self.hide_self_window()
        else:
            for title in self.window_titles:
                selfhwnd = win32gui.FindWindow(None, title)
                # 从待恢复列表中移除已经恢复的窗口
                self.window_stack = deque([(hwnd, pid) for hwnd, pid in self.window_stack if hwnd != selfhwnd])
            self.show_self_window()
            
    
        self.selfVisibly = not self.selfVisibly
    # 绑定快捷键
    def bind_hotkeys(self):
        keys = [self.hide_key, self.show_key, self.self_key]
        if self.is_clear == False:
            # for key in keys:
            #     try:
            #         keyboard.add_hotkey(key, self.action_for_key(key))
            #     except ValueError:
            #         self.show_message({'title':"错误",'message':f"无效的组合键: {key}"})
            keyboard.unhook_all()
            self.is_clear = True
        self.save_config()  # 更新配置

    # 根据键名选择对应的动作
    def action_for_key(self, key):
        if key == self.hide_key:
            return self.hide_action
        elif key == self.show_key:
            return self.show_action
        elif key == self.self_key:
            return self.self_action

    # 监控按键状态
    def monitor_keys(self):
        keyboard.hook(self.on_key_event)

    # 处理按键事件
    def on_key_event(self, event):
        if event.event_type == 'down':
            self.keys_pressed.add(event.name)
            self.check_hotkey_state()
        elif event.event_type == 'up':
            self.keys_pressed.discard(event.name)

    # 检查热键状态
    def check_hotkey_state(self):
        # 检查每个热键是否被按下
        if all(key in self.keys_pressed for key in self.hide_key.split('+')):
            self.hide_action()  # 立即执行动作
        if all(key in self.keys_pressed for key in self.show_key.split('+')):
            self.show_action()  # 立即执行动作
        if all(key in self.keys_pressed for key in self.self_key.split('+')):
            self.self_action()  # 立即执行动作

    # 更新快捷键
    def update_hotkeys(self, hide_key, show_key,self_key):
        # 检查快捷键是否重复
        if len({hide_key, show_key, self_key}) < 3:
            show_message({'title':"警告",'message':"快捷键不能重复，请重新设置"})
            return
        self.hide_key = hide_key
        self.show_key = show_key
        self.self_key = self_key
        keyboard.clear_all_hotkeys()
        self.bind_hotkeys()

    # 保存配置到本地
    def save_config(self):
        config = {
            'hide_key': self.hide_key,
            'show_key': self.show_key,
            'self_key': self.self_key,
            'restore_on_exit': self.restore_on_exit,
            'mode': self.mode,
            'minimize_on_show': self.minimize_on_show,
            'sync_self': self.sync_self,  # 新增配置项
            'x': self.x,
            'y': self.y,
            'version': current_version,
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    # 从本地加载配置
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.hide_key = config.get('hide_key', self.hide_key)
                self.show_key = config.get('show_key', self.show_key)
                self.self_key = config.get('self_key', self.self_key)
                self.restore_on_exit = config.get('restore_on_exit', True)  # 关闭前恢复全部窗口
                self.mode = config.get('mode', False)  # 切换模式
                self.minimize_on_show = config.get('minimize_on_show', False)  # 静默显示
                self.sync_self = config.get('sync_self', False)  # 同时隐藏自己
                self.x = config.get('x', self.x)  # 上次x坐标
                self.y = config.get('y', self.y)  # 上次y坐标
        else:
            # 如果配置文件不存在，则创建默认配置
            self.save_config()

    # 获取当前隐藏的窗口数量
    def get_hidden_window_count(self):
        return len(self.window_stack)

    # 获取待恢复的窗口列表，并按隐藏顺序倒序
    def get_hidden_windows(self):
        return [(hwnd, pid) for hwnd, pid in reversed(self.window_stack)]

    # 获取进程名称
    def get_process_name(self, hwnd):
        try:
            pid = win32process.GetWindowThreadProcessId(hwnd)[1]
            process = psutil.Process(pid)
            return process.name()
        except Exception as e:
            show_message({'title':"错误",'message':f"获取窗口名称时出错: {e}"})
            return "Unknown"

    # 切换指定模式
    def toggle_mode(self):
        self.mode = not self.mode
        self.save_config()
        # 更新控件的显示状态
        self.update_visibility()

    # 切换同步隐藏/恢复自身功能
    def toggle_sync_self(self):
        self.sync_self = self.sync_var.get()
        self.save_config()

    def on_closing(self):
        if self.restore_on_exit:
            for hwnd, _ in self.window_stack:
                show_window(hwnd)
        
        self.x = root.winfo_x()
        self.y = root.winfo_y()
        settings = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                settings = json.load(f)

        # 更新位置
        settings['x'] = self.x
        settings['y'] = self.y
        with open(self.config_file, 'w') as f:
            json.dump(settings, f)
        root.destroy()

    # 隐藏指定
    def hide_process(self):
        process_name = self.process_dropdown.get()  # 获取选择的进名
        selected_process_name = next((key for key, val in self.process_dict.items() if val == process_name), None)
        if selected_process_name:
            self.hide_windows(selected_process_name)  # 隐藏该进程的窗口
        else:
            show_message({'title':"信息",'message':f"请选择一个窗口来切换模式",'timeout':5000}) 
            self.process_dropdown.set('')  # 清空 process_dropdown 的值
            return False
        return True
            
    # 恢复选定进程的窗口
    def restore_process(self):
        process_name = self.process_dropdown.get()
        selected_process_name = next((key for key, val in self.process_dict.items() if val == process_name), None)
        if selected_process_name:
            self.restore_windows(selected_process_name)
 
    def hide_windows(self, process_name):
        # 隐藏指定进程的所有窗口
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.name() == process_name:
                pid = proc.info['pid']
                self.hide_windows_by_pid(pid)
    def hide_windows_by_pid(self, pid):
        # 隐藏指定进程ID的所有窗口
        def callback(hwnd, whdls):
            if win32gui.IsWindowVisible(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    whdls.append(hwnd)
                    self.original_styles[hwnd] = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                    win32gui.ShowWindow(hwnd, 0)
                    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, self.original_styles[hwnd] & ~win32con.WS_VISIBLE)
                    # 将窗口添加到待恢复列表中
                    self.window_stack.append((hwnd, pid))
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)

    def restore_windows(self, process_name):
        # 恢复指定进程的所有窗口
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.name() == process_name:
                pid = proc.info['pid']
                self.restore_windows_by_pid(pid)
    def restore_windows_by_pid(self, target_pid):
        windows_to_restore = []
        
        # 遍历 window_stack 逐个检查 PID
        for hwnd, pid in self.window_stack:
            if pid == target_pid:
                windows_to_restore.append((hwnd, pid))
        
        # 处理匹配到的窗口
        for hwnd, pid in windows_to_restore:
            try:
                if self.minimize_on_show:
                    minimize_window(hwnd)
                else:
                    # 尝试多种方法恢复窗口
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 0, 0, 
                                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
                    show_window(hwnd)
                    win32gui.RedrawWindow(hwnd, None, None, 
                                            win32con.RDW_INVALIDATE | win32con.RDW_ERASE | win32con.RDW_FRAME | win32con.RDW_ALLCHILDREN)
                   
            except Exception as e:
                show_message({'title':"错误",'message':f"恢复错误: {e}"})

        # 从待恢复列表中移除已经恢复的窗口
        self.window_stack = deque([(hwnd, pid) for hwnd, pid in self.window_stack if pid != target_pid])
    def update_process_list(self):
        visible_windows = {}

        # 定义回调函数，用于获取所有窗口
        def enum_windows_callback(hwnd, _):
            #获取可见窗口
            if win32gui.IsWindowVisible(hwnd):
                # 获取窗口标题
                window_title = win32gui.GetWindowText(hwnd)
                if window_title:
                    # 获取窗口对应的进程 ID
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    # 查找进程名
                    try:
                        proc = psutil.Process(pid)
                        process_name = proc.name()
                        # 只添加一次进程名称
                        if process_name not in visible_windows:
                            # 将'key'设为process_name, 'value'设为'window_title - process_name'
                            visible_windows[process_name] = f"{process_name} - {window_title}"
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass

        # 枚举所有窗口并执行回调
        win32gui.EnumWindows(enum_windows_callback, None)

        # 对字典的values进行排序
        sorted_visible_windows = dict(sorted(visible_windows.items(), key=lambda item: item[1]))

        # 更新下拉列表，显示'窗口标题 - 进程名'，但是实际选中的值是'process_name'
        self.process_dropdown['values'] = list(sorted_visible_windows.values())

        # 存储key-value对应关系，供其他功能使用
        self.process_dict = sorted_visible_windows
    def toggle_restore(self):
        self.restore_on_exit = self.restore_var.get()
        self.save_config()  # 保存配置

    def toggle_minimize(self):
        self.minimize_on_show = self.minimize_var.get()
        self.save_config()  # 保存配置

    def reset_hide_key(self):
        self.hide_entry.delete(0, tk.END)
        self.hide_entry.insert(0, "ctrl+alt+h")
        self.set_hotkeys()

    def reset_show_key(self):
        self.show_entry.delete(0, tk.END)
        self.show_entry.insert(0, "ctrl+alt+s")
        self.set_hotkeys()

    def reset_self_key(self):
        self.self_entry.delete(0, tk.END)
        self.self_entry.insert(0, "ctrl+alt+t")
        self.set_hotkeys()

    def set_hotkeys(self):
        hide_key = self.hide_entry.get() or self.hide_key
        show_key = self.show_entry.get() or self.show_key
        self_key = self.self_entry.get() or self.self_key
        self.update_hotkeys(hide_key, show_key,self_key)
        self.show_save_button.focus_set()
    def update_hidden_count(self):
        self.hidden_count_label.config(text=f"当前隐藏窗口数量: {self.get_hidden_window_count()}")
    def open_settings_window(self):
        # 检查设置窗口是否已存在且有效
        if not hasattr(self, 'settings_window') or not self.settings_window.winfo_exists():
            # 创建设置窗口
            self.settings_window = tk.Toplevel()
            self.settings_window.config(cursor=f"@{cursor_path}")
            self.settings_window.title("设置")
            self.settings_window.geometry("360x300")
            self.settings_window.geometry(f"+{self.x}+{self.y}")
            # 隐藏快捷键行
            hide_frame = tk.Frame(self.settings_window)
            hide_frame.pack(pady=5, padx=10, fill=tk.X)
            tk.Label(hide_frame, text="隐藏快捷键:").pack(side=tk.LEFT, padx=20)
            self.hide_entry = tk.Entry(hide_frame, width=20)
            self.hide_entry.insert(0, self.hide_key)
            self.hide_entry.pack(side=tk.LEFT, padx=5)
            # 恢复默认按钮
            hide_reset_button = tk.Button(hide_frame, text="恢复默认", command=self.reset_hide_key, cursor=f"@{btn_path}")
            hide_reset_button.pack(side=tk.LEFT, padx=5)

            # 显示快捷键行
            show_frame = tk.Frame(self.settings_window)
            show_frame.pack(pady=5, padx=10, fill=tk.X)
            tk.Label(show_frame, text="显示快捷键:").pack(side=tk.LEFT, padx=20)
            self.show_entry = tk.Entry(show_frame, width=20)
            self.show_entry.insert(0, self.show_key)
            self.show_entry.pack(side=tk.LEFT, padx=5)
            # 恢复默认按钮
            show_reset_button = tk.Button(show_frame, text="恢复默认", command=self.reset_show_key, cursor=f"@{btn_path}")
            show_reset_button.pack(side=tk.LEFT, padx=5)

            # 显示快捷键行
            self_frame = tk.Frame(self.settings_window)
            self_frame.pack(pady=5, padx=10, fill=tk.X)
            tk.Label(self_frame, text="隐藏/显示此窗口:").pack(side=tk.LEFT, padx=5)
            self.self_entry = tk.Entry(self_frame, width=20)
            self.self_entry.insert(0, self.self_key)
            self.self_entry.pack(side=tk.LEFT, padx=5)
            # 恢复默认按钮
            self_reset_button = tk.Button(self_frame, text="恢复默认", command=self.reset_self_key, cursor=f"@{btn_path}")
            self_reset_button.pack(side=tk.LEFT, padx=5)

            # 保存按钮
            self.show_save_button = tk.Button(self.settings_window, text="保存快捷键", command=self.set_hotkeys, cursor=f"@{btn_path}")
            self.show_save_button.pack(pady=10)
            # 关闭前恢复窗口选项
            self.restore_var = tk.BooleanVar(value=self.restore_on_exit)  # 读取配置中的值
            self.restore_check = tk.restore_focus_on_showCheckbutton(self.settings_window, text="关闭程序前恢复所有窗口", variable=self.restore_var, command=self.toggle_restore, cursor=f"@{btn_path}")
            self.restore_check.pack()

            # 显示时最小化选项
            self.minimize_var = tk.BooleanVar(value=self.minimize_on_show)  # 读取配置中的值
            self.minimize_check = tk.restore_focus_on_showCheckbutton(self.settings_window, text="静默显示", variable=self.minimize_var, command=self.toggle_minimize, cursor=f"@{btn_path}")
            self.minimize_check.pack()
            

            
            # 操作时是否隐藏/恢复本程序
            self.sync_var = tk.BooleanVar(value=self.sync_self)  # 默认不同步
            self.sync_self_check = tk.restore_focus_on_showCheckbutton(
                self.settings_window, text="操作时是否 隐藏/恢复 此窗口", variable=self.sync_var, command=self.toggle_sync_self, cursor=f"@{btn_path}"
            )
            self.sync_self_check.pack()
            self.check_update = tk.Button(self.settings_window, text="检查更新", command=check_and_update, cursor=f"@{btn_path}")
            self.check_update.pack(pady=10)

        # 如果窗口已经存在且有效，将其置于最上层
        self.settings_window.lift()
        self.settings_window.focus()
    def show_hidden_windows(self):
        if not hasattr(self, 'list_window') or not self.list_window.winfo_exists():
            # 创建显示窗口列表的对话框
            self.list_window = tk.Toplevel()
            self.list_window.config(cursor=f"@{cursor_path}")
            self.list_window.title("待恢复窗口列表")
            self.list_window.geometry("300x200")
            self.list_window.geometry(f"+{self.x}+{self.y}")
            tk.Label(self.list_window, text="注: 绿色表示下一个恢复的窗口").pack(anchor='w', padx=10)
            tk.Label(self.list_window, text="点击窗口可快速恢复").pack(anchor='w', padx=10)
            self.listbox = tk.Listbox(self.list_window)
            self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            # 绑定点击事件
            self.listbox.bind("<ButtonRelease-1>", self.on_listbox_click)
            self.listbox.config(cursor=f"@{btn_path}")
            self.getList()

        # 如果窗口已经存在且有效，将其置于最上层
        self.list_window.lift()
        self.list_window.focus()

    def restore_selected_window(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            hwnd = int(self.listbox.get(selected_index).split(",")[0].split(":")[1].strip())
            if hwnd in [hwnd for hwnd, _ in self.window_stack]:
                show_window(hwnd)
                self.window_stack = deque([(h, p) for h, p in self.window_stack if h != hwnd])
                self.update_hidden_count()

    # 显示待恢复窗口列表
    def show_code(self):
        if not hasattr(self, 'code_window') or not self.code_window.winfo_exists():
            # 创建显示窗口列表的对话框
            self.code_window = tk.Toplevel()
            self.code_window.config(cursor=f"@{cursor_path}")
            self.code_window.title("打赏")
            self.code_window.geometry("440x600")
            self.code_window.geometry(f"+{self.x}+{self.y}")
            # 下载图片到本地
            local_image_path = self.download_image()
            img = tk.PhotoImage(file=local_image_path)
            img_label = tk.Label(self.code_window, image=img)
            img_label.image = img  # 防止图片被垃圾回收
            img_label.pack(pady=10)
        
        self.code_window.lift()  # 提升窗口
        self.code_window.focus_force()  # 聚焦窗口
    def download_image(self):
        url = "https://youngreeds.com/code.png"
        local_image_path = "./icon/code.png"
        response = requests.get(url)
        with open(local_image_path, 'wb') as f:
            f.write(response.content)
        return local_image_path

    # 处理点击列表项事件
    def on_listbox_click(self, event):
        widget = event.widget
        selection = widget.curselection()
        if selection:
            index = selection[0]
            self.restore_window(index)  # 恢复选中的窗口

    # 刷新列表显示
    def getList(self):
        if hasattr(self, 'list_window') and self.list_window.winfo_exists():
            self.update_hidden_window_list()

    # 更新隐藏窗口列表（使用Listbox）
    def update_hidden_window_list(self):
        if hasattr(self, 'listbox') and self.listbox:
            hidden_windows = self.get_hidden_windows()

            # 清空Listbox
            self.listbox.delete(0, tk.END)
            for idx, (hwnd, pid) in enumerate(hidden_windows):
                try:
                    pid = int(pid)
                    process_name = psutil.Process(pid).name()
                    self.listbox.insert(tk.END, f"窗口句柄: {hwnd}, 窗口名称: {process_name}")
                    if idx == 0:
                        self.listbox.itemconfig(idx, {'fg': 'green'})
                except psutil.NoSuchProcess:
                    continue
            
            self.listbox.bind('<Double-1>', self.restore_selected_window)
    # 恢复指定窗口并从列表中移除
    def restore_window(self, index):
        hidden_windows = self.get_hidden_windows()
        if index < len(hidden_windows):
            hwnd, _ = hidden_windows[index]
            if self.minimize_on_show:
                minimize_window(hwnd)
            show_window(hwnd)
            self.window_stack.remove((hwnd, _))  # 从栈中移除恢复的窗口
            self.update_hidden_count()  # 更新GUI
            self.getList()  # 更新列表

if __name__ == "__main__":
    root = tk.Tk()
    app = WindowManager(root)
    check_and_update()
    root.mainloop()