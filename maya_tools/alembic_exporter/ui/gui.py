import sys
import os
from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
from maya_tools.alembic_exporter import export_char_alembic, export_prop_alembic

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
    window.show()
    return window