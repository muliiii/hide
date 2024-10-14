import os
import sys
import shutil
import tkinter as tk
import time
import json
import requests
import threading
from tkinter import messagebox, ttk
import zipfile

cursor_path = "./cursor/cursor.cur"  # 鼠标
btn_path = "./cursor/hover.cur"  # hover
# config中存版本
current_version = '2.0'
config_file = "config.json"
x = 778
y = 449

# 标志变量，用于控制线程停止
stop_event = threading.Event()
# 从本地加载配置
def load_config():
    global x, y, current_version
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            x = config.get('x', x)  # 上次x坐标
            y = config.get('y', y)  # 上次y坐标
            current_version = config.get('version')  # 关闭前恢复全部窗口

def show_error_message(message):
    error_window = tk.Toplevel()
    error_window.config(cursor=f"@{cursor_path}")
    error_window.geometry(f"+{x}+{y}")
    error_window.title("错误")
    tk.Label(error_window, text=message).pack(pady=10)
    tk.Button(error_window, text="关闭", command=error_window.destroy, cursor=f"@{btn_path}").pack(pady=10)

def get_update_info():
    try:
        response = requests.get("https://my.youngreeds.com/version.json")
        update_info = response.json()
        return str(update_info['version']), update_info['url'], update_info['content']
    except requests.RequestException as e:
        show_error_message(f"获取更新信息失败: {e}")
        return None, None, None

def download_and_apply_update(url):
    global x, y
    download_path = "update.zip"
    new_version_folder = os.path.join(get_application_path(), f"new_version")

    # 检查是否存在 new_version 文件夹，存在则删除
    if os.path.exists(new_version_folder):
        shutil.rmtree(new_version_folder)

    progress_window = tk.Toplevel()
    progress_window.config(cursor=f"@{cursor_path}")
    progress_window.geometry(f"+{x}+{y}")
    progress_window.title("下载更新")
    
    progress_window.protocol("WM_DELETE_WINDOW",  lambda:confirm_close(progress_window))
    progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=20)
    
    download_status = tk.Label(progress_window, text="下载状态: 0 MB / 0 MB")
    download_status.pack(pady=10)
    progress_window.after(2000, lambda:  tk.Label(progress_window, text="服务器带宽有限，下载速度过慢，请耐心等待~").pack(pady=10))  # 延迟2秒显示下载状态
   
    
    def update_task():
        try:
            if download_update(url, download_path, progress_bar, download_status):
                if extract_update(download_path, new_version_folder):
                    os.remove(download_path)  # 删除下载的 ZIP 文件
                    show_restart_prompt()
                else:
                    messagebox.showerror("更新失败", "解压更新包时出现问题")
            else:
                messagebox.showerror("更新失败", "下载更新时出现问题")
        except Exception as e:
            messagebox.showerror("更新错误", f"更新过程中出现错误: {e}")

    update_thread = threading.Thread(target=update_task)
    update_thread.start()

def extract_update(file_path, extract_to):
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

            # 处理文件名编码
            for i in zip_ref.namelist():
                target_address = extract_to
                file_sep = '/'
                file_sep0 = '\\'
                os.renames(os.path.join(target_address + file_sep0 + i.replace(file_sep, file_sep0)), 
                           os.path.join(target_address + file_sep0 + i.encode('cp437').decode('gbk').replace(file_sep0, file_sep)))
                
        return True
    except zipfile.BadZipFile:
        show_error_message("更新包格式错误")
        return False

def download_update(url, file_path, progress_bar, download_status):
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    progress_bar['value'] = (downloaded / total_size) * 100
                    download_status.config(text=f"下载状态: {downloaded / (1024 * 1024):.2f} MB / {total_size / (1024 * 1024):.2f} MB")
                    # 检查stop_event标志
                    if stop_event.is_set():
                        break  # 停止下载任务
        return True
    except requests.RequestException as e:
        show_error_message(f"下载更新失败: {e}")
        return False

def get_application_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)  # 打包后的应用
    else:
        return os.path.dirname(os.path.abspath(__file__))  # 开发环境

def replace_files(new_version_folder):
    current_folder = get_application_path()
    # 将新版本文件夹中的所有文件替换到当前文件夹
    for item in os.listdir(new_version_folder):
        s = os.path.join(new_version_folder, item)
        d = os.path.join(current_folder, item)
        if os.path.isdir(s):
            shutil.rmtree(d, ignore_errors=True)  # 删除旧文件夹
            shutil.copytree(s, d)  # 复制新文件夹
        else:
            if os.path.exists(d):
                os.remove(d)  # 删除旧文件
            shutil.copy2(s, d)  # 复制新文件

def restart_application():
    os.popen('taskkill /f /im my.exe')
    time.sleep(1)
    new_version_folder = os.path.join(get_application_path(), f"new_version")
    replace_files(new_version_folder)  # 替换当前版本
    shutil.rmtree(new_version_folder)  # 删除临时文件夹
    os.startfile(os.path.join(get_application_path(), f'my.exe'))  # 启动新版本
    os._exit(0)  # 关闭更新程序

# 重启
def show_restart_prompt():
    global restart_window
    restart_window = tk.Tk()
    restart_window.geometry(f"+{x}+{y}")
    restart_window.title("更新完成")
    restart_window.protocol("WM_DELETE_WINDOW",  lambda:confirm_close(restart_window))
    tk.Label(restart_window, text="更新已完成，是否立即重启？").pack(padx=40,pady=20)
    tk.Button(restart_window, text="重启", command=lambda: (restart_window.destroy(), restart_application()), cursor=f"@{btn_path}").pack()
    restart_window.mainloop()

def confirm_close(window):
    if messagebox.askokcancel("确认关闭", "即将完成安装，确定关闭？"):
        stop_event.set()  # 设置stop_event标志，通知后台任务停止
        window.destroy()
        root.quit()
        root.protocol()

if __name__ == "__main__":
    load_config()
    root = tk.Tk()  # 创建主窗口
    root.geometry(f"+{x}+{y}")  # 设置窗口位置
    root.iconphoto(True, tk.PhotoImage(file='./icon/favicon.png'))  # 设置窗口图标

    latest_version, url, content = get_update_info()
    
    if latest_version:
        # 更新提示在主窗口中显示
        if latest_version > current_version:
            root.title("发现新版本")
            tk.Label(root, text=f"有新版本可用: v{latest_version}", fg="green", font=("Arial", 10, "bold")).pack(pady=10)
            content_box = tk.Text(root, height=10, width=50, wrap="word")
            content_box.pack(pady=5)
            content_box.insert(tk.END, f"{content}")
            content_box.config(state=tk.DISABLED)
            tk.Button(root, text="立即更新", command=lambda: download_and_apply_update(url), cursor=f"@{btn_path}").pack(pady=10)
        else:
            root.title("恭喜")
            tk.Label(root, text=f"您的版本已经是最新版本！: v{latest_version}", fg="green", font=("Arial", 10, "bold")).pack(padx=20,pady=20)
    root.lift()
    root.focus()
    # root.protocol("WM_DELETE_WINDOW", lambda: confirm_close(root))  # 关闭窗口时终止程序
    root.mainloop()  # 启动主事件循环
