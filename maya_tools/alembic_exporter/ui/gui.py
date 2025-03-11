import sys
import os
from PySide2 import QtWidgets, QtCore
import maya.cmds as mc
from maya_tools.alembic_exporter.export import export_char_alembic, export_prop_alembic, export_fur_alembic

class AlembicExporterGUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        # 使用传入的父窗口（通常是Maya主窗口）
        super(AlembicExporterGUI, self).__init__(parent)
        
        # 设置窗口标志，保持作为独立窗口同时附属于父窗口
        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.CustomizeWindowHint | 
                           QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint)
        
        self.setWindowTitle("Alembic缓存导出工具")
        self.setMinimumWidth(400)
        self.setFixedHeight(180)  # 设置固定高度，使界面更紧凑
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 说明标签
        info_label = QtWidgets.QLabel("此工具用于导出角色、道具及毛发生长面的Alembic缓存")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)
        
        # 按钮布局
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 导出角色按钮
        self.export_char_btn = QtWidgets.QPushButton("导出角色缓存")
        self.export_char_btn.setToolTip("导出场景中的角色模型为Alembic缓存")
        self.export_char_btn.clicked.connect(self.export_character)
        button_layout.addWidget(self.export_char_btn)
        
        # 导出道具按钮
        self.export_prop_btn = QtWidgets.QPushButton("导出道具缓存")
        self.export_prop_btn.setToolTip("导出场景中的道具模型为Alembic缓存")
        self.export_prop_btn.clicked.connect(self.export_prop)
        button_layout.addWidget(self.export_prop_btn)
        
        # 添加到主布局
        main_layout.addLayout(button_layout)
        
        # 毛发生长面按钮布局
        fur_button_layout = QtWidgets.QHBoxLayout()
        fur_button_layout.setSpacing(10)
        
        # 导出毛发生长面按钮
        self.export_fur_btn = QtWidgets.QPushButton("导出 Xgen 生长面 Fur_Grp")
        self.export_fur_btn.setToolTip("导出场景中的毛发生长面(Fur_Grp)为Alembic缓存")
        self.export_fur_btn.clicked.connect(self.export_fur)
        fur_button_layout.addWidget(self.export_fur_btn)
        
        # 添加到主布局
        main_layout.addLayout(fur_button_layout)
        
        # 状态标签
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)
        
        # 添加弹性空间
        main_layout.addStretch()
        
    def export_character(self):
        """导出角色缓存"""
        try:
            files = export_char_alembic()
            if files:
                self.status_label.setText(f"成功导出 {len(files)} 个角色的 Alembic 缓存")
            else:
                self.status_label.setText("没有找到可导出的角色模型")
        except Exception as e:
            self.status_label.setText(f"导出失败: {str(e)}")
            
    def export_prop(self):
        """导出道具缓存"""
        try:
            files = export_prop_alembic()
            if files:
                self.status_label.setText(f"成功导出 {len(files)} 个道具的 Alembic 缓存")
            else:
                self.status_label.setText("没有找到可导出的道具模型")
        except Exception as e:
            self.status_label.setText(f"导出失败: {str(e)}")
            
    def export_fur(self):
        """导出毛发生长面缓存"""
        try:
            files = export_fur_alembic()
            if files:
                self.status_label.setText(f"成功导出 {len(files)} 个毛发生长面 Fur_Grp 的 Alembic 缓存")
            else:
                self.status_label.setText("没有找到可导出的毛发生长面 Fur_Grp")
        except Exception as e:
            self.status_label.setText(f"导出失败: {str(e)}")

def show_window():
    """显示Alembic导出工具窗口"""
    # 首先获取Maya主窗口作为父窗口
    maya_main_window = None
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if obj.objectName() == "MayaWindow":
            maya_main_window = obj
            break
    
    # 关闭已有窗口
    for widget in QtWidgets.QApplication.allWidgets():
        if isinstance(widget, AlembicExporterGUI):
            widget.close()
    
    # 创建新窗口，使用Maya主窗口作为父窗口
    window = AlembicExporterGUI(parent=maya_main_window)
    
    # 确保窗口尺寸合适
    window.resize(450, window.height())
    
    # 显示窗口并放置在合适位置
    window.show()
    
    # 将窗口移动到Maya窗口中心附近但偏右上方，这样不会挡住场景视图
    if maya_main_window:
        center = maya_main_window.geometry().center()
        window.move(center.x() - window.width()//2 + 200, 
                   center.y() - maya_main_window.height()//2 + 150)
    
    # 确保窗口在前
    window.raise_()
    window.activateWindow()
    
    return window