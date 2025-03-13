import sys
import os
from PySide2 import QtWidgets, QtCore, QtGui
import maya.cmds as mc
from maya_tools.alembic_exporter.export import export_char_alembic, export_prop_alembic, export_fur_alembic
from maya_tools.alembic_exporter.core.xgen_guides import XGenGuidesManager

class XGenGuidesDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(XGenGuidesDialog, self).__init__(parent)
        self.setWindowTitle("导出 XGen Guides")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)
        
        # 创建功能管理器实例
        self.guides_manager = XGenGuidesManager()
        
        # 编译正则表达式
        self.asset_id_pattern = QtCore.QRegExp("c[0-9]{3}")
        self.collection_pattern = QtCore.QRegExp("(?i)col_[a-z][a-z0-9_]*")
        
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主布局
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建左侧布局（包含输入框和列表）
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.setSpacing(5)
        
        # 创建输入框布局
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(5)
        form_layout.setContentsMargins(0, 0, 0, 5)
        
        # 资产ID输入框
        self.asset_id_edit = QtWidgets.QLineEdit()
        self.asset_id_edit.setPlaceholderText("示例: c001, c002")
        self.asset_id_edit.setToolTip("资产编号, 如:c001 (仅支持c+3位数字格式)")
        self.asset_id_edit.setMaxLength(4)  # 限制最大长度为4个字符
        
        # 创建验证器
        validator = QtGui.QRegExpValidator(self.asset_id_pattern)
        self.asset_id_edit.setValidator(validator)
        
        # 添加输入框状态变化处理
        self.asset_id_edit.textChanged.connect(self.on_asset_id_changed)
        
        form_layout.addRow("资产ID:", self.asset_id_edit)
        
        # Collection名称输入框
        self.collection_edit = QtWidgets.QLineEdit()
        self.collection_edit.setPlaceholderText("示例: COL_Hair, col_hair")
        self.collection_edit.setToolTip("Collection名称, 如: COL_Hair, col_hair (仅支持单个Collection)")
        
        # 添加Collection输入框状态变化处理
        self.collection_edit.textChanged.connect(self.on_collection_changed)
        
        form_layout.addRow("Collection:", self.collection_edit)
        
        left_layout.addLayout(form_layout)
        
        # 创建列表部件
        self.list_widget = QtWidgets.QListWidget()
        left_layout.addWidget(self.list_widget)
        
        main_layout.addLayout(left_layout)
        
        # 创建按钮布局
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(3)
        
        # 添加按钮
        self.add_btn = QtWidgets.QPushButton("添加")
        self.add_btn.setFixedSize(60, 25)
        self.add_btn.clicked.connect(self.add_guides)
        button_layout.addWidget(self.add_btn)
        
        # 导出按钮
        self.export_btn = QtWidgets.QPushButton("导出")
        self.export_btn.setFixedSize(60, 25)
        self.export_btn.clicked.connect(self.export_guides)
        button_layout.addWidget(self.export_btn)
        
        # 清空按钮
        self.clear_btn = QtWidgets.QPushButton("清空")
        self.clear_btn.setFixedSize(60, 25)
        self.clear_btn.clicked.connect(self.clear_list)
        button_layout.addWidget(self.clear_btn)
        
        # 添加弹性空间
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 设置窗口最小尺寸
        self.setMinimumWidth(400)  # 增加宽度以适应输入框
        
    def on_asset_id_changed(self, text):
        """处理资产ID输入框的文本变化"""
        if text:
            # 检查是否匹配模式
            if not self.asset_id_pattern.exactMatch(text):
                self.asset_id_edit.setStyleSheet("QLineEdit { background-color: #FFE4E1; }")
                self.asset_id_edit.setToolTip("格式错误: 请输入c+3位数字的格式, 如c001")
            else:
                self.asset_id_edit.setStyleSheet("")
                self.asset_id_edit.setToolTip("资产编号, 如:c001")
        else:
            self.asset_id_edit.setStyleSheet("")
            self.asset_id_edit.setToolTip("资产编号, 如:c001")

    def on_collection_changed(self, text):
        """处理Collection输入框的文本变化"""
        if text:
            # 检查是否包含逗号或多个Collection
            if "," in text or text.lower().count("col_") > 1:
                self.collection_edit.setStyleSheet("QLineEdit { background-color: #FFE4E1; }")
                self.collection_edit.setToolTip("格式错误: 只能输入单个Collection, 如: COL_Hair")
                return
            
            # 检查是否以col_开头（不区分大小写）
            if len(text) >= 4:
                if not text.lower().startswith("col_"):
                    self.collection_edit.setStyleSheet("QLineEdit { background-color: #FFE4E1; }")
                    self.collection_edit.setToolTip("格式错误: 请使用COL_或col_开头加名称")
                # 检查COL_后面是否直接跟数字
                elif len(text) > 4 and text[4].isdigit():
                    self.collection_edit.setStyleSheet("QLineEdit { background-color: #FFE4E1; }")
                    self.collection_edit.setToolTip("格式错误: COL_后必须是字母开头，如: COL_Hair")
                else:
                    self.collection_edit.setStyleSheet("")
                    self.collection_edit.setToolTip("Collection名称, 如: COL_Hair, col_hair")
            else:
                self.collection_edit.setStyleSheet("")
                self.collection_edit.setToolTip("Collection名称, 如: COL_Hair, col_hair")
        else:
            self.collection_edit.setStyleSheet("")
            self.collection_edit.setToolTip("Collection名称, 如: COL_Hair, col_hair")

    def validate_inputs(self):
        """验证输入框内容"""
        asset_id = self.asset_id_edit.text().strip()
        collection = self.collection_edit.text().strip()
        
        if not asset_id:
            QtWidgets.QMessageBox.warning(self, "警告", "请输入资产ID")
            self.asset_id_edit.setFocus()
            return False
            
        if not self.asset_id_pattern.exactMatch(asset_id):
            QtWidgets.QMessageBox.warning(self, "警告", "资产ID格式错误, 请使用c+3位数字的格式, 如: c001")
            self.asset_id_edit.setFocus()
            return False
            
        if not collection:
            QtWidgets.QMessageBox.warning(self, "警告", "请输入Collection名称")
            self.collection_edit.setFocus()
            return False
            
        if "," in collection or collection.lower().count("col_") > 1:
            QtWidgets.QMessageBox.warning(self, "警告", "只能输入单个Collection名称")
            self.collection_edit.setFocus()
            return False
            
        # 检查collection格式
        if not collection.lower().startswith("col_"):
            QtWidgets.QMessageBox.warning(self, "警告", "Collection格式错误, 请使用COL_或col_开头加名称")
            self.collection_edit.setFocus()
            return False
            
        # 检查COL_后面是否是字母开头
        if len(collection) <= 4 or not collection[4].isalpha():
            QtWidgets.QMessageBox.warning(self, "警告", "Collection格式错误, COL_后必须是字母开头，如: COL_Hair")
            self.collection_edit.setFocus()
            return False
            
        return True
        
    def add_guides(self):
        """添加选中的XGen Guides到列表"""
        selected_guides = self.guides_manager.get_selected_guides()
        if not selected_guides:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择要添加的guides物体")
            return
            
        # 添加到列表, 避免重复
        for guide in selected_guides:
            items = self.list_widget.findItems(guide, QtCore.Qt.MatchExactly)
            if not items:
                self.list_widget.addItem(guide)
        
    def export_guides(self):
        """导出列表中的XGen Guides"""
        # 首先验证输入
        if not self.validate_inputs():
            return
            
        if self.list_widget.count() == 0:
            QtWidgets.QMessageBox.warning(self, "警告", "列表为空, 请先添加要导出的guides物体")
            return
            
        guides_list = []
        for i in range(self.list_widget.count()):
            guides_list.append(self.list_widget.item(i).text())
            
        try:
            # 获取输入框的值
            asset_id = self.asset_id_edit.text().strip()
            collection = self.collection_edit.text().strip()
            
            result = self.guides_manager.export_guides(guides_list, asset_id=asset_id, collection=collection)
            if result:
                QtWidgets.QMessageBox.information(self, "成功", "成功导出guides缓存")
            else:
                QtWidgets.QMessageBox.warning(self, "警告", "导出失败, 请检查guides物体是否有效")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"导出过程中发生错误: {str(e)}")

    def clear_list(self):
        """清空列表"""
        if self.list_widget.count() > 0:
            reply = QtWidgets.QMessageBox.question(
                self,
                "确认",
                "确定要清空列表吗？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.list_widget.clear()

class AlembicExporterGUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        # 使用传入的父窗口（通常是Maya主窗口）
        super(AlembicExporterGUI, self).__init__(parent)
        
        # 设置窗口标志, 保持作为独立窗口同时附属于父窗口
        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.CustomizeWindowHint | 
                           QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint)
        
        self.setWindowTitle("Alembic缓存导出工具")
        self.setMinimumWidth(380)  # 减小最小宽度
        self.setFixedHeight(190)  # 减小窗口高度
        self.setup_ui()
        
        # 创建XGen Guides导出窗口实例
        self.xgen_guides_dialog = None
        
    def setup_ui(self):
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 减小窗口边缘间距
        main_layout.setSpacing(3)  # 进一步减小主布局间距
        
        # 说明标签
        info_label = QtWidgets.QLabel("此工具用于导出角色、道具及毛发生长面的Alembic缓存")
        info_label.setWordWrap(True)
        info_label.setContentsMargins(0, 0, 0, 0)  # 移除标签边距
        main_layout.addWidget(info_label)
        
        # 设置按钮的固定大小
        button_size = QtCore.QSize(170, 28)  # 调整按钮大小
        
        # 创建动画分组
        anim_group = QtWidgets.QGroupBox("动画环节")
        anim_layout = QtWidgets.QVBoxLayout(anim_group)
        anim_layout.setContentsMargins(3, 8, 3, 3)  # 减小分组内边距
        anim_layout.setSpacing(3)  # 减小分组内间距
        
        # 创建动画按钮网格布局
        anim_grid = QtWidgets.QGridLayout()
        anim_grid.setSpacing(3)  # 减小网格间距
        anim_grid.setHorizontalSpacing(3)  # 设置水平间距
        
        # 导出角色按钮
        self.export_char_btn = QtWidgets.QPushButton("导出角色缓存")
        self.export_char_btn.setToolTip("导出场景中的角色模型为Alembic缓存")
        self.export_char_btn.clicked.connect(self.export_character)
        self.export_char_btn.setFixedSize(button_size)
        anim_grid.addWidget(self.export_char_btn, 0, 0)
        
        # 导出道具按钮
        self.export_prop_btn = QtWidgets.QPushButton("导出道具缓存")
        self.export_prop_btn.setToolTip("导出场景中的道具模型为Alembic缓存")
        self.export_prop_btn.clicked.connect(self.export_prop)
        self.export_prop_btn.setFixedSize(button_size)
        anim_grid.addWidget(self.export_prop_btn, 0, 1)
        
        # 导出毛发生长面按钮
        self.export_fur_btn = QtWidgets.QPushButton("导出 Xgen 生长面")
        self.export_fur_btn.setToolTip("导出场景中的毛发生长面(Fur_Grp)为Alembic缓存")
        self.export_fur_btn.clicked.connect(self.export_fur)
        self.export_fur_btn.setFixedSize(button_size)
        anim_grid.addWidget(self.export_fur_btn, 1, 0)
        
        anim_layout.addLayout(anim_grid)
        main_layout.addWidget(anim_group)
        
        # 创建CFX分组
        cfx_group = QtWidgets.QGroupBox("CFX环节")
        cfx_layout = QtWidgets.QVBoxLayout(cfx_group)
        cfx_layout.setContentsMargins(3, 8, 3, 3)  # 减小分组内边距
        cfx_layout.setSpacing(3)  # 减小分组内间距
        
        # 创建CFX按钮网格布局
        cfx_grid = QtWidgets.QGridLayout()
        cfx_grid.setSpacing(3)  # 减小网格间距
        cfx_grid.setHorizontalSpacing(3)  # 设置水平间距
        
        # 导出Cloth缓存按钮（禁用状态）
        self.export_cloth_btn = QtWidgets.QPushButton("导出 Cloth 缓存")
        self.export_cloth_btn.setToolTip("导出场景中的布料缓存为Alembic缓存（功能开发中）")
        self.export_cloth_btn.setFixedSize(button_size)
        self.export_cloth_btn.setEnabled(False)  # 禁用按钮
        cfx_grid.addWidget(self.export_cloth_btn, 0, 0)
        
        # 导出XGen Guides按钮
        self.export_guides_btn = QtWidgets.QPushButton("导出 XGen Guides")
        self.export_guides_btn.setToolTip("导出场景中的XGen Guides为Alembic缓存")
        self.export_guides_btn.setFixedSize(button_size)
        self.export_guides_btn.clicked.connect(self.show_guides_dialog)
        cfx_grid.addWidget(self.export_guides_btn, 0, 1)
        
        cfx_layout.addLayout(cfx_grid)
        main_layout.addWidget(cfx_group)
        
        # 状态标签
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setContentsMargins(0, 0, 0, 0)  # 移除状态标签的边距
        main_layout.addWidget(self.status_label)
        
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

    def show_guides_dialog(self):
        """显示XGen Guides导出窗口"""
        if not self.xgen_guides_dialog:
            self.xgen_guides_dialog = XGenGuidesDialog(self)
        
        # 将对话框放置在主窗口右侧
        pos = self.mapToGlobal(self.rect().topRight())
        self.xgen_guides_dialog.move(pos.x() + 5, pos.y())
        
        self.xgen_guides_dialog.show()
        self.xgen_guides_dialog.raise_()
        self.xgen_guides_dialog.activateWindow()

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
    
    # 创建新窗口, 使用Maya主窗口作为父窗口
    window = AlembicExporterGUI(parent=maya_main_window)
    
    # 确保窗口尺寸合适
    window.resize(380, window.height())  # 调整窗口宽度
    
    # 显示窗口并放置在合适位置
    window.show()
    
    # 将窗口移动到Maya窗口中心附近但偏右上方, 这样不会挡住场景视图
    if maya_main_window:
        center = maya_main_window.geometry().center()
        window.move(center.x() - window.width()//2 + 200, 
                   center.y() - maya_main_window.height()//2 + 150)
    
    # 确保窗口在前
    window.raise_()
    window.activateWindow()
    
    return window