import maya.cmds as mc
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import sys
import os
import gc

from ..core.asset_manager import AssetManager
from ..core.path_checker import PathChecker
from ..core.render_manager import RenderManager
from ..core.camera_manager import CameraManager
from ..core.utils import handle_error, update_status, set_frame_range, show_progress, update_progress, end_progress
from ..core.config import PATH_TEMPLATES, RENDER_SETTINGS


def maya_main_window():
    """获取Maya主窗口"""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


# 在类定义前添加一个全局变量
_shot_asset_manager_instance = None


class ShotAssetManagerUI(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        global _shot_asset_manager_instance

        # 如果已经有实例，先关闭它
        if _shot_asset_manager_instance is not None:
            try:
                _shot_asset_manager_instance.close()
                _shot_asset_manager_instance.deleteLater()
            except Exception as e:
                print(f"关闭旧窗口时出错: {str(e)}")

        # 调用父类构造函数
        super(ShotAssetManagerUI, self).__init__(parent)

        # 设置全局实例
        _shot_asset_manager_instance = self

        # 设置关闭时的行为，确保实例被正确清理
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # 连接销毁信号，确保实例被正确清理
        self.destroyed.connect(self._on_destroyed)

        # 其余初始化代码保持不变
        self.setWindowTitle("镜头资产管理器")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        # 初始化属性
        self.checker = PathChecker()
        self.episode_data = {}
        self.current_episode = None
        self.current_sequence = None
        self.current_shot = None
        self.asset_status = {}  # 存储资产检查状态
        self.asset_manager = AssetManager()

        # 创建UI并加载数据
        self.create_ui()
        self.load_episodes()

    def _on_destroyed(self):
        """窗口销毁时的处理"""
        global _shot_asset_manager_instance
        if _shot_asset_manager_instance == self:
            _shot_asset_manager_instance = None
            # 强制垃圾回收
            gc.collect()

    # 在create_ui方法中，在资产列表之前添加相机列表
    def create_ui(self):
        """创建UI界面"""
        main_layout = QtWidgets.QVBoxLayout(self)

        # 创建分割窗口
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧面板 - 镜头层级
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        # Episode 列表
        episode_group = QtWidgets.QGroupBox("剧集")
        episode_layout = QtWidgets.QVBoxLayout(episode_group)
        self.episode_list = QtWidgets.QListWidget()
        episode_layout.addWidget(self.episode_list)
        left_layout.addWidget(episode_group)

        # Sequence 列表
        sequence_group = QtWidgets.QGroupBox("场次")
        sequence_layout = QtWidgets.QVBoxLayout(sequence_group)
        self.sequence_list = QtWidgets.QListWidget()
        sequence_layout.addWidget(self.sequence_list)
        left_layout.addWidget(sequence_group)

        # Shot 列表
        shot_group = QtWidgets.QGroupBox("镜头")
        shot_layout = QtWidgets.QVBoxLayout(shot_group)
        self.shot_list = QtWidgets.QListWidget()
        shot_layout.addWidget(self.shot_list)
        left_layout.addWidget(shot_group)

        splitter.addWidget(left_widget)

        # 右侧面板 - 资产列表和操作按钮
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        # 添加相机列表
        camera_group = QtWidgets.QGroupBox("相机列表")
        camera_layout = QtWidgets.QHBoxLayout(camera_group)

        # 相机列表
        self.camera_list = QtWidgets.QListWidget()
        self.camera_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        camera_layout.addWidget(self.camera_list)

        # 导入相机按钮
        camera_btn_layout = QtWidgets.QVBoxLayout()
        self.import_camera_btn = QtWidgets.QPushButton("导入相机")
        camera_btn_layout.addWidget(self.import_camera_btn)
        camera_btn_layout.addStretch()

        camera_layout.addLayout(camera_btn_layout)
        right_layout.addWidget(camera_group)

        # 资产列表 (原有代码)
        asset_group = QtWidgets.QGroupBox("资产列表")
        asset_layout = QtWidgets.QVBoxLayout(asset_group)

        # 添加资产类型标签页
        self.asset_tabs = QtWidgets.QTabWidget()

        # 角色列表
        self.char_list = QtWidgets.QListWidget()
        self.char_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.asset_tabs.addTab(self.char_list, "角色")

        # 道具列表
        self.prop_list = QtWidgets.QListWidget()
        self.prop_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.asset_tabs.addTab(self.prop_list, "道具")

        asset_layout.addWidget(self.asset_tabs)
        right_layout.addWidget(asset_group)

        # 操作按钮
        button_layout = QtWidgets.QHBoxLayout()

        self.check_btn = QtWidgets.QPushButton("检查资产")
        self.import_btn = QtWidgets.QPushButton("导入选中资产")
        self.import_all_btn = QtWidgets.QPushButton("导入所有资产")
        self.save_btn = QtWidgets.QPushButton("保存场景")

        self.check_btn.setToolTip("检查当前镜头的资产状态")
        self.import_btn.setToolTip("导入选中的资产")
        self.import_all_btn.setToolTip("导入所有资产")
        self.import_camera_btn.setToolTip("导入选中的相机")
        self.save_btn.setToolTip("保存场景到对应的Lighting工作目录")

        button_layout.addWidget(self.check_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.import_all_btn)
        button_layout.addWidget(self.save_btn)

        right_layout.addLayout(button_layout)

        # 状态信息
        self.status_label = QtWidgets.QLabel("就绪")
        right_layout.addWidget(self.status_label)

        splitter.addWidget(right_widget)

        # 设置分割比例
        splitter.setSizes([300, 500])

        # 连接信号
        self.episode_list.itemClicked.connect(self.on_episode_selected)
        self.sequence_list.itemClicked.connect(self.on_sequence_selected)
        self.shot_list.itemClicked.connect(self.on_shot_selected)
        self.check_btn.clicked.connect(self.check_assets)
        self.import_btn.clicked.connect(self.import_selected_assets)
        self.import_all_btn.clicked.connect(self.import_all_assets)
        self.import_camera_btn.clicked.connect(self.import_camera)
        self.save_btn.clicked.connect(self.save_scene)

    def load_episodes(self):
        """加载剧集数据"""
        self.episode_list.clear()
        self.sequence_list.clear()
        self.shot_list.clear()
        self.char_list.clear()
        self.prop_list.clear()
        self.camera_list.clear()  # 添加清空相机列表

        # 从AssetManager获取数据
        episodes = self.asset_manager.get_episodes()

        # 添加到列表
        for episode_name in episodes:
            self.episode_list.addItem(episode_name)

    def on_episode_selected(self, item):
        """选择剧集时的处理"""
        episode = item.text()
        self.sequence_list.clear()
        self.shot_list.clear()
        self.char_list.clear()
        self.prop_list.clear()
        self.camera_list.clear()  # 清空相机列表

        # 加载场次数据
        sequences = self.asset_manager.get_sequences(episode)
        for seq_name in sequences:
            self.sequence_list.addItem(seq_name)

    def on_sequence_selected(self, item):
        """选择场次时的处理"""
        sequence = item.text()
        episode = self.asset_manager.current_episode
        self.shot_list.clear()
        self.char_list.clear()
        self.prop_list.clear()
        self.camera_list.clear()  # 清空相机列表

        # 加载镜头数据
        shots = self.asset_manager.get_shots(episode, sequence)
        for shot_id in shots:
            # 转换为首字母大写格式
            display_shot = "Sc" + shot_id[2:]
            item = QtWidgets.QListWidgetItem(display_shot)
            item.setData(QtCore.Qt.UserRole, shot_id)  # 存储原始shot_id
            self.shot_list.addItem(item)

    def on_shot_selected(self, item):
        """选择镜头时的处理"""
        shot_display = item.text()
        shot_id = item.data(QtCore.Qt.UserRole)
        episode = self.asset_manager.current_episode
        sequence = self.asset_manager.current_sequence

        self.char_list.clear()
        self.prop_list.clear()
        self.camera_list.clear()  # 清空相机列表

        # 更新当前选中的镜头        
        self.current_episode = episode
        self.current_sequence = sequence
        self.current_shot = shot_id

        # 加载资产数据
        assets = self.asset_manager.get_shot_assets(episode, sequence, shot_id)

        # 加载角色
        for char in assets["Chars"]:
            item = QtWidgets.QListWidgetItem(char)
            self.char_list.addItem(item)

        # 加载道具
        for prop in assets["Props"]:
            item = QtWidgets.QListWidgetItem(prop)
            self.prop_list.addItem(item)
        self.load_camera_list()

    def load_camera_list(self):
        """加载当前镜头的相机列表"""
        if not all([self.current_episode, self.current_sequence, self.current_shot]):
            return

        # 构建work目录路径
        shot_path = os.path.join(self.checker.anm_path, self.current_episode,
                                 self.current_sequence, self.current_shot, "work")

        if not os.path.exists(shot_path):
            self.status_label.setText(f"路径不存在: {shot_path}")
            return

        # 查找以cam_开头的FBX文件
        camera_files = []
        for file in os.listdir(shot_path):
            if file.lower().startswith("cam_") and file.lower().endswith(".fbx"):
                camera_files.append(file)

        # 添加到列表
        for camera_file in sorted(camera_files):
            item = QtWidgets.QListWidgetItem(camera_file)
            item.setData(QtCore.Qt.UserRole, os.path.join(shot_path, camera_file))
            self.camera_list.addItem(item)

        if not camera_files:
            self.status_label.setText("未找到相机文件")
        else:
            self.status_label.setText(f"找到 {len(camera_files)} 个相机文件")

    def import_camera(self):
        """导入选中的相机"""

        selected_items = self.camera_list.selectedItems()

        if not selected_items:
            handle_error("请先选择要导入的相机", self.status_label)
            return

        camera_file = selected_items[0].data(QtCore.Qt.UserRole)
        camera_name = os.path.basename(camera_file)

        if not os.path.exists(camera_file):
            handle_error(f"相机文件不存在: {camera_file}", self.status_label)
            return

        if CameraManager.check_camera_exists():
            if mc.confirmDialog(
                    title='相机已存在',
                    message='场景中已存在相机，是否继续导入？',
                    button=['是', '否'],
                    defaultButton='否',
                    cancelButton='否',
                    dismissString='否') == '否':
                return

        try:
            update_status(self.status_label, f"正在导入相机: {camera_name}")

            # 导入相机FBX
            mc.file(camera_file, i=True, type="FBX", ignoreVersion=True,
                    ra=True, mergeNamespacesOnClash=False, namespace="camera")

            # 设置帧率
            mc.currentUnit(time=RENDER_SETTINGS["frame_rate"])

            # 解析帧范围
            start_frame, end_frame = CameraManager.parse_frame_range(camera_name)
            error = None
            if error:
                handle_error(error, self.status_label)
                return

            # 设置帧范围
            set_frame_range(start_frame, end_frame)

            # 设置渲染相机
            camera, error = CameraManager.find_render_camera()
            if error:
                handle_error(error, self.status_label)
                return

            # 设置渲染参数
            success, error = RenderManager.setup_render_globals(start_frame, end_frame)
            if not success:
                handle_error(error, self.status_label)
                return

            success, error = RenderManager.setup_arnold_renderer()
            if not success:
                handle_error(error, self.status_label)
                return

            update_status(self.status_label, f"成功导入相机并设置渲染: {camera}")

        except Exception as e:
            # 使用异常信息更新状态标签
            handle_error(e, self.status_label)

    def check_assets(self):
        """检查当前镜头的资产状态"""
        try:
            self.status_label.setText("正在检查资产...")

            # 使用AssetManager检查所有资产
            self.asset_status = self.asset_manager.check_all_assets()

            # 更新UI显示
            self._update_asset_status_ui(self.asset_status)

            self.status_label.setText("资产检查完成")
        except Exception as e:
            handle_error(f"检查资产时出错: {str(e)}", self.status_label)

    def _update_asset_status_ui(self, asset_status):
        """更新资产状态UI显示"""
        # 更新角色列表
        for i in range(self.char_list.count()):
            item = self.char_list.item(i)
            char_id = item.text()
            status = asset_status.get(char_id, {})

            # 设置背景色
            if status.get("lookdev_exists", False):
                item.setBackground(QtGui.QColor(120, 230, 120))  # 更鲜艳的绿色
                item.setForeground(QtGui.QColor(0, 0, 0))  # 黑色文字
            else:
                item.setBackground(QtGui.QColor(230, 120, 120))  # 更鲜艳的红色
                item.setForeground(QtGui.QColor(255, 255, 255))  # 白色文字

            # 设置提示信息
            tooltip = f"角色: {char_id}\n"
            tooltip += f"LookDev文件: {'存在' if status.get('lookdev_exists', False) else '不存在'}\n"
            tooltip += f"ABC文件: {'存在' if status.get('abc_exists', False) else '不存在'}"
            item.setToolTip(tooltip)

        # 更新道具列表
        for i in range(self.prop_list.count()):
            item = self.prop_list.item(i)
            prop_id = item.text()
            status = asset_status.get(prop_id, {})

            # 设置背景色
            if status.get("lookdev_exists", False):
                item.setBackground(QtGui.QColor(120, 230, 120))  # 更鲜艳的绿色
                item.setForeground(QtGui.QColor(0, 0, 0))
            else:
                item.setBackground(QtGui.QColor(230, 120, 120))  # 更鲜艳的红色
                item.setForeground(QtGui.QColor(255, 255, 255))  # 白色文字

            # 设置提示信息
            tooltip = f"道具: {prop_id}\n"
            tooltip += f"LookDev文件: {'存在' if status.get('lookdev_exists', False) else '不存在'}\n"
            tooltip += f"ABC文件: {'存在' if status.get('abc_exists', False) else '不存在'}"
            item.setToolTip(tooltip)

    def import_selected_assets(self):
        """导入选中的资产"""
        # 获取选中的角色和道具
        selected_chars = self.char_list.selectedItems()
        selected_props = self.prop_list.selectedItems()

        if not selected_chars and not selected_props:
            mc.warning("请先选择要导入的资产")
            return

        imported_count = 0
        failed_count = 0
        updated_abc_count = 0

        # 导入选中的角色
        for item in selected_chars:
            char_id = item.text()
            try:
                # 导入资产
                self.asset_manager.import_asset(char_id)
                imported_count += 1
                self.status_label.setText(f"成功导入角色 {char_id} 的LookDev文件")

                # 等待资产加载完成
                mc.refresh()

                # 更新ABC引用路径
                if self.asset_manager.update_abc_reference(char_id):
                    updated_abc_count += 1
            except Exception as e:
                error_msg = f"导入角色 {char_id} 时出错: {str(e)}"
                mc.warning(error_msg)
                self.status_label.setText(error_msg)
                failed_count += 1

        # 导入选中的道具
        for item in selected_props:
            prop_id = item.text()
            try:
                # 导入资产
                self.asset_manager.import_asset(prop_id)
                imported_count += 1
                self.status_label.setText(f"成功导入道具 {prop_id} 的LookDev文件")

                # 等待资产加载完成
                mc.refresh()

                # 更新ABC引用路径
                if self.asset_manager.update_abc_reference(prop_id):
                    updated_abc_count += 1
            except Exception as e:
                error_msg = f"导入道具 {prop_id} 时出错: {str(e)}"
                mc.warning(error_msg)
                self.status_label.setText(error_msg)
                failed_count += 1

        self.status_label.setText(
            f"导入完成: 成功 {imported_count} 个, 失败 {failed_count} 个, 更新ABC {updated_abc_count} 个")

    def import_all_assets(self):
        """导入当前镜头的所有资产"""
        if not self.asset_status:
            self.check_assets()  # 先检查资产

        assets = list(self.asset_status.keys())
        if not assets:
            self.status_label.setText("没有可导入的资产")
            return

        progress_bar = show_progress("导入资产", "准备导入...", len(assets))

        try:
            # 选择所有角色和道具
            self.char_list.selectAll()
            self.prop_list.selectAll()

            # 显示进度
            update_progress(progress_bar, 0, "正在导入所有资产...")

            # 调用导入选中资产的方法
            self.import_selected_assets()

            self.status_label.setText(f"成功导入所有资产")
        finally:
            end_progress(progress_bar)

    def save_scene(self):
        """保存当前场景到对应的 light 文件夹的 work 目录"""
        if not all([self.current_episode, self.current_sequence, self.current_shot]):
            mc.warning("请先选择一个镜头")
            return

        light_work_path = PATH_TEMPLATES["lighting_work"].format(
            episode=self.current_episode,
            sequence=self.current_sequence,
            shot=self.current_shot
        )

        # 确保目录存在
        if not os.path.exists(light_work_path):
            try:
                os.makedirs(light_work_path)
            except Exception as e:
                mc.warning(f"创建目录失败: {light_work_path}\n错误: {str(e)}")
                return

        # 构建文件名基础部分
        file_base = f"{self.current_sequence}_{self.current_shot}_Lgt"

        # 查找现有文件，确定版本号
        version = 1
        existing_files = [f for f in os.listdir(light_work_path) if f.startswith(file_base) and f.endswith(".ma")]

        if existing_files:
            # 从现有文件中提取最大版本号
            versions = []
            for file in existing_files:
                try:
                    # 提取版本号部分 (v001, v002 等)
                    v_part = file.split("_")[-1].split(".")[0]
                    if v_part.startswith("v") and len(v_part) == 4 and v_part[1:].isdigit():
                        versions.append(int(v_part[1:]))
                except:
                    pass

            if versions:
                version = max(versions) + 1

        # 构建完整文件名
        file_name = PATH_TEMPLATES["lighting_file_pattern"].format(
            sequence=self.current_sequence,
            shot=self.current_shot,
            version=version
        )
        full_path = os.path.join(light_work_path, file_name)

        if os.path.exists(full_path):
            if mc.confirmDialog(
                    title='文件已存在',
                    message=f'文件 {file_name} 已存在，是否覆盖？',
                    button=['是', '否'],
                    defaultButton='否',
                    cancelButton='否',
                    dismissString='否') == '否':
                return

        # 保存文件
        try:
            mc.file(rename=full_path)
            mc.file(save=True, type="mayaAscii")
            self.status_label.setText(f"场景已保存到: {full_path}")
        except Exception as e:
            error_msg = f"保存文件时出错: {str(e)}"
            mc.warning(error_msg)
            self.status_label.setText(error_msg)
