import sys
import os
from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
from maya_tools.alembic_exporter import export_char_alembic, export_prop_alembic

class AlembicExporterGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alembic 导出工具")
        
        # 设置窗口标志，使其始终保持在前
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # 添加说明标签
        info_label = QtWidgets.QLabel("此工具将自动导出场景中的角色模型到 Alembic 缓存")
        layout.addWidget(info_label)

        # 添加按钮布局
        btn_layout = QtWidgets.QHBoxLayout()

        # 添加导出角色按钮
        export_char_btn = QtWidgets.QPushButton("导出角色 Alembic")
        export_char_btn.clicked.connect(self.export_character)
        btn_layout.addWidget(export_char_btn)

        # 添加导出道具按钮
        export_prop_btn = QtWidgets.QPushButton("导出道具 Alembic")
        export_prop_btn.clicked.connect(self.export_prop)
        btn_layout.addWidget(export_prop_btn)

        layout.addLayout(btn_layout)
        
        # 添加状态显示
        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)
        
    def export_character(self):
        try:
            export_char_alembic()
            self.status_label.setText("角色导出成功！")
            self.status_label.setStyleSheet("color: green")
        except Exception as e:
            self.status_label.setText(f"角色导出失败：{str(e)}")
            self.status_label.setStyleSheet("color: red")

    def export_prop(self):
        try:
            export_prop_alembic()
            self.status_label.setText("道具导出成功！")
            self.status_label.setStyleSheet("color: green")
        except Exception as e:
            self.status_label.setText(f"道具导出失败：{str(e)}")
            self.status_label.setStyleSheet("color: red")

    def export(self):
        # 保留原有方法，调用导出角色的功能
        self.export_character()

def show_window():
    # 如果已存在窗口，则关闭
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(widget, AlembicExporterGUI):
            widget.close()
    
    # 创建新窗口
    window = AlembicExporterGUI()
    
    # 获取主窗口的位置和大小，用于计算居中位置
    main_window = None
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if widget.objectName() == "MayaWindow":
            main_window = widget
            break
    
    # 如果找到Maya主窗口，则将我们的窗口居中显示
    if main_window:
        center_point = main_window.geometry().center()
        window_rect = window.geometry()
        window_rect.moveCenter(center_point)
        window.setGeometry(window_rect)
    
    window.show()
    window.raise_()  # 确保窗口在前端显示
    window.activateWindow()  # 激活窗口
    
    return window