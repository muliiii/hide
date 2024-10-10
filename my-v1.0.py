import tkinter as tk
import ctypes
import win32gui
import win32con
import win32process
import keyboard
import json
import os
from collections import deque
import psutil
import requests  # 用于下载网络图片
import pywintypes

# 获取前台窗口的句柄
def get_active_window():
    return win32gui.GetForegroundWindow()

# 隐藏窗口
def hide_window(hwnd):
    ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_HIDE)

# 显示窗口
def show_window(hwnd):
    ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_SHOW)

# 处理隐藏和显示
class WindowHider:
    def __init__(self):
        self.window_stack = deque()  # 栈用于管理窗口恢复顺序
        self.hide_key = "ctrl+alt+h"
        self.show_key = "ctrl+alt+s"
        self.config_file = "config.json"
        self.load_config()  # 尝试加载配置
        self.gui_update_callback = None

    def hide_action(self):
        hwnd = get_active_window()
        
        # 如果获取的窗口句柄为 0，表示没有窗口处于激活状态，直接返回，不做处理
        if hwnd == 0:
            return
        
        # 检查该窗口是否已经隐藏（即是否已经在 self.window_stack 中）
        if any(hidden_hwnd == hwnd for hidden_hwnd, _ in self.window_stack):
            return
        
        # 如果是新的窗口，执行隐藏操作
        hide_window(hwnd)
        process_name = self.get_process_name(hwnd)
        
        # 将隐藏的窗口句柄和进程名称添加到栈中
        self.window_stack.append((hwnd, process_name))  
        self.update_gui()  # 更新GUI
        self.getList()  # 初始化时加载窗口列表

    # 显示之前隐藏的窗口
    def show_action(self):
        if self.window_stack:
            hwnd, process_name = self.window_stack.pop()  # 从栈中取出最上面的句柄和进程名称
            show_window(hwnd)
            self.update_gui()  # 更新GUI
            self.getList()  # 初始化时加载窗口列表
            return hwnd  # 返回恢复的窗口句柄

    # 绑定快捷键
    def bind_hotkeys(self):
        keyboard.add_hotkey(self.hide_key, self.hide_action)
        keyboard.add_hotkey(self.show_key, self.show_action)

    # 更新快捷键
    def update_hotkeys(self, hide_key, show_key):
        self.hide_key = hide_key
        self.show_key = show_key
        keyboard.clear_all_hotkeys()
        self.bind_hotkeys()
        self.save_config()  # 更新配置

    # 保存配置到本地
    def save_config(self):
        config = {
            'hide_key': self.hide_key,
            'show_key': self.show_key
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

    # 获取当前隐藏的窗口数量
    def get_hidden_window_count(self):
        return len(self.window_stack)

    # 获取待恢复的窗口列表，并按隐藏顺序倒序
    def get_hidden_windows(self):
        return [(hwnd, process_name) for hwnd, process_name in reversed(self.window_stack)]

    # 获取进程名称
    def get_process_name(self, hwnd):
        try:
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            process_name = psutil.Process(process_id).name()
            return process_name
        except Exception as e:
            print(f"Error getting process name: {e}")
            return "Unknown"

    # 更新GUI
    def update_gui(self):
        if self.gui_update_callback:
            self.gui_update_callback()

    # 注册GUI更新回调
    def register_gui_update_callback(self, callback):
        self.gui_update_callback = callback

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
            
            for idx, (hwnd, process_name) in enumerate(hidden_windows):
                self.listbox.insert(tk.END, process_name)
                
                # 将第一个隐藏的窗口项背景设为绿色
                if idx == 0:
                    self.listbox.itemconfig(idx, {'fg': 'green'})

    # 恢复指定窗口并从列表中移除
    def restore_window(self, index):
        hidden_windows = self.get_hidden_windows()
        if index < len(hidden_windows):
            hwnd, _ = hidden_windows[index]
            show_window(hwnd)
            self.window_stack.remove((hwnd, _))  # 从栈中移除恢复的窗口
            self.update_gui()  # 更新GUI
            self.getList()  # 更新列表

# 创建GUI
class WindowApp:
    def __init__(self, root, hider):
        self.hider = hider
        self.hider.register_gui_update_callback(self.update_hidden_count)

        # GUI窗口设置
        root.title("窗口隐藏工具v1.0")
        root.geometry("350x280")

        # 隐藏快捷键行
        hide_frame = tk.Frame(root)
        hide_frame.pack(pady=5, padx=10, anchor='w')

        tk.Label(hide_frame, text="隐藏快捷键:").pack(side=tk.LEFT, padx=5,pady=10)
        self.hide_entry = tk.Entry(hide_frame, width=20)
        self.hide_entry.insert(0, self.hider.hide_key)
        self.hide_entry.pack(side=tk.LEFT, padx=5)

        # 恢复默认按钮
        hide_reset_button = tk.Button(hide_frame, text="恢复默认", command=self.reset_hide_key)
        hide_reset_button.pack(side=tk.LEFT, padx=5)

        # 显示快捷键行
        show_frame = tk.Frame(root)
        show_frame.pack(pady=5, padx=10, anchor='w')

        tk.Label(show_frame, text="显示快捷键:").pack(side=tk.LEFT, padx=5)
        self.show_entry = tk.Entry(show_frame, width=20)
        self.show_entry.insert(0, self.hider.show_key)
        self.show_entry.pack(side=tk.LEFT, padx=5)

        # 恢复默认按钮
        show_reset_button = tk.Button(show_frame, text="恢复默认", command=self.reset_show_key)
        show_reset_button.pack(side=tk.LEFT, padx=5)

        # 设置按钮
        tk.Button(root, text="保存快捷键", command=self.set_hotkeys).pack(pady=10)
        # 隐藏数量标签
        self.hidden_count_label = tk.Label(root, text=f"当前隐藏窗口数量: {self.hider.get_hidden_window_count()}")
        self.hidden_count_label.pack(pady=10)

        # 显示列表按钮
        tk.Button(root, text="查看待恢复窗口", command=self.show_hidden_windows).pack(pady=5)
        # 显示打赏二维码
        tk.Button(root, text="打赏", command=self.show_code).pack(pady=5)


    # 恢复隐藏快捷键到默认值
    def reset_hide_key(self):
        self.hide_entry.delete(0, tk.END)
        self.hide_entry.insert(0, "ctrl+alt+h")  # 默认值
        self.hider.update_hotkeys("ctrl+alt+h", self.hider.show_key)  # 更新并保存

    # 恢复显示快捷键到默认值
    def reset_show_key(self):
        self.show_entry.delete(0, tk.END)
        self.show_entry.insert(0, "ctrl+alt+s")  # 默认值
        self.hider.update_hotkeys(self.hider.hide_key, "ctrl+alt+s")  # 更新并保存

    # 获取用户输入并更新快捷键
    def set_hotkeys(self):
        hide_key = self.hide_entry.get() or self.hider.hide_key
        show_key = self.show_entry.get() or self.hider.show_key
        self.hider.update_hotkeys(hide_key, show_key)

    # 更新隐藏窗口数量标签
    def update_hidden_count(self):
        count = self.hider.get_hidden_window_count()
        self.hidden_count_label.config(text=f"当前隐藏窗口数量: {count}")

    # 显示待恢复窗口列表
    def show_hidden_windows(self):
        if not hasattr(self.hider, 'list_window') or not self.hider.list_window.winfo_exists():
            # 创建显示窗口列表的对话框
            self.hider.list_window = tk.Toplevel()
            self.hider.list_window.title("待恢复窗口列表")
            self.hider.list_window.geometry("300x200")
            
            tk.Label(self.hider.list_window, text="注: 绿色表示下一个恢复的窗口").pack(anchor='w', padx=10)
            tk.Label(self.hider.list_window, text="点击程序可快速恢复").pack(anchor='w', padx=10)
            self.hider.listbox = tk.Listbox(self.hider.list_window)
            self.hider.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 绑定点击事件
            self.hider.listbox.bind("<ButtonRelease-1>", self.on_listbox_click)
            
            self.hider.getList()  # 初始化时加载窗口列表
        else:
            self.hider.list_window.deiconify()
            self.hider.list_window.lift()  # 提升窗口
            self.hider.list_window.focus_force()  # 聚焦窗口

    # 显示待恢复窗口列表
    def show_code(self):
        if not hasattr(self.hider, 'code_window') or not self.hider.code_window.winfo_exists():
            # 创建显示窗口列表的对话框
            self.hider.code_window = tk.Toplevel()
            self.hider.code_window.title("打赏")
            self.hider.code_window.geometry("440x600")
            # 下载图片到本地
            local_image_path = self.download_image()
            img = tk.PhotoImage(file=local_image_path)
            img_label = tk.Label(self.hider.code_window, image=img)
            img_label.image = img  # 防止图片被垃圾回收
            img_label.pack(pady=10)
        else:
            self.hider.code_window.deiconify()
            self.hider.code_window.lift()  # 提升窗口
            self.hider.code_window.focus_force()  # 聚焦窗口
    def download_image(self):
        url = "https://youngreeds.com/code.png"
        local_image_path = "code.png"
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
            self.hider.restore_window(index)  # 恢复选中的窗口

# 初始化程序
if __name__ == "__main__":
    hider = WindowHider()
   

    root = tk.Tk()
    app = WindowApp(root, hider)
    hider.bind_hotkeys()  # 绑定默认快捷键
    root.mainloop()
