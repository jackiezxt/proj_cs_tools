import sys
import os
from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
from maya_tools.alembic_exporter import export_alembic

class AlembicExporterGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alembic 导出工具")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # 添加说明标签
        info_label = QtWidgets.QLabel("此工具将自动导出场景中的角色模型到 Alembic 缓存")
        layout.addWidget(info_label)
        
        # 添加导出按钮
        export_btn = QtWidgets.QPushButton("导出 Alembic")
        export_btn.clicked.connect(self.export)
        layout.addWidget(export_btn)
        
        # 添加状态显示
        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)
        
    def export(self):
        try:
            export_alembic()
            self.status_label.setText("导出成功！")
            self.status_label.setStyleSheet("color: green")
        except Exception as e:
            self.status_label.setText(f"导出失败：{str(e)}")
            self.status_label.setStyleSheet("color: red")

def show_window():
    # 如果已存在窗口，则关闭
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(widget, AlembicExporterGUI):
            widget.close()
    
    # 创建新窗口
    window = AlembicExporterGUI()
    window.show()
    return window