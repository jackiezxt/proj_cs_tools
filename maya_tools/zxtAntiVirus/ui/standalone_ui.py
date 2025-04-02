#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立用户界面模块 - 用于显示病毒扫描和清理界面
"""
import os
import sys
import traceback

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 尝试导入Qt库
try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    try:
        from PySide import QtGui, QtCore
        QtWidgets = QtGui
    except ImportError:
        try:
            from PyQt5 import QtWidgets, QtCore, QtGui
        except ImportError:
            try:
                from PyQt4 import QtGui, QtCore
                QtWidgets = QtGui
            except ImportError:
                print("错误：无法导入任何Qt库（PySide2/PySide/PyQt5/PyQt4）")
                print("请安装以下任一Qt包：")
                print("- pip install PySide2")
                print("- pip install PyQt5")
                raise

from core.scanner import VirusScanner
from core.cleaner import VirusCleaner
from utils.logger import Logger
from ui.main_window import MainWindow

def show_ui(log_path=None):
    """显示独立UI界面"""
    logger = Logger(log_path) if log_path else Logger()
    logger.info("启动独立UI界面")
    
    # 创建Qt应用程序（如果尚未创建）
    app = None
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    
    try:
        # 创建主窗口
        window = MainWindow(logger=logger)
        window.setObjectName("VirusScannerWindow")
        window.setWindowTitle("Maya病毒扫描工具")
        
        # 设置窗口属性
        window.setWindowFlags(QtCore.Qt.Window)
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        # 显示窗口
        window.show()
        
        # 如果我们创建了应用，则运行事件循环
        if app:
            sys.exit(app.exec_())
        
        return window
    
    except Exception as e:
        logger.error(f"显示UI界面时出错: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"显示UI界面时出错: {str(e)}")
        print("检查是否已安装GUI所需的Qt库(PySide2/PyQt5)")
        if app:
            sys.exit(1)
        return None 