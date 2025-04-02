# Maya病毒扫描与清理工具

## 简介

这是一个用于扫描和清理Maya文件中病毒代码的工具。它能够检测和移除常见的Maya脚本病毒，如breed_gene和其他恶意脚本节点。

## 功能特点

- 扫描单个Maya文件或整个目录
- 识别并清理恶意脚本节点
- 保留合法的脚本节点
- 自动创建文件备份
- 图形界面和命令行两种操作方式
- 详细的日志记录

## 使用方法

### 图形界面

双击`run.bat`启动图形界面。界面支持：

- 单文件模式：选择单个Maya文件进行扫描和清理
- 文件夹模式：扫描整个文件夹内的Maya文件，支持递归扫描子文件夹

### 命令行

基本用法：

```
mayapy main.py [选项]
```

参数说明：

```
--path PATH          要扫描的文件或文件夹路径
--recursive          递归扫描文件夹
--scan-startup       扫描启动脚本
--clean              清理感染的文件
--backup             在清理前备份文件
--scene-cleanup      清理当前Maya场景中的病毒
--system-cleanup     清理系统中的Maya垃圾文件和插件(独立模式)
--gui                启动图形界面模式
```

示例：

```
# 扫描单个文件
mayapy main.py --path C:\path\to\file.ma

# 递归扫描文件夹并清理感染的文件
mayapy main.py --path C:\path\to\folder --recursive --clean

# 扫描并清理启动脚本
mayapy main.py --scan-startup --clean

# 只进行系统清理
mayapy main.py --system-cleanup

# 只进行场景清理（需要在Maya内运行）
mayapy main.py --scene-cleanup
```

### 快速使用

1. **扫描文件**：将Maya文件拖放到`scan_file.bat`上
2. **清理文件**：将Maya文件拖放到`scan_and_clean.bat`上

## 病毒检测原理

工具检测以下恶意代码特征：

1. 可疑的脚本节点（包含特定的恶意代码模式）
2. 可疑的scriptJob（设置为在场景打开时执行）
3. 未知的插件加载命令
4. 未知的节点类型
5. 恶意的编辑器回调
6. 修改的初始节点
7. 系统中的恶意启动脚本和插件

### 已知的恶意代码特征

- 文件写入操作（例如`open()`、`file.write()`）
- 网络连接操作（例如`urllib`、`requests`）
- 加密或混淆的JavaScript代码
- 编码过的Base64或十六进制字符串
- 系统命令执行（例如`os.system()`、`subprocess`）
- 特定的已知恶意函数名或变量名

## 免责声明

本工具仅用于检测和清理已知的Maya病毒模式。不能保证能够检测和清理所有类型的恶意代码。请在使用前备份重要文件。

## 运行环境

- Maya 2018-2024 自带的Python (mayapy.exe)
- 或独立的Python环境 (需要PySide2/PySide6/PyQt5)

## 错误排查

如果遇到问题：
1. 检查日志文件夹中的最新日志
2. 确保Maya安装路径正确
3. 尝试以管理员身份运行 