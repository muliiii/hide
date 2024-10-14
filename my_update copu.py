import os
import sys
import shutil
import tkinter as tk
import time
import requests
import threading
from tkinter import messagebox, ttk
import zipfile

# config中存版本
current_version = '1.0'
def show_error_message(message):
    error_window = tk.Toplevel()
    error_window.title("错误")
    tk.Label(error_window, text=message).pack(pady=10)
    tk.Button(error_window, text="关闭", command=error_window.destroy).pack(pady=10)

def get_update_info():
    try:
        response = requests.get("https://my.youngreeds.com/version.json")
        update_info = response.json()
        return str(update_info['version']), update_info['url'], update_info['content']
    except requests.RequestException as e:
        show_error_message(f"获取更新信息失败: {e}")
        return None, None, None

def show_update_prompt(latest_version, url,content):
    update_window = tk.Toplevel()
    update_window.title("更新提示")
    if latest_version <= current_version:
        version_label = tk.Label(update_window, text=f"您的版本已经是最新版本！: v{latest_version}", fg="green", font=("Arial",10, "bold"))
        version_label.pack(pady=10)
        return
    # 版本号标签，使用绿色字体
    version_label = tk.Label(update_window, text=f"有新版本可用: v{latest_version}", fg="green", font=("Arial",10, "bold"))
    version_label.pack(pady=10)

    # 使用 Text 组件显示多行更新内容
    content_box = tk.Text(update_window, height=10, width=50, wrap="word")
    content_box.pack(pady=5)

    content_box.insert(tk.END, f"{content}")
    content_box.config(state=tk.DISABLED)  # 禁止用户编辑
    tk.Button(update_window, text="立即更新", command=lambda: (update_window.destroy(), download_and_apply_update(url))).pack(pady=10)
    # update_window.mainloop()
def download_and_apply_update(url):
    download_path = "update.zip"
    new_version_folder = os.path.join(get_application_path(), f"new_version")

    progress_window = tk.Toplevel()
    progress_window.title("下载更新")
    
    progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=20)
    
    download_status = tk.Label(progress_window, text="下载状态: 0 MB / 0 MB")
    download_status.pack(pady=10)

    def update_task():
        if download_update(url, download_path, progress_bar, download_status):
            if extract_update(download_path, new_version_folder):
                os.remove(download_path)  # 删除下载的 ZIP 文件
                show_restart_prompt()
            else:
                messagebox.showerror("更新失败", "解压更新包时出现问题")
        else:
            messagebox.showerror("更新失败", "下载更新时出现问题")
        progress_window.destroy()  # 关闭进度窗口

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
                    # restart_window.update_idletasks()  # 刷新界面
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
    os.popen('taskkill /f /im main-v1.1.exe')
    time.sleep(1)
    new_version_folder = os.path.join(get_application_path(), f"new_version")
    replace_files(new_version_folder)  # 替换当前版本
    shutil.rmtree(new_version_folder)  # 删除临时文件夹
    os.startfile(os.path.join(get_application_path(), f'main-v{update_version}.exe'))  # 启动新版本
    os._exit(0)  # 关闭更新程序

# 重启
def show_restart_prompt():
    global restart_window
    restart_window = tk.Tk()
    restart_window.title("更新完成")
    
    tk.Label(restart_window, text="更新已完成，是否立即重启？").pack(pady=10)
    tk.Button(restart_window, text="重启", command=lambda: (restart_window.destroy(), restart_application())).pack(pady=10)
    tk.Button(restart_window, text="稍后重启", command=restart_window.destroy).pack(pady=5)
    restart_window.mainloop()
if __name__ == "__main__":
    root = tk.Tk()  # 创建主窗口
    root.withdraw()  # 隐藏主窗口，因为我们不需要它
    update_version = "1.1"  # 假设新版本为 1.1，实际情况可以根据需要动态获取
    latest_version, url, content = get_update_info()
    if latest_version:
        show_update_prompt(latest_version, url,content)
    root.mainloop()  # 启动主事件循环
