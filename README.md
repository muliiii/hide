<p align="center">
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-blue" alt="license MIT"></a>
    <a href="https://qm.qq.com/q/JdiwPsYpCG"><img src="https://img.shields.io/badge/QQ%E7%BE%A4-955567942-green" alt="QQ群：955567942"></a>
</p>

### 帖子：https://www.52pojie.cn/thread-1963457-1-1.html

## 使用教程

`git pull`</br>
`pip install xx`</br>
`python .\my-v1.0.py`

## 打包exe：

> ### 使用
>
> `pyinstaller --onefile --noconsole my.py 命令打包exe`</br>
>
> ### 带图标：
>
> `pyinstaller --onefile --noconsole -i icon\favicon.ico .\my-v1.3.py`</br>

> ### 兼容win7：
>
> `-D -p C:\Windows\System32\downlevel -F -w --hidden-import=win32timezone`</br>
>
> ### 完整
>
> `pyinstaller -D -p C:\Windows\System32\downlevel -F -w --hidden-import=win32timezone --onefile --noconsole -i icon\favicon.ico my-v1.5.py`

### upx：https://github.com/upx/upx/releases/

> #### 压缩：
>
> `pyinstaller -D -p C:\Windows\System32\downlevel -F -w --hidden-import=win32timezone --onefile --noconsole -i icon\favicon.ico my-v1.4.py --upx-dir D:\下载\upx-4.2.4-win64\`

### 更换py版本打包

#### 创建新虚拟环境

`python -m venv new_env`

#### 激活新虚拟环境

`new_env\Scripts\activate # Windows`

#### 安装所需依赖

`pip install pyinstaller`

#### 退出虚拟环境

`deactivate`

## 免责声明

窗口隐藏工具程序是免费开源的产品，仅用于学习交流使用！       
不可用于任何违反`中华人民共和国(含台湾省)`或`使用者所在地区`法律法规的用途。      
因为作者即本人仅完成代码的开发和开源活动`(开源即任何人都可以下载使用)`，从未参与用户的任何运营和盈利活动。    
且不知晓用户后续将`程序源代码`用于何种用途，故用户使用过程中所带来的任何法律责任即由用户自己承担。      

## License

窗口隐藏工具 [MIT license](https://opensource.org/licenses/MIT).


**如果对你有帮助，不妨请作者喝杯咖啡**
![](https://youngreeds.com/code.png)
