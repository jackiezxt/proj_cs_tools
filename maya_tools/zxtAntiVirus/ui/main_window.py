#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from PySide2 import QtWidgets, QtCore, QtGui

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.scanner import VirusScanner
from core.cleaner import VirusCleaner
from utils.logger import Logger

class MainWindow(QtWidgets.QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("Maya Virus Scanner")
        self.resize(800, 600)
        
        # 创建中央部件
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        
        # 创建标签
        self.title_label = QtWidgets.QLabel("Maya文件病毒扫描与清理工具")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        # 设置标题标签的字体
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.title_label.setFont(font)
        
        # 创建选择模式组
        self.mode_group = QtWidgets.QGroupBox("扫描模式")
        self.mode_layout = QtWidgets.QHBoxLayout()
        self.file_mode_radio = QtWidgets.QRadioButton("单文件模式")
        self.folder_mode_radio = QtWidgets.QRadioButton("文件夹模式")
        self.file_mode_radio.setChecked(True)
        self.mode_layout.addWidget(self.file_mode_radio)
        self.mode_layout.addWidget(self.folder_mode_radio)
        self.mode_group.setLayout(self.mode_layout)
        
        # 创建文件选择组件
        self.file_group = QtWidgets.QGroupBox("文件选择")
        self.file_layout = QtWidgets.QHBoxLayout()
        self.file_path = QtWidgets.QLineEdit()
        self.browse_file_btn = QtWidgets.QPushButton("浏览文件...")
        self.file_layout.addWidget(self.file_path)
        self.file_layout.addWidget(self.browse_file_btn)
        self.file_group.setLayout(self.file_layout)
        
        # 创建文件夹选择组件
        self.folder_group = QtWidgets.QGroupBox("文件夹选择")
        self.folder_layout = QtWidgets.QVBoxLayout()
        
        # 文件夹路径选择
        self.folder_path_layout = QtWidgets.QHBoxLayout()
        self.folder_path = QtWidgets.QLineEdit()
        self.browse_folder_btn = QtWidgets.QPushButton("浏览文件夹...")
        self.folder_path_layout.addWidget(self.folder_path)
        self.folder_path_layout.addWidget(self.browse_folder_btn)
        
        # 递归选项
        self.recursive_check = QtWidgets.QCheckBox("递归扫描子文件夹")
        self.recursive_check.setChecked(True)
        
        # 添加到文件夹布局
        self.folder_layout.addLayout(self.folder_path_layout)
        self.folder_layout.addWidget(self.recursive_check)
        self.folder_group.setLayout(self.folder_layout)
        
        # 默认隐藏文件夹选择组
        self.folder_group.setVisible(False)
        
        # 创建按钮
        self.scan_btn = QtWidgets.QPushButton("扫描")
        self.clean_btn = QtWidgets.QPushButton("一键清理")
        
        # 设置按钮大小
        self.scan_btn.setMinimumHeight(40)
        self.clean_btn.setMinimumHeight(40)
        
        # 创建日志显示区域
        self.log_group = QtWidgets.QGroupBox("操作日志")
        self.log_layout = QtWidgets.QVBoxLayout()
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_layout.addWidget(self.log_text)
        self.log_group.setLayout(self.log_layout)
        
        # 设置按钮布局
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.scan_btn)
        self.button_layout.addWidget(self.clean_btn)
        
        # 添加组件到主布局
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.mode_group)
        self.main_layout.addWidget(self.file_group)
        self.main_layout.addWidget(self.folder_group)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.log_group)
        
        # 设置按钮状态
        self.clean_btn.setEnabled(False)
        
        # 连接信号和槽
        self.file_mode_radio.toggled.connect(self.toggle_mode)
        self.folder_mode_radio.toggled.connect(self.toggle_mode)
        self.browse_file_btn.clicked.connect(self.browse_file)
        self.browse_folder_btn.clicked.connect(self.browse_folder)
        self.scan_btn.clicked.connect(self.scan)
        self.clean_btn.clicked.connect(self.clean)
        
        # 初始化变量
        self.current_file = ""
        self.current_folder = ""
        self.scan_results = None
        self.infected_files = []
        
        # 设置日志
        self.setup_logger()
    
    def toggle_mode(self):
        """切换扫描模式"""
        is_file_mode = self.file_mode_radio.isChecked()
        self.file_group.setVisible(is_file_mode)
        self.folder_group.setVisible(not is_file_mode)
        self.clean_btn.setEnabled(False)
        
    def setup_logger(self):
        """设置日志记录器"""
        import datetime
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = os.path.join(log_dir, "gui_{}.log".format(timestamp))
        self.logger = Logger(self.log_path)
        self.logger.info("GUI started")
    
    def browse_file(self):
        """浏览并选择文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择Maya文件", "", "Maya Files (*.ma *.mb);;All Files (*)"
        )
        
        if file_path:
            self.file_path.setText(file_path)
            self.current_file = file_path
            self.clean_btn.setEnabled(False)
            self.log_message("已选择文件: {}".format(file_path))
    
    def browse_folder(self):
        """浏览并选择文件夹"""
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择要扫描的文件夹", ""
        )
        
        if folder_path:
            self.folder_path.setText(folder_path)
            self.current_folder = folder_path
            self.clean_btn.setEnabled(False)
            self.log_message("已选择文件夹: {}".format(folder_path))
    
    def scan(self):
        """执行扫描操作"""
        if self.file_mode_radio.isChecked():
            self.scan_file()
        else:
            self.scan_folder()
    
    def clean(self):
        """执行清理操作"""
        if self.file_mode_radio.isChecked():
            self.clean_file()
        else:
            self.clean_folder()
    
    def scan_file(self):
        """扫描文件"""
        file_path = self.file_path.text()
        
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择要扫描的文件")
            return
        
        if not os.path.exists(file_path):
            QtWidgets.QMessageBox.warning(self, "错误", "文件不存在: {}".format(file_path))
            return
        
        try:
            self.log_message("开始扫描文件: {}".format(file_path))
            self.logger.info("Scanning file: {}".format(file_path))
            
            # 创建扫描器并扫描文件
            scanner = VirusScanner(self.log_path)
            self.scan_results = scanner.scan_file(file_path)
            
            # 解析扫描结果
            if self.scan_results and self.scan_results["summary"].get("infected", False):
                self.log_message("扫描完成，发现可疑代码!")
                self.logger.info("Scan complete, file is infected")
                
                # 启用清理按钮
                self.clean_btn.setEnabled(True)
                
                # 显示详细信息
                for i, node in enumerate(self.scan_results.get("infected_nodes", []), 1):
                    self.log_message("可疑节点 #{}: {}".format(i, node.get("name", "未知节点")))
                    self.log_message("  - 类型: {}".format(node.get("type", "未知")))
                    if "line_number" in node:
                        self.log_message("  - 行号: {}".format(node["line_number"]))
            else:
                self.log_message("扫描完成，未发现问题。")
                self.logger.info("Scan complete, file is clean")
                self.clean_btn.setEnabled(False)
        
        except Exception as e:
            self.log_message("扫描出错: {}".format(str(e)))
            self.logger.error("Error during scan: {}".format(str(e)))
            import traceback
            traceback.print_exc()
    
    def scan_folder(self):
        """扫描文件夹"""
        folder_path = self.folder_path.text()
        
        if not folder_path:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择要扫描的文件夹")
            return
        
        if not os.path.exists(folder_path):
            QtWidgets.QMessageBox.warning(self, "错误", "文件夹不存在: {}".format(folder_path))
            return
        
        try:
            recursive = self.recursive_check.isChecked()
            self.log_message("开始扫描文件夹: {}{}".format(
                folder_path, " (包含子文件夹)" if recursive else ""
            ))
            self.logger.info("Scanning folder: {} (recursive={})".format(folder_path, recursive))
            
            # 创建扫描器并扫描文件夹
            scanner = VirusScanner(self.log_path)
            results = scanner.scan_folder(folder_path, recursive=recursive)
            
            # 解析扫描结果
            scanned = results.get("files_scanned", 0)
            infected = results.get("files_infected", 0)
            self.infected_files = results.get("infected_files", [])
            
            self.log_message("扫描完成，共扫描 {} 个文件，发现 {} 个受感染文件".format(scanned, infected))
            self.logger.info("Scan complete, scanned {} files, found {} infected files".format(scanned, infected))
            
            # 显示详细信息
            if infected > 0:
                self.clean_btn.setEnabled(True)
                self.log_message("\n受感染文件列表:")
                for i, file_info in enumerate(self.infected_files, 1):
                    file_path = file_info.get("file", "")
                    self.log_message("{}. {}".format(i, file_path))
            else:
                self.clean_btn.setEnabled(False)
        
        except Exception as e:
            self.log_message("扫描出错: {}".format(str(e)))
            self.logger.error("Error during scan: {}".format(str(e)))
            import traceback
            traceback.print_exc()
    
    def clean_file(self):
        """清理文件"""
        if not self.current_file or not self.scan_results:
            QtWidgets.QMessageBox.warning(self, "警告", "请先扫描文件")
            return
        
        # 确认清理
        reply = QtWidgets.QMessageBox.question(
            self, "确认", "是否要清理此文件？建议先备份。",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                self.log_message("开始清理文件: {}".format(self.current_file))
                self.logger.info("Cleaning file: {}".format(self.current_file))
                
                # 创建清理器并清理文件
                cleaner = VirusCleaner(self.log_path)
                cleaner.clean_file(self.current_file, make_backup=True)
                
                self.log_message("清理完成!")
                self.logger.info("Cleaning complete")
                
                # 禁用清理按钮
                self.clean_btn.setEnabled(False)
                
                # 提示成功
                QtWidgets.QMessageBox.information(self, "成功", "文件清理完成")
            
            except Exception as e:
                self.log_message("清理出错: {}".format(str(e)))
                self.logger.error("Error during cleaning: {}".format(str(e)))
                QtWidgets.QMessageBox.critical(self, "错误", "文件清理失败: {}".format(str(e)))
    
    def clean_folder(self):
        """清理文件夹中的受感染文件"""
        if not self.infected_files:
            QtWidgets.QMessageBox.warning(self, "警告", "请先扫描文件夹")
            return
        
        # 确认清理
        infected_count = len(self.infected_files)
        reply = QtWidgets.QMessageBox.question(
            self, "确认", "是否要清理发现的 {} 个受感染文件？建议先备份。".format(infected_count),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                self.log_message("开始清理受感染文件...")
                self.logger.info("Starting to clean infected files")
                
                # 创建清理器
                cleaner = VirusCleaner(self.log_path)
                cleaned_count = 0
                
                # 逐个清理文件
                for file_info in self.infected_files:
                    file_path = file_info.get("file")
                    if file_path and file_path.lower().endswith(('.ma', '.mb')):
                        self.log_message("清理文件: {}".format(file_path))
                        self.logger.info("Cleaning file: {}".format(file_path))
                        try:
                            cleaner.clean_file(file_path, make_backup=True)
                            cleaned_count += 1
                        except Exception as e:
                            self.log_message("清理文件失败: {}, 错误: {}".format(file_path, str(e)))
                            self.logger.error("Failed to clean file: {}, error: {}".format(file_path, str(e)))
                
                self.log_message("清理完成，成功清理 {} 个文件".format(cleaned_count))
                self.logger.info("Cleaning complete, successfully cleaned {} files".format(cleaned_count))
                
                # 禁用清理按钮
                self.clean_btn.setEnabled(False)
                
                # 提示成功
                QtWidgets.QMessageBox.information(self, "成功", "清理完成，成功清理 {} 个文件".format(cleaned_count))
                
            except Exception as e:
                self.log_message("批量清理过程中出错: {}".format(str(e)))
                self.logger.error("Error during batch cleaning: {}".format(str(e)))
                QtWidgets.QMessageBox.critical(self, "错误", "批量清理失败: {}".format(str(e)))
    
    def log_message(self, message):
        """在UI上记录消息"""
        self.log_text.append(message) 