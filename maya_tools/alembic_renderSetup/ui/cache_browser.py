"""
缓存浏览器组件

用于显示和管理布料缓存和XGen缓存文件
"""

import os
import maya.cmds as mc
import maya.OpenMaya as OpenMaya
import maya.mel as mel
from PySide2 import QtWidgets, QtCore, QtGui
from datetime import datetime
import threading
import time
import xgenm as xg
import xgenm.xgGlobal as xgg

from ..core.asset_manager import AssetManager
from ..core.utils import update_status
from maya_tools.alembic_renderSetup.core import cloth_cache_importer
from maya_tools.alembic_renderSetup.core import xgen_cache_importer

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
        self.cloth_list.itemDoubleClicked.connect(lambda: self._import_selected_caches("cloth"))
        cloth_layout.addWidget(self.cloth_list)
        
        # 布料缓存按钮
        cloth_btn_layout = QtWidgets.QHBoxLayout()
        
        self.import_cloth_btn = QtWidgets.QPushButton("导入所选缓存")
        self.import_cloth_btn.setToolTip("导入选中的布料缓存文件")
        self.import_cloth_btn.clicked.connect(lambda: self._import_selected_caches("cloth"))
        
        self.refresh_cloth_btn = QtWidgets.QPushButton("刷新")
        self.refresh_cloth_btn.setToolTip("刷新布料缓存列表")
        self.refresh_cloth_btn.clicked.connect(lambda: self._refresh_caches("cloth", False))
        
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
        self.xgen_list.itemDoubleClicked.connect(lambda: self._import_selected_caches("xgen"))
        xgen_layout.addWidget(self.xgen_list)
        
        # XGen缓存按钮
        xgen_btn_layout = QtWidgets.QHBoxLayout()
        
        self.import_xgen_btn = QtWidgets.QPushButton("导入所选缓存")
        self.import_xgen_btn.setToolTip("导入选中的XGen缓存文件")
        self.import_xgen_btn.clicked.connect(lambda: self._import_selected_caches("xgen"))
        
        self.refresh_xgen_btn = QtWidgets.QPushButton("刷新")
        self.refresh_xgen_btn.setToolTip("刷新XGen缓存列表")
        self.refresh_xgen_btn.clicked.connect(lambda: self._refresh_caches("xgen", False))
        
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
        
        参数:
            cache_type (str): 缓存类型，"cloth"或"xgen"
            force (bool): 是否强制刷新
        """
        if cache_type == "cloth":
            self._search_cloth_caches(force_refresh=force)
        else:
            self._search_xgen_caches(force_refresh=force)
        
    def _search_cloth_caches(self, force_refresh=False):
        """搜索布料缓存
        
        参数:
            force_refresh (bool): 是否强制刷新，不使用缓存
        """
        if not all([self.current_episode, self.current_sequence, self.current_shot, self.current_asset_id]):
            self._update_status("cloth", "请先选择资产")
            return
            
        # 尝试从缓存获取
        cache_key = (self.current_episode, self.current_sequence, self.current_shot, self.current_asset_id, "cloth")
        if not force_refresh and cache_key in self.cache:
            self._process_cache_results(self.cache[cache_key], "cloth")
            return
            
        # 停止现有搜索
        self._stop_search("cloth")
        
        # 更新UI状态
        self._update_status("cloth", "正在搜索缓存...")
        self._set_stop_button_enabled("cloth", True)
        
        # 清空列表
        self._clear_list("cloth")
        
        # 创建并启动搜索线程
        thread = CacheThread(
            self.asset_manager,
            self.current_episode,
            self.current_sequence,
            self.current_shot,
            self.current_asset_id,
            "cloth"
        )
        
        # 连接信号
        thread.update_signal.connect(self._on_thread_update)
        thread.error_signal.connect(self._on_thread_error)
        thread.finished_signal.connect(self._on_thread_finished)
        
        # 保存线程引用
        self.cloth_thread = thread
        
        # 启动线程
        thread.start()
    
    def _search_xgen_caches(self, force_refresh=False):
        """搜索XGen缓存
        
        参数:
            force_refresh (bool): 是否强制刷新，不使用缓存
        """
        if not all([self.current_episode, self.current_sequence, self.current_shot, self.current_asset_id]):
            self._update_status("xgen", "请先选择资产")
            return
            
        # 尝试从缓存获取
        cache_key = (self.current_episode, self.current_sequence, self.current_shot, self.current_asset_id, "xgen")
        if not force_refresh and cache_key in self.cache:
            self._process_cache_results(self.cache[cache_key], "xgen")
            return
            
        # 停止现有搜索
        self._stop_search("xgen")
        
        # 更新UI状态
        self._update_status("xgen", "正在搜索缓存...")
        self._set_stop_button_enabled("xgen", True)
        
        # 清空列表
        self._clear_list("xgen")
        
        # 创建并启动搜索线程
        thread = CacheThread(
            self.asset_manager,
            self.current_episode,
            self.current_sequence,
            self.current_shot,
            self.current_asset_id,
            "xgen"
        )
        
        # 连接信号
        thread.update_signal.connect(self._on_thread_update)
        thread.error_signal.connect(self._on_thread_error)
        thread.finished_signal.connect(self._on_thread_finished)
        
        # 保存线程引用
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
        """更新缓存数量标签
        
        参数:
            cache_type (str): 缓存类型，"cloth"或"xgen"
            count (int): 缓存数量
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
        """导入选中的缓存文件"""
        # 获取对应类型的列表控件
        list_widget = self.cloth_list if cache_type == "cloth" else self.xgen_list
        
        # 获取选中项
        selected_items = list_widget.selectedItems()
        if not selected_items:
            mc.warning(f"未选择{cache_type}缓存文件")
            return
        
        # 根据缓存类型调用相应的导入函数
        if cache_type == "cloth":
            self._import_cloth_cache()
        else:
            self._import_xgen_cache()
    
    def _import_cloth_cache(self):
        """导入选中的布料缓存文件"""
        selected_items = self.cloth_list.selectedItems()
        if not selected_items:
            mc.warning("未选择布料缓存文件")
            return
        
        # 获取选中项的文件路径
        selected_item = selected_items[0]
        cache_path = selected_item.data(QtCore.Qt.UserRole)
        
        if not cache_path or not os.path.exists(cache_path):
            mc.warning(f"缓存文件不存在: {cache_path}")
            return
        
        # 从当前界面获取资产ID，而不是从路径解析
        asset_id = self.current_asset_id
        
        # 如果界面上没有选中资产，再尝试从路径解析
        if not asset_id:
            asset_id = self._extract_asset_id_from_path(cache_path)
            
        # 如果仍然无法获取，要求用户输入
        if not asset_id:
            asset_id, ok = QtWidgets.QInputDialog.getText(
                self, "输入资产ID", "无法确定资产ID，请手动输入:")
            if not ok or not asset_id:
                mc.warning("未提供有效的资产ID，无法导入缓存")
                return
        
        # 调用导入函数
        try:
            result, matched, unmatched = cloth_cache_importer.import_cloth_cache(asset_id, cache_path)
            if result:
                self._show_import_result_dialog("布料缓存导入成功", 
                                            f"成功匹配材质: {len(matched)}/{len(matched) + len(unmatched)} 个几何体")
            else:
                self._show_import_result_dialog("布料缓存导入失败", 
                                            "请确保资产已正确导入场景", error=True)
        except Exception as e:
            mc.error(f"布料缓存导入失败: {str(e)}")
            self._show_import_result_dialog("布料缓存导入失败", str(e), error=True)
    
    def _import_xgen_cache(self):
        """导入选中的XGen缓存"""
        try:
            selected_items = self.xgen_list.selectedItems()
            if not selected_items:
                QtWidgets.QMessageBox.warning(self, "警告", "请先选择要导入的XGen缓存")
                return

            # 获取选中项的文件路径
            selected_item = selected_items[0]
            cache_path = selected_item.data(QtCore.Qt.UserRole)
            
            # 格式化路径，确保使用"/"作为路径分隔符
            cache_path = cache_path.replace("\\", "/")
            print(f"原始缓存路径: {cache_path}")
            
            # 验证路径格式
            if "//" in cache_path:
                cache_path = cache_path.replace("//", "/")
                print(f"修正重复分隔符后的路径: {cache_path}")
            
            # 验证文件是否存在
            if not os.path.exists(cache_path):
                # 尝试使用系统环境变量解析路径
                if "$(DESG)" in cache_path:
                    desg_var = mc.getenv("DESG")
                    if desg_var:
                        resolved_path = cache_path.replace("$(DESG)", desg_var)
                        print(f"尝试解析环境变量后的路径: {resolved_path}")
                        if os.path.exists(resolved_path):
                            cache_path = resolved_path
                            print(f"已成功解析环境变量路径: {cache_path}")
                
                # 再次检查文件是否存在
                if not os.path.exists(cache_path):
                    QtWidgets.QMessageBox.warning(self, "警告", f"缓存文件不存在: {cache_path}")
                    return
                
            print(f"最终使用的缓存路径: {cache_path}")

            # 使用当前界面上的资产ID
            asset_id = self.current_asset_id
            
            # 如果界面上没有选中资产，尝试从路径解析
            if not asset_id:
                asset_id = self._extract_asset_id_from_path(cache_path)
                
            # 如果仍然无法获取，要求用户输入
            if not asset_id:
                asset_id, ok = QtWidgets.QInputDialog.getText(
                    self, "输入资产ID", "无法确定资产ID，请手动输入:")
                if not ok or not asset_id:
                    QtWidgets.QMessageBox.warning(self, "警告", "未提供有效的资产ID，无法导入缓存")
                    return
            
            # 确保XGen插件已加载 - 专为Maya 2024优化
            xgen_loaded = mc.pluginInfo("xgenToolkit", query=True, loaded=True)
            if not xgen_loaded:
                try:
                    mc.loadPlugin("xgenToolkit")
                    print("已自动加载XGen插件")
                    # 重新检查插件状态
                    xgen_loaded = mc.pluginInfo("xgenToolkit", query=True, loaded=True)
                    if not xgen_loaded:
                        QtWidgets.QMessageBox.critical(self, "错误", "无法加载XGen插件，请检查Maya安装")
                        return
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "错误", f"加载XGen插件失败: {str(e)}")
                    return
            
            # 显示进度对话框
            progress_dialog = QtWidgets.QProgressDialog("正在导入XGen缓存...", "取消", 0, 100, self)
            progress_dialog.setWindowTitle("XGen缓存导入")
            progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
            progress_dialog.setValue(10)
            progress_dialog.show()
            QtWidgets.QApplication.processEvents()
            
            # 导入缓存操作
            try:
                # 使用优化过的XGen缓存导入器
                import maya_tools.alembic_renderSetup.core.xgen_cache_importer as xgen_importer
                
                # 更新进度
                progress_dialog.setLabelText("查找XGen Collections...")
                progress_dialog.setValue(30)
                QtWidgets.QApplication.processEvents()
                
                # 导入缓存
                progress_dialog.setLabelText("导入缓存中...")
                progress_dialog.setValue(50)
                QtWidgets.QApplication.processEvents()
                
                # 调用优化后的导入函数
                success, collection, description = xgen_importer.import_xgen_cache(asset_id, cache_path)
                
                # 完成导入
                progress_dialog.setValue(100)
                progress_dialog.close()
                
                # 显示结果
                if success:
                    self._show_import_result_dialog(
                        "XGen缓存导入成功", 
                        f"成功将缓存连接到:\nCollection: {collection}\nDescription: {description}"
                    )
                    
                    # 设置Guide Animation属性
                    # 再次确保路径格式正确
                    cache_path = cache_path.replace("\\", "/")
                    print(f"设置XGen缓存路径: {cache_path}")
                    
                    try:
                        xg.setAttr('cacheFileName', cache_path, collection, description, 'SplinePrimitive')
                        print(f"✓ 已设置缓存路径: {cache_path}")
                        
                        xg.setAttr('useCache', 'true', collection, description, 'SplinePrimitive')
                        print(f"✓ 已启用缓存")
                        
                        xg.setAttr('liveMode', 'false', collection, description, 'SplinePrimitive')
                        print(f"✓ 已关闭Live Mode")
                        
                        # 刷新XGen视图
                        try:
                            de = xgg.DescriptionEditor
                            de.refresh('Full')
                            print("✓ 已完全刷新XGen视图")
                        except Exception as e:
                            print(f"使用DescriptionEditor刷新失败: {str(e)}")
                            try:
                                xg.refreshDescription(collection, description)
                                print("✓ 已使用替代方法刷新XGen描述")
                            except Exception as e:
                                print(f"刷新描述失败: {str(e)}")
                    except Exception as e:
                        print(f"设置Guide Animation属性时出错: {str(e)}")
                else:
                    self._show_import_result_dialog(
                        "XGen缓存导入失败", 
                        "无法找到或创建匹配的XGen Description。\n请确保场景中已导入正确的XGen资产，\n且Legacy XGen系统正确设置。", 
                        error=True
                    )
                    
            except Exception as e:
                # 确保进度对话框关闭
                progress_dialog.close()
                
                # 显示详细错误
                self._show_import_result_dialog(
                    "XGen缓存导入出错", 
                    f"导入过程中发生错误:\n{str(e)}\n\n请查看脚本编辑器获取详细信息。", 
                    error=True
                )
                
                # 打印详细的堆栈跟踪
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"导入XGen缓存时发生错误：{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _show_import_result_dialog(self, title, message, error=False):
        """显示导入结果对话框"""
        dialog = QtWidgets.QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        if error:
            dialog.setIcon(QtWidgets.QMessageBox.Critical)
        else:
            dialog.setIcon(QtWidgets.QMessageBox.Information)
        dialog.exec_()
    
    def _show_context_menu(self, position, cache_type):
        """显示右键菜单"""
        menu = QtWidgets.QMenu()
        
        # 获取选中项
        list_widget = self.cloth_list if cache_type == "cloth" else self.xgen_list
        item = list_widget.itemAt(position)
        
        if item:
            # 获取数据
            cache_path = item.data(QtCore.Qt.UserRole)
            
            # 添加菜单项
            open_action = menu.addAction("打开文件位置")
            open_action.triggered.connect(lambda: self._open_file_location(cache_path))
            
            copy_action = menu.addAction("复制文件路径")
            copy_action.triggered.connect(lambda: self._copy_to_clipboard(cache_path))
            
            menu.addSeparator()
            
            # 添加导入菜单项
            import_action = menu.addAction("导入所选缓存")
            import_action.triggered.connect(lambda: self._import_selected_caches(cache_type))
            
            menu.addSeparator()
            
            # 添加刷新操作
            refresh_action = menu.addAction("刷新缓存列表")
            refresh_action.triggered.connect(lambda: self._refresh_caches(cache_type, False))
            
            force_refresh_action = menu.addAction("强制刷新缓存列表")
            force_refresh_action.triggered.connect(lambda: self._refresh_caches(cache_type, True))
            
            # 显示菜单
            menu.exec_(list_widget.mapToGlobal(position))
            
    def _open_file_location(self, cache_path):
        """打开文件位置"""
        if os.path.exists(cache_path):
            # 使用系统默认方式打开文件所在文件夹
            os.startfile(os.path.dirname(cache_path))
        else:
            mc.warning(f"文件不存在: {cache_path}")
            
    def _copy_to_clipboard(self, cache_path):
        """复制文件路径到剪贴板"""
        if os.path.exists(cache_path):
            # 使用Qt剪贴板功能复制文件路径
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(cache_path)
            OpenMaya.MGlobal.displayInfo(f"已复制路径到剪贴板: {cache_path}")
        else:
            mc.warning(f"文件不存在: {cache_path}")
            
    def closeEvent(self, event):
        """窗口关闭事件，确保线程停止"""
        self._stop_search("cloth")
        self._stop_search("xgen")
        super(CacheBrowserWidget, self).closeEvent(event)
        
    def _extract_asset_id_from_path(self, cache_path):
        """从缓存路径中提取资产ID"""
        try:
            # 如果当前已有资产ID（从UI选择），优先使用
            if hasattr(self, 'current_asset_id') and self.current_asset_id:
                return self.current_asset_id
                
            # 尝试从文件名解析资产ID
            filename = os.path.basename(cache_path)
            # 假设文件名格式为: assetID_cloth_v001.abc 或类似格式
            parts = filename.split('_')
            if len(parts) >= 2:
                return parts[0]  # 第一部分通常是资产ID
        except:
            pass
        
        return None 