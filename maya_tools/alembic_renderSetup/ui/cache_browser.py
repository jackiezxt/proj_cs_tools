"""
缓存浏览器组件

用于显示和管理布料缓存和XGen缓存文件
"""

import os
import maya.cmds as mc
from PySide2 import QtWidgets, QtCore, QtGui
from datetime import datetime
import threading
import time

from ..core.asset_manager import AssetManager
from ..core.utils import update_status

# 列常量定义
class ClothColumns:
    FILENAME = 0

class XGenColumns:
    FILENAME = 0


class CacheThread(QtCore.QThread):
    """缓存搜索线程，避免UI卡顿"""
    # 自定义信号
    update_signal = QtCore.Signal(list, str)  # 传递找到的缓存列表和类型
    error_signal = QtCore.Signal(str)   # 传递错误信息
    finished_signal = QtCore.Signal(str, int)  # 传递完成状态和找到的缓存数量

    def __init__(self, asset_manager, episode, sequence, shot, asset_id, cache_type):
        """初始化搜索线程
        
        Args:
            asset_manager: 资产管理器实例
            episode: 剧集
            sequence: 场次
            shot: 镜头号
            asset_id: 资产ID
            cache_type: 缓存类型，"cloth"或"xgen"
        """
        super(CacheThread, self).__init__()
        self.asset_manager = asset_manager
        self.episode = episode
        self.sequence = sequence
        self.shot = shot
        self.asset_id = asset_id
        self.cache_type = cache_type
        self.is_running = True

    def run(self):
        """运行线程"""
        try:
            if not all([self.episode, self.sequence, self.shot, self.asset_id]):
                self.error_signal.emit("缺少必要信息，无法查找缓存")
                return

            # 根据类型调用不同的查找方法
            if self.cache_type == "cloth":
                try:
                    caches = self.asset_manager.find_cloth_caches(
                        self.episode, self.sequence, self.shot, self.asset_id
                    )
                    self.update_signal.emit(caches, "cloth")
                    self.finished_signal.emit("cloth", len(caches))
                except Exception as e:
                    self.error_signal.emit(f"查找布料缓存时出错: {str(e)}")
            elif self.cache_type == "xgen":
                try:
                    caches = self.asset_manager.find_xgen_caches(
                        self.episode, self.sequence, self.shot, self.asset_id
                    )
                    self.update_signal.emit(caches, "xgen")
                    self.finished_signal.emit("xgen", len(caches))
                except Exception as e:
                    self.error_signal.emit(f"查找XGen缓存时出错: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"查找缓存时发生错误: {str(e)}")
        finally:
            self.is_running = False

    def stop(self):
        """停止线程"""
        self.is_running = False
        self.wait()


class CacheBrowserWidget(QtWidgets.QWidget):
    """缓存浏览器组件，显示布料缓存和XGen缓存列表"""
    
    def __init__(self, parent=None):
        """初始化缓存浏览器组件"""
        super(CacheBrowserWidget, self).__init__(parent)
        
        # 创建资产管理器实例
        self.asset_manager = AssetManager()
        
        # 当前选中的资产信息
        self.current_episode = ""
        self.current_sequence = ""
        self.current_shot = ""
        self.current_asset_id = ""
        
        # 搜索线程
        self.cloth_thread = None
        self.xgen_thread = None
        
        # 缓存机制
        self.cache = {}  # 格式: {(episode, sequence, shot, asset_id, type): caches}
        
        # 设置UI
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI布局和组件"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 布料缓存部分
        cloth_group = QtWidgets.QGroupBox("布料缓存")
        cloth_layout = QtWidgets.QVBoxLayout(cloth_group)
        
        # 布料缓存状态和统计
        cloth_status_layout = QtWidgets.QHBoxLayout()
        self.cloth_status_label = QtWidgets.QLabel("就绪")
        self.cloth_count_label = QtWidgets.QLabel("0 个缓存")
        cloth_status_layout.addWidget(self.cloth_status_label, 1)
        cloth_status_layout.addWidget(self.cloth_count_label, 0)
        cloth_layout.addLayout(cloth_status_layout)
        
        # 布料缓存列表 - 简化为只有文件名
        self.cloth_list = QtWidgets.QListWidget()  # 改用QListWidget
        self.cloth_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.cloth_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.cloth_list.customContextMenuRequested.connect(lambda pos: self._show_context_menu(pos, "cloth"))
        
        cloth_layout.addWidget(self.cloth_list)
        
        # 布料缓存按钮
        cloth_btn_layout = QtWidgets.QHBoxLayout()
        
        self.import_cloth_btn = QtWidgets.QPushButton("导入所选缓存")
        self.import_cloth_btn.setToolTip("导入选中的布料缓存文件")
        self.import_cloth_btn.clicked.connect(lambda: self._import_selected_caches("cloth"))
        
        self.refresh_cloth_btn = QtWidgets.QPushButton("刷新")
        self.refresh_cloth_btn.setToolTip("刷新布料缓存列表")
        self.refresh_cloth_btn.clicked.connect(lambda: self._refresh_caches("cloth", True))
        
        self.stop_cloth_btn = QtWidgets.QPushButton("停止")
        self.stop_cloth_btn.setToolTip("停止查找缓存")
        self.stop_cloth_btn.clicked.connect(lambda: self._stop_search("cloth"))
        self.stop_cloth_btn.setEnabled(False)
        
        cloth_btn_layout.addWidget(self.import_cloth_btn)
        cloth_btn_layout.addWidget(self.refresh_cloth_btn)
        cloth_btn_layout.addWidget(self.stop_cloth_btn)
        cloth_layout.addLayout(cloth_btn_layout)
        
        # XGen缓存部分
        xgen_group = QtWidgets.QGroupBox("XGen缓存")
        xgen_layout = QtWidgets.QVBoxLayout(xgen_group)
        
        # XGen缓存状态和统计
        xgen_status_layout = QtWidgets.QHBoxLayout()
        self.xgen_status_label = QtWidgets.QLabel("就绪")
        self.xgen_count_label = QtWidgets.QLabel("0 个缓存")
        xgen_status_layout.addWidget(self.xgen_status_label, 1)
        xgen_status_layout.addWidget(self.xgen_count_label, 0)
        xgen_layout.addLayout(xgen_status_layout)
        
        # XGen缓存列表 - 简化为只有文件名
        self.xgen_list = QtWidgets.QListWidget()  # 改用QListWidget
        self.xgen_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.xgen_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.xgen_list.customContextMenuRequested.connect(lambda pos: self._show_context_menu(pos, "xgen"))
        
        xgen_layout.addWidget(self.xgen_list)
        
        # XGen缓存按钮
        xgen_btn_layout = QtWidgets.QHBoxLayout()
        
        self.import_xgen_btn = QtWidgets.QPushButton("导入所选缓存")
        self.import_xgen_btn.setToolTip("导入选中的XGen缓存文件")
        self.import_xgen_btn.clicked.connect(lambda: self._import_selected_caches("xgen"))
        
        self.refresh_xgen_btn = QtWidgets.QPushButton("刷新")
        self.refresh_xgen_btn.setToolTip("刷新XGen缓存列表")
        self.refresh_xgen_btn.clicked.connect(lambda: self._refresh_caches("xgen", True))
        
        self.stop_xgen_btn = QtWidgets.QPushButton("停止")
        self.stop_xgen_btn.setToolTip("停止查找缓存")
        self.stop_xgen_btn.clicked.connect(lambda: self._stop_search("xgen"))
        self.stop_xgen_btn.setEnabled(False)
        
        xgen_btn_layout.addWidget(self.import_xgen_btn)
        xgen_btn_layout.addWidget(self.refresh_xgen_btn)
        xgen_btn_layout.addWidget(self.stop_xgen_btn)
        xgen_layout.addLayout(xgen_btn_layout)
        
        # 将所有组件添加到主布局
        main_layout.addWidget(cloth_group, 1)
        main_layout.addWidget(xgen_group, 1)
        
        # 初始化线程信号连接
        self._setup_thread_signals()
        
    def _setup_thread_signals(self):
        """设置线程信号连接"""
        # 在这里只设置连接方式，实际的线程创建在需要时进行
        pass
        
    def update_cache_lists(self, episode, sequence, shot, asset_id):
        """更新缓存列表，显示指定资产的缓存文件
        
        Args:
            episode: 剧集
            sequence: 场次
            shot: 镜头
            asset_id: 资产ID，如"c001"
        """
        # 保存当前选择的信息
        self.current_episode = episode
        self.current_sequence = sequence
        self.current_shot = shot
        self.current_asset_id = asset_id
        
        # 更新布料和XGen缓存列表
        self._refresh_caches("cloth", False)
        self._refresh_caches("xgen", False)
        
    def _refresh_caches(self, cache_type, force=False):
        """刷新缓存列表
        
        Args:
            cache_type: 缓存类型，"cloth"或"xgen"
            force: 是否强制刷新，不使用缓存
        """
        if not all([self.current_episode, self.current_sequence, self.current_shot, self.current_asset_id]):
            self._update_status(cache_type, "请先选择资产")
            return
            
        # 尝试从缓存获取
        cache_key = (self.current_episode, self.current_sequence, self.current_shot, self.current_asset_id, cache_type)
        if not force and cache_key in self.cache:
            self._process_cache_results(self.cache[cache_key], cache_type)
            return
            
        # 停止现有搜索
        self._stop_search(cache_type)
        
        # 更新UI状态
        self._update_status(cache_type, "正在搜索缓存...")
        self._set_stop_button_enabled(cache_type, True)
        
        # 清空列表
        self._clear_list(cache_type)
        
        # 创建并启动搜索线程
        thread = CacheThread(
            self.asset_manager,
            self.current_episode,
            self.current_sequence,
            self.current_shot,
            self.current_asset_id,
            cache_type
        )
        
        # 连接信号
        thread.update_signal.connect(self._on_thread_update)
        thread.error_signal.connect(self._on_thread_error)
        thread.finished_signal.connect(self._on_thread_finished)
        
        # 保存线程引用
        if cache_type == "cloth":
            self.cloth_thread = thread
        else:
            self.xgen_thread = thread
            
        # 启动线程
        thread.start()
        
    def _on_thread_update(self, caches, cache_type):
        """处理线程更新信号
        
        Args:
            caches: 找到的缓存列表
            cache_type: 缓存类型，"cloth"或"xgen"
        """
        # 更新缓存
        cache_key = (self.current_episode, self.current_sequence, self.current_shot, self.current_asset_id, cache_type)
        self.cache[cache_key] = caches
        
        # 处理结果
        self._process_cache_results(caches, cache_type)
        
    def _on_thread_error(self, error_msg):
        """处理线程错误信号
        
        Args:
            error_msg: 错误信息
        """
        mc.warning(error_msg)
        
    def _on_thread_finished(self, cache_type, count):
        """处理线程完成信号
        
        Args:
            cache_type: 缓存类型，"cloth"或"xgen"
            count: 找到的缓存数量
        """
        # 更新UI状态
        self._update_status(cache_type, f"搜索完成，找到 {count} 个缓存")
        self._set_stop_button_enabled(cache_type, False)
        
        # 更新计数标签
        self._update_count_label(cache_type, count)
        
    def _process_cache_results(self, caches, cache_type):
        """处理缓存搜索结果
        
        Args:
            caches: 缓存列表
            cache_type: 缓存类型，"cloth"或"xgen"
        """
        if cache_type == "cloth":
            self._update_cloth_list(caches)
        else:
            self._update_xgen_list(caches)
            
    def _update_status(self, cache_type, status):
        """更新状态标签
        
        Args:
            cache_type: 缓存类型，"cloth"或"xgen"
            status: 状态文本
        """
        if cache_type == "cloth":
            self.cloth_status_label.setText(status)
        else:
            self.xgen_status_label.setText(status)
            
    def _update_count_label(self, cache_type, count):
        """更新计数标签
        
        Args:
            cache_type: 缓存类型，"cloth"或"xgen"
            count: 缓存数量
        """
        if cache_type == "cloth":
            self.cloth_count_label.setText(f"{count} 个缓存")
        else:
            self.xgen_count_label.setText(f"{count} 个缓存")
            
    def _set_stop_button_enabled(self, cache_type, enabled):
        """设置停止按钮状态
        
        Args:
            cache_type: 缓存类型，"cloth"或"xgen"
            enabled: 是否启用
        """
        if cache_type == "cloth":
            self.stop_cloth_btn.setEnabled(enabled)
        else:
            self.stop_xgen_btn.setEnabled(enabled)
            
    def _clear_list(self, cache_type):
        """清空列表
        
        Args:
            cache_type: 缓存类型，"cloth"或"xgen"
        """
        if cache_type == "cloth":
            self.cloth_list.clear()
        else:
            self.xgen_list.clear()
            
    def _stop_search(self, cache_type):
        """停止搜索
        
        Args:
            cache_type: 缓存类型，"cloth"或"xgen"
        """
        if cache_type == "cloth" and self.cloth_thread is not None:
            self.cloth_thread.stop()
            self.cloth_thread = None
            self._set_stop_button_enabled("cloth", False)
        elif cache_type == "xgen" and self.xgen_thread is not None:
            self.xgen_thread.stop()
            self.xgen_thread = None
            self._set_stop_button_enabled("xgen", False)
            
    def _update_cloth_list(self, cloth_caches):
        """更新布料缓存列表
        
        Args:
            cloth_caches: 布料缓存列表
        """
        self._clear_list("cloth")
        
        # 填充列表 - 简化版本，只显示文件名
        for cache in cloth_caches:
            filename = cache.get("filename", "")
            item = QtWidgets.QListWidgetItem(filename)
            
            # 设置工具提示显示完整路径
            item.setToolTip(cache.get("path", ""))
            
            # 保存完整路径供后续使用
            item.setData(QtCore.Qt.UserRole, cache.get("path", ""))
            
            # 保存其他信息以便需要时使用
            version = cache.get("version", 0)
            item.setData(QtCore.Qt.UserRole + 1, version)
            
            # 添加到列表
            self.cloth_list.addItem(item)
            
        # 更新计数
        self._update_count_label("cloth", len(cloth_caches))
            
    def _update_xgen_list(self, xgen_caches):
        """更新XGen缓存列表
        
        Args:
            xgen_caches: XGen缓存列表
        """
        self._clear_list("xgen")
        
        # 填充列表 - 简化版本，只显示文件名
        for cache in xgen_caches:
            filename = cache.get("filename", "")
            item = QtWidgets.QListWidgetItem(filename)
            
            # 设置工具提示显示完整路径和描述
            tooltip = f"{cache.get('path', '')}\n描述: {cache.get('description', '')}"
            item.setToolTip(tooltip)
            
            # 保存完整路径供后续使用
            item.setData(QtCore.Qt.UserRole, cache.get("path", ""))
            
            # 保存描述信息
            item.setData(QtCore.Qt.UserRole + 1, cache.get("description", ""))
            
            # 添加到列表
            self.xgen_list.addItem(item)
            
        # 更新计数
        self._update_count_label("xgen", len(xgen_caches))
            
    def _import_selected_caches(self, cache_type):
        """导入选中的缓存
        
        Args:
            cache_type: 缓存类型，"cloth"或"xgen"
        """
        # 获取列表和选中项
        list_widget = self.cloth_list if cache_type == "cloth" else self.xgen_list
        selected_items = list_widget.selectedItems()
        
        if not selected_items:
            mc.warning(f"请先选择要导入的{cache_type}缓存")
            return
            
        # 导入每个选中的缓存
        for item in selected_items:
            cache_path = item.data(QtCore.Qt.UserRole)
            if cache_path and os.path.exists(cache_path):
                if cache_type == "cloth":
                    self._import_cloth_cache(cache_path)
                else:
                    # 获取描述名称
                    description = item.data(QtCore.Qt.UserRole + 1)
                    self._import_xgen_cache(cache_path, description)
            else:
                mc.warning(f"缓存文件不存在: {cache_path}")
                
    def _import_cloth_cache(self, cache_path):
        """导入布料缓存"""
        # 实现布料缓存导入逻辑
        # 这部分可能需要根据项目具体需求实现
        mc.warning(f"导入布料缓存: {cache_path}")
        # 示例: 使用Alembic导入节点
        cache_node = mc.createNode('AlembicNode')
        mc.setAttr(f"{cache_node}.abc_File", cache_path, type="string")
        mc.warning(f"创建Alembic节点: {cache_node}")
        
    def _import_xgen_cache(self, cache_path, description):
        """导入XGen缓存"""
        # 实现XGen缓存导入逻辑
        # 这部分可能需要根据项目具体需求实现
        mc.warning(f"导入XGen缓存: {cache_path}, 描述: {description}")
        # 示例: 使用Alembic导入节点
        cache_node = mc.createNode('AlembicNode')
        mc.setAttr(f"{cache_node}.abc_File", cache_path, type="string")
        mc.warning(f"创建Alembic节点: {cache_node}")
        
    def _show_context_menu(self, position, cache_type):
        """显示右键菜单
        
        Args:
            position: 鼠标位置
            cache_type: 缓存类型，"cloth"或"xgen"
        """
        # 获取列表控件
        list_widget = self.cloth_list if cache_type == "cloth" else self.xgen_list
        
        # 创建右键菜单
        menu = QtWidgets.QMenu()
        
        # 添加菜单项
        import_action = menu.addAction("导入选中缓存")
        preview_action = menu.addAction("预览缓存信息")
        menu.addSeparator()
        open_folder_action = menu.addAction("打开所在文件夹")
        menu.addSeparator()
        refresh_action = menu.addAction("刷新缓存列表")
        force_refresh_action = menu.addAction("强制刷新缓存列表")
        
        # 获取选中的项
        selected_items = list_widget.selectedItems()
        if not selected_items:
            import_action.setEnabled(False)
            preview_action.setEnabled(False)
            open_folder_action.setEnabled(False)
            
        # 显示菜单并获取选择的操作
        action = menu.exec_(list_widget.mapToGlobal(position))
        
        # 处理选择的操作
        if action == import_action:
            self._import_selected_caches(cache_type)
        elif action == preview_action:
            self._preview_cache_info(selected_items, cache_type)
        elif action == open_folder_action:
            # 打开第一个选中项所在的文件夹
            if selected_items:
                cache_path = selected_items[0].data(QtCore.Qt.UserRole)
                self._open_folder(os.path.dirname(cache_path))
        elif action == refresh_action:
            self._refresh_caches(cache_type, False)
        elif action == force_refresh_action:
            self._refresh_caches(cache_type, True)
            
    def _preview_cache_info(self, selected_items, cache_type):
        """预览缓存信息
        
        Args:
            selected_items: 选中的列表项
            cache_type: 缓存类型，"cloth"或"xgen"
        """
        if not selected_items:
            return
            
        # 获取第一个选中项
        item = selected_items[0]
        cache_path = item.data(0, QtCore.Qt.UserRole)
        
        if not os.path.exists(cache_path):
            mc.warning(f"缓存文件不存在: {cache_path}")
            return
            
        # 显示基本信息
        info = f"文件: {os.path.basename(cache_path)}\n"
        info += f"路径: {cache_path}\n"
        
        # 这里可以添加更多信息，如帧范围、顶点数量等
        # 需要调用Alembic API或Maya命令获取
            
        # 显示信息对话框
        QtWidgets.QMessageBox.information(self, "缓存信息", info)
            
    def _open_folder(self, folder_path):
        """打开文件夹"""
        if os.path.exists(folder_path):
            # 使用系统默认方式打开文件夹
            os.startfile(folder_path)
        else:
            mc.warning(f"文件夹不存在: {folder_path}")
            
    def closeEvent(self, event):
        """窗口关闭事件，确保线程停止"""
        self._stop_search("cloth")
        self._stop_search("xgen")
        super(CacheBrowserWidget, self).closeEvent(event) 