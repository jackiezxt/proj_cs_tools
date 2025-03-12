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
import re
import sys
import logging

from ..core.asset_manager import AssetManager
from ..core.utils import update_status
from maya_tools.alembic_renderSetup.core import cloth_cache_importer
from maya_tools.alembic_renderSetup.core import xgen_cache_importer
from maya_tools.alembic_renderSetup.core import utils
from maya_tools.alembic_renderSetup.core.cloth_cache_importer import import_cloth_cache
from maya_tools.alembic_renderSetup.core.xgen_cache_importer import import_xgen_cache

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


class XGenBlendShapeDialog(QtWidgets.QDialog):
    """XGen生长面与布料几何体BlendShape对话框"""
    
    def __init__(self, parent=None, asset_id=None):
        super(XGenBlendShapeDialog, self).__init__(parent)
        self.setWindowTitle("XGen生长面与布料几何体BlendShape")
        self.setMinimumSize(600, 400)
        self.cloth_des_items = []  # 存储布料几何体项目
        self.xgen_des_items = []   # 存储XGen生长面项目
        self.asset_id = asset_id   # 存储角色ID
        self._setup_ui()
        self._populate_lists()
        
    def _setup_ui(self):
        """设置对话框UI"""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # 显示当前选中的角色ID
        if self.asset_id:
            asset_label = QtWidgets.QLabel(f"当前角色: {self.asset_id}")
            asset_label.setStyleSheet("font-weight: bold; color: #3366CC;")
            main_layout.addWidget(asset_label)
        
        # 创建列表布局
        lists_layout = QtWidgets.QHBoxLayout()
        
        # 左侧列表 - XGen生长面（调整位置）
        xgen_layout = QtWidgets.QVBoxLayout()
        xgen_label = QtWidgets.QLabel("XGen生长面 (_DES)")
        self.xgen_list = QtWidgets.QListWidget()
        self.xgen_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)  # 仅单选
        xgen_layout.addWidget(xgen_label)
        xgen_layout.addWidget(self.xgen_list)
        
        # 中间箭头 - 调整方向为从左到右
        arrow_layout = QtWidgets.QVBoxLayout()
        arrow_layout.addStretch()
        arrow_label = QtWidgets.QLabel("→")
        arrow_layout.addWidget(arrow_label, 0, QtCore.Qt.AlignCenter)
        arrow_layout.addStretch()
        
        # 右侧列表 - 布料几何体（调整位置）
        cloth_layout = QtWidgets.QVBoxLayout()
        cloth_label = QtWidgets.QLabel("毛发生长面 (_DES)")
        self.xgen_mesh_cache_list = QtWidgets.QListWidget()
        self.xgen_mesh_cache_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)  # 仅单选
        cloth_layout.addWidget(cloth_label)
        cloth_layout.addWidget(self.xgen_mesh_cache_list)
        
        # 添加到列表布局 - 调整顺序
        lists_layout.addLayout(xgen_layout, 1)
        lists_layout.addLayout(arrow_layout)
        lists_layout.addLayout(cloth_layout, 1)
        
        # 底部按钮
        button_layout = QtWidgets.QHBoxLayout()
        self.import_xgen_mesh_btn = QtWidgets.QPushButton("导入毛发生长面 Cache")
        self.import_xgen_mesh_btn.setToolTip("导入当前场景对应的毛发生长面缓存文件")
        self.import_xgen_mesh_btn.clicked.connect(self._import_xgen_mesh_cache)
        self.create_btn = QtWidgets.QPushButton("生成 BlendShape")
        self.create_btn.clicked.connect(self._create_blendshape)
        button_layout.addStretch()
        button_layout.addWidget(self.import_xgen_mesh_btn)
        button_layout.addWidget(self.create_btn)
        
        # 添加到主布局
        main_layout.addLayout(lists_layout)
        main_layout.addLayout(button_layout)
        
        # 连接信号
        self.xgen_mesh_cache_list.itemClicked.connect(self._on_xgen_mesh_cache_item_selected)
        self.xgen_list.itemClicked.connect(self._on_xgen_item_selected)
    
    def _populate_lists(self):
        """填充列表数据"""
        # 如果没有选择角色，则返回
        if not self.asset_id:
            return
            
        # 查找带有_DES后缀的布料几何体
        cloth_des_meshes = []
        # 查找场景中带有_DES后缀的布料几何体，按角色过滤
        all_transforms = mc.ls(type="transform")
        for transform in all_transforms:
            # 检查是否属于当前角色并且有_DES后缀
            # 使用小写比较以避免大小写问题，例如"c001"和"C001"
            if (self.asset_id.lower() in transform.lower() or 
                # 为了处理特殊情况，比如角色名称可能是"c001"但几何体命名为"cloth:HeadTOP2_DES"
                (transform.startswith("cloth:") and "_DES" in transform)):
                if "_DES" in transform and not transform.startswith("C001_lookdev:"):
                    shapes = mc.listRelatives(transform, shapes=True, type="mesh")
                    if shapes:
                        cloth_des_meshes.append(transform)
        
        # XGen生长面查找逻辑 - 使用与示例函数相同的简洁逻辑
        xgen_des_meshes = []
        try:
            # 1. 查找所有引用文件
            all_references = mc.ls(type="reference")
            ma_refs = []
            
            # 2. 筛选.ma格式的引用
            for ref in all_references:
                try:
                    # 获取引用节点的文件路径
                    ref_path = mc.referenceQuery(ref, filename=True)
                    if ref_path.lower().endswith(".ma"):
                        ma_refs.append(ref)
                except Exception as e:
                    print(f"处理引用节点 {ref} 时出错: {str(e)}")
            
            # 3. 查找Fur_Grp节点
            fur_grp_nodes = []
            for ref in ma_refs:
                try:
                    # 获取该引用中的所有节点
                    ref_nodes = mc.referenceQuery(ref, nodes=True) or []
                    for node in ref_nodes:
                        # 不区分大小写查找包含Fur_Grp的节点
                        if "fur_grp" in node.lower():
                            fur_grp_nodes.append(node)
                except Exception as e:
                    print(f"处理引用 {ref} 中的节点时出错: {str(e)}")
            
            # 如果没有直接找到Fur_Grp节点，尝试在所有节点中搜索
            if not fur_grp_nodes:
                for transform in all_transforms:
                    if "fur_grp" in transform.lower():
                        fur_grp_nodes.append(transform)
            
            # 4. 获取Fur_Grp下的所有几何体
            all_fur_meshes = []
            for fur_grp in fur_grp_nodes:
                try:
                    # 检查节点是否存在
                    if mc.objExists(fur_grp):
                        # 获取所有子级节点
                        children = mc.listRelatives(fur_grp, allDescendents=True, type="transform") or []
                        for child in children:
                            # 检查是否是网格
                            shapes = mc.listRelatives(child, shapes=True, type="mesh")
                            if shapes:
                                all_fur_meshes.append(child)
                except Exception as e:
                    print(f"处理Fur_Grp {fur_grp} 时出错: {str(e)}")
            
            # 5. 使用示例函数的简洁逻辑检查与XGen的连接关系
            
            # 确保XGen插件已加载
            if not mc.pluginInfo("xgenToolkit", query=True, loaded=True):
                try:
                    mc.loadPlugin("xgenToolkit")
                except Exception as e:
                    print(f"加载XGen插件失败: {str(e)}")
            
            # 检查每个几何体
            for mesh in all_fur_meshes:
                try:
                    # 获取短名称用于输出
                    mesh_short = mesh.split(":")[-1] if ":" in mesh else mesh
                    connected_to_xgm = False
                    connection_reason = ""
                    
                    # 获取shape节点
                    shapes = mc.listRelatives(mesh, shapes=True, fullPath=True) or []
                    if not shapes:
                        continue
                    
                    # 检查每个shape节点的连接
                    for shape in shapes:
                        # 获取所有连接的节点 - 这里是关键，不区分输入/输出连接
                        connections = mc.listConnections(shape) or []
                        
                        # 检查每个连接节点
                        for conn in connections:
                            try:
                                # 获取节点类型
                                conn_type = mc.objectType(conn)
                                
                                # 如果是transform节点，检查它的子节点
                                if conn_type == "transform":
                                    # 检查是否有xgmSubdPatch类型的子节点
                                    children = mc.listRelatives(conn, children=True, type="xgmSubdPatch") or []
                                    if children:
                                        connected_to_xgm = True
                                        connection_reason = f"连接到含xgmSubdPatch子节点的transform: {conn}"
                                        break
                                    
                                    # 检查shape节点
                                    shapes = mc.listRelatives(conn, shapes=True) or []
                                    for child_shape in shapes:
                                        child_type = mc.objectType(child_shape)
                                        if child_type == "xgmSubdPatch" or "xgm" in child_type.lower():
                                            connected_to_xgm = True
                                            connection_reason = f"连接到含xgmSubdPatch形状的transform: {conn}"
                                            break
                                
                                # 直接检查节点类型是否包含xgm - 使用简单的字符串检查
                                elif "xgm" in conn_type.lower():
                                    connected_to_xgm = True
                                    connection_reason = f"直接连接到XGen节点: {conn} (类型: {conn_type})"
                                    break
                            except Exception as e:
                                print(f"检查连接节点 {conn} 时出错: {str(e)}")
                                continue
                            
                            if connected_to_xgm:
                                break
                        
                        if connected_to_xgm:
                            break
                    
                    # 如果没有找到普通连接，尝试历史检查
                    if not connected_to_xgm:
                        for shape in shapes:
                            # 检查历史中是否有xgmSubdPatch节点
                            history = mc.listHistory(shape) or []
                            for hist in history:
                                if hist != shape and hist != mesh:  # 排除自身
                                    try:
                                        hist_type = mc.objectType(hist)
                                        if "xgm" in hist_type.lower():
                                            connected_to_xgm = True
                                            connection_reason = f"历史中有XGen节点: {hist} (类型: {hist_type})"
                                            break
                                    except Exception:
                                        pass
                            
                            if connected_to_xgm:
                                break
                    
                    # 根据结果添加到列表
                    if connected_to_xgm:
                        xgen_des_meshes.append(mesh)
                        
                except Exception as e:
                    print(f"检查 {mesh} 与XGen连接时出错: {str(e)}")
                    
        except Exception as e:
            print(f"查找XGen生长面时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"找到 {len(xgen_des_meshes)} 个XGen生长面")
        
        # 清空并填充列表
        self.xgen_mesh_cache_list.clear()
        self.xgen_list.clear()
        self.cloth_des_items = []
        self.xgen_des_items = []
        
        # 使用正则表达式提取基本名称，用于匹配
        for cloth_mesh in cloth_des_meshes:
            base_name = re.search(r'([^:]+_DES)$', cloth_mesh)
            if base_name:
                item = QtWidgets.QListWidgetItem(cloth_mesh)
                item.setData(QtCore.Qt.UserRole, base_name.group(1))
                self.xgen_mesh_cache_list.addItem(item)
                self.cloth_des_items.append(item)
        
        for xgen_mesh in xgen_des_meshes:
            # 获取短名称用于显示
            short_name = xgen_mesh.split(":")[-1] if ":" in xgen_mesh else xgen_mesh
            item = QtWidgets.QListWidgetItem(xgen_mesh)
            item.setData(QtCore.Qt.UserRole, short_name)
            self.xgen_list.addItem(item)
            self.xgen_des_items.append(item)
                
        # 如果列表为空，显示提示信息
        if self.xgen_mesh_cache_list.count() == 0:
            empty_item = QtWidgets.QListWidgetItem("未找到XGen生长面缓存")
            empty_item.setForeground(QtGui.QColor("gray"))
            self.xgen_mesh_cache_list.addItem(empty_item)
        if self.xgen_list.count() == 0:
            empty_item = QtWidgets.QListWidgetItem("未找到XGen生长面")
            empty_item.setForeground(QtGui.QColor("gray"))
            self.xgen_list.addItem(empty_item)

    def _import_xgen_mesh_cache(self):
        """导入当前场景对应的毛发生长面缓存文件"""
        try:
            # 1. 获取当前场景信息
            current_file = mc.file(q=True, sn=True)
            if not current_file:
                QtWidgets.QMessageBox.warning(self, "警告", "请先保存Maya文件")
                return
                
            # 2. 解析路径信息
            normalized_path = current_file.replace('\\', '/').replace('//', '/')
            path_parts = normalized_path.split('/')
            print(f"Maya文件路径: {normalized_path}")
            
            # 3. 获取episode/sequence/shot信息
            try:
                project_index = path_parts.index("CSprojectFiles")
                
                # 为毛发生长面提取路径组件
                fur_episode = path_parts[project_index + 3] 
                fur_sequence = path_parts[project_index + 4] 
                fur_shot = path_parts[project_index + 5]
                print(f"毛发生长面路径解析: episode={fur_episode}, sequence={fur_sequence}, shot={fur_shot}")
                
            except (ValueError, IndexError) as e:
                # 如果路径解析失败，尝试从文件名提取信息
                file_name = os.path.basename(current_file)
                seq_match = re.search(r'(Sq\d+)', file_name)
                shot_match = re.search(r'(Sc\d+)', file_name)
                
                if seq_match and shot_match:
                    fur_sequence = seq_match.group(1)
                    fur_shot = shot_match.group(1)
                    # 使用默认episode
                    fur_episode = "EP00"
                    print(f"从文件名提取: sequence={fur_sequence}, shot={fur_shot}, 使用默认episode={fur_episode}")
                else:
                    QtWidgets.QMessageBox.warning(
                        self, 
                        "警告", 
                        "无法从当前场景路径解析剧集/场次/镜头信息，请确保文件在正确的项目结构中"
                    )
                    return
            
            # 4. 使用ConfigManager获取路径模板
            from maya_tools.common.config_manager import ConfigManager
            config_manager = ConfigManager()
            
            # 5. 从配置中获取毛发生长面路径模板
            xgen_mesh_cache_template = config_manager.project_config.get("path_templates", {}).get(
                "xgen_mesh_cache", 
                "X:/projects/CSprojectFiles/Shot/CFX/{episode}/{sequence}/{shot}"
            )
            
            # 6. 使用模板生成毛发生长面导入路径
            fur_cache_dir = xgen_mesh_cache_template.format(
                episode=fur_episode,
                sequence=fur_sequence,
                shot=fur_shot
            )
            
            # 7. 添加publish/xgen_mesh子目录
            fur_cache_dir = os.path.join(fur_cache_dir, "publish", "xgen_mesh")
            
            # 8. 检查目录是否存在
            if not os.path.exists(fur_cache_dir):
                QtWidgets.QMessageBox.warning(
                    self, 
                    "警告", 
                    f"毛发生长面缓存目录不存在:\n{fur_cache_dir}"
                )
                return
                
            # 9. 获取当前资产ID
            asset_id = self.asset_id
            if not asset_id:
                QtWidgets.QMessageBox.warning(self, "警告", "无法确定资产ID，请先选择资产")
                return
                
            # 创建进度对话框
            progress_dialog = QtWidgets.QProgressDialog("搜索毛发生长面缓存文件...", "取消", 0, 100, self)
            progress_dialog.setWindowTitle("导入毛发生长面")
            progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
            progress_dialog.setValue(10)
            progress_dialog.show()
            QtWidgets.QApplication.processEvents()
            
            # 10. 在目录中查找匹配当前资产的.abc文件
            matching_files = []
            file_pattern = f"{fur_sequence}_{fur_shot}_xgenMesh_{asset_id.lower()}_*.abc"
            print(f"搜索文件模式: {file_pattern}")
            
            progress_dialog.setLabelText(f"搜索匹配文件: {file_pattern}")
            progress_dialog.setValue(30)
            QtWidgets.QApplication.processEvents()
            
            # 列出所有匹配的文件 - 改进匹配逻辑，忽略xgenMesh部分的大小写
            for filename in os.listdir(fur_cache_dir):
                # 使用正则表达式进行更灵活的匹配，忽略xgenMesh部分的大小写
                file_lower = filename.lower()
                pattern_lower = f"{fur_sequence.lower()}_{fur_shot.lower()}_xgenmesh_{asset_id.lower()}_"
                
                # 检查文件名是否匹配模式并以.abc结尾
                if file_lower.startswith(pattern_lower) and file_lower.endswith(".abc"):
                    matching_files.append(filename)
                    print(f"找到匹配文件: {filename}")
                    
            # 备用方案：如果未找到文件，尝试直接列出目录内容并手动检查
            if not matching_files:
                print(f"未找到匹配的文件，列出目录内容:")
                try:
                    all_files = os.listdir(fur_cache_dir)
                    for file in all_files:
                        print(f"  - {file}")
                        
                        # 使用更宽松的匹配条件，只检查关键部分
                        if (asset_id.lower() in file.lower() and 
                            fur_sequence.lower() in file.lower() and 
                            fur_shot.lower() in file.lower() and 
                            file.lower().endswith(".abc")):
                            print(f"  ✓ 使用宽松条件匹配到文件: {file}")
                            matching_files.append(file)
                except Exception as e:
                    print(f"列出目录内容时出错: {str(e)}")
            
            if not matching_files:
                progress_dialog.close()
                QtWidgets.QMessageBox.warning(
                    self, 
                    "警告", 
                    f"未找到匹配的毛发生长面缓存文件。\n搜索路径: {fur_cache_dir}\n文件模式: {file_pattern}"
                )
                return
                
            # 如果找到多个文件，使用最新的文件
            if len(matching_files) > 1:
                print(f"找到多个匹配文件，将使用最新的文件")
                # 按修改时间排序
                matching_files.sort(key=lambda x: os.path.getmtime(os.path.join(fur_cache_dir, x)), reverse=True)
            
            selected_file = matching_files[0]
            full_path = os.path.join(fur_cache_dir, selected_file).replace("\\", "/")
            print(f"选择文件: {full_path}")
            
            progress_dialog.setLabelText(f"准备引用文件: {selected_file}")
            progress_dialog.setValue(50)
            QtWidgets.QApplication.processEvents()
            
            # 11. 创建命名空间 - 使用资产ID加上_XGM后缀
            namespace = f"{asset_id}_XGM"
            
            # 检查是否已存在相同的命名空间
            existing_refs = mc.ls(type="reference")
            for ref in existing_refs:
                try:
                    ref_path = mc.referenceQuery(ref, filename=True)
                    ref_ns = mc.referenceQuery(ref, namespace=True)
                    
                    # 如果找到同名命名空间的引用
                    if ref_ns == namespace:
                        # 询问用户是否替换
                        reply = QtWidgets.QMessageBox.question(
                            self, 
                            "确认", 
                            f"已存在命名空间为 '{namespace}' 的引用。\n是否移除并重新引用？",
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                            QtWidgets.QMessageBox.No
                        )
                        
                        if reply == QtWidgets.QMessageBox.Yes:
                            # 移除现有引用
                            mc.file(ref_path, removeReference=True)
                            print(f"已移除现有引用: {ref_path}")
                        else:
                            progress_dialog.close()
                            return
                except Exception as e:
                    print(f"检查引用 {ref} 时出错: {str(e)}")
            
            progress_dialog.setLabelText("引用文件中...")
            progress_dialog.setValue(70)
            QtWidgets.QApplication.processEvents()
            
            # 12. 引用ABC文件
            try:
                # 使用reference模式而不是import模式，这样可以保持原始层级结构
                progress_dialog.setLabelText("引用文件中...")
                progress_dialog.setValue(70)
                QtWidgets.QApplication.processEvents()
                
                # 使用Maya的标准file命令引用ABC文件，而不是AbcImport
                # 这样可以保持文件的原始结构和命名空间
                try:
                    # 尝试方法1: 使用file命令引用
                    mc.file(full_path, reference=True, namespace=namespace)
                    print(f"✓ 使用file命令成功引用文件: {full_path}")
                    result = True
                except Exception as e1:
                    print(f"使用file命令引用失败: {str(e1)}")
                    
                    # 尝试方法2: 使用AbcImport命令引用，但使用reference模式
                    try:
                        import_cmd = f'AbcImport -mode reference -reparent "{namespace}:" "{full_path}";'
                        print(f"执行引用命令: {import_cmd}")
                        result = mel.eval(import_cmd)
                        print(f"AbcImport reference模式结果: {result}")
                    except Exception as e2:
                        print(f"AbcImport reference模式失败: {str(e2)}")
                        
                        # 尝试方法3: 使用原始AbcImport方法，但不指定连接节点
                        try:
                            # 创建命名空间
                            if not mc.namespace(exists=namespace):
                                mc.namespace(add=namespace)
                            
                            # 不指定连接节点，让Maya自动处理层级
                            import_cmd = f'AbcImport -mode import "{full_path}" -wcs -reparent "{namespace}:";'
                            print(f"执行最终引用命令: {import_cmd}")
                            result = mel.eval(import_cmd)
                            print(f"最终AbcImport结果: {result}")
                        except Exception as e3:
                            print(f"最终导入方法也失败: {str(e3)}")
                            result = False
                            raise Exception(f"所有引用方法均失败:\n方法1: {str(e1)}\n方法2: {str(e2)}\n方法3: {str(e3)}")
                
                if result:
                    progress_dialog.setLabelText("引用成功!")
                    progress_dialog.setValue(100)
                    QtWidgets.QApplication.processEvents()
                    
                    mc.inViewMessage(
                        amg=f"成功引用毛发生长面缓存: <hl>{selected_file}</hl>",
                        pos='midCenter',
                        fade=True,
                        fadeOutTime=3.0
                    )
                    
                    # 列出引用的节点，帮助用户了解导入的内容
                    try:
                        imported_nodes = mc.ls(f"{namespace}:*", long=True)
                        print(f"成功引用，导入了 {len(imported_nodes)} 个节点:")
                        for i, node in enumerate(imported_nodes[:10]):  # 仅显示前10个
                            print(f"  {i+1}. {node}")
                        if len(imported_nodes) > 10:
                            print(f"  ... 以及其他 {len(imported_nodes)-10} 个节点")
                        
                        # 新增：根据左侧列表筛选匹配的几何体并添加到右侧列表
                        self._filter_and_display_imported_meshes(namespace, imported_nodes)
                        
                        # 新增：隐藏导入的顶层组
                        self._hide_top_level_group(namespace)
                    except Exception as e:
                        print(f"列出导入节点时出错: {str(e)}")
                    
                    # 关闭进度对话框
                    progress_dialog.close()
                else:
                    progress_dialog.close()
                    QtWidgets.QMessageBox.warning(
                        self, 
                        "警告", 
                        f"引用命令未返回有效结果，请检查命令输出"
                    )
            except Exception as e:
                progress_dialog.close()
                QtWidgets.QMessageBox.critical(
                    self, 
                    "错误", 
                    f"引用ABC文件时出错:\n{str(e)}"
                )
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, 
                "错误", 
                f"导入毛发生长面缓存时发生错误:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def _filter_and_display_imported_meshes(self, namespace, imported_nodes):
        """筛选出与左侧XGen生长面匹配的导入节点并显示在右侧列表中"""
        try:
            print("开始筛选匹配的毛发生长面缓存几何体...")
            
            # 清空右侧列表
            self.xgen_mesh_cache_list.clear()
            self.cloth_des_items = []
            
            # 如果左侧没有XGen生长面项目，则无法进行匹配
            if not self.xgen_des_items:
                print("左侧列表中没有XGen生长面，无法进行匹配")
                empty_item = QtWidgets.QListWidgetItem("未找到匹配的XGen生长面缓存")
                empty_item.setForeground(QtGui.QColor("gray"))
                self.xgen_mesh_cache_list.addItem(empty_item)
                return
            
            # 获取所有导入的Mesh几何体
            imported_meshes = []
            for node in imported_nodes:
                # 只检查transform节点
                if mc.objectType(node) == "transform":
                    # 查找该节点下的mesh形状节点
                    shapes = mc.listRelatives(node, shapes=True, type="mesh") or []
                    if shapes:
                        # 获取短名称用于比较
                        short_name = node.split(":")[-1] if ":" in node else node
                        imported_meshes.append({"full_path": node, "short_name": short_name})
            
            print(f"导入的几何体数量: {len(imported_meshes)}")
            
            # 收集左侧列表中的XGen生长面名称
            xgen_names = []
            for i in range(self.xgen_list.count()):
                item = self.xgen_list.item(i)
                if item.text() != "未找到XGen生长面":
                    xgen_full_path = item.text()
                    # 获取短名称
                    xgen_short_name = xgen_full_path.split(":")[-1] if ":" in xgen_full_path else xgen_full_path
                    xgen_names.append({"full_path": xgen_full_path, "short_name": xgen_short_name})
            
            print(f"左侧XGen生长面数量: {len(xgen_names)}")
            
            # 匹配导入的几何体与左侧XGen生长面
            matched_meshes = []
            for imported_mesh in imported_meshes:
                for xgen_name in xgen_names:
                    # 基本名称匹配（忽略可能的后缀差异）
                    if xgen_name["short_name"] in imported_mesh["short_name"] or imported_mesh["short_name"] in xgen_name["short_name"]:
                        matched_meshes.append(imported_mesh)
                        print(f"找到匹配: {imported_mesh['full_path']} 匹配 {xgen_name['full_path']}")
                        break
            
            print(f"匹配的几何体数量: {len(matched_meshes)}")
            
            # 添加匹配的几何体到右侧列表
            if matched_meshes:
                for mesh in matched_meshes:
                    # 在右侧列表添加匹配的几何体
                    item = QtWidgets.QListWidgetItem(mesh["full_path"])
                    base_name = mesh["short_name"]
                    if "_DES" in base_name:
                        # 提取基本名称，用于后续匹配
                        des_match = re.search(r'([^:]+_DES)$', base_name)
                        if des_match:
                            base_name = des_match.group(1)
                    item.setData(QtCore.Qt.UserRole, base_name)
                    self.xgen_mesh_cache_list.addItem(item)
                    self.cloth_des_items.append(item)
                    
                    # 设置工具提示
                    item.setToolTip(f"导入的毛发生长面缓存\n原始路径: {mesh['full_path']}")
            else:
                # 如果没有匹配的几何体，显示提示
                empty_item = QtWidgets.QListWidgetItem("未找到匹配的XGen生长面缓存")
                empty_item.setForeground(QtGui.QColor("gray"))
                self.xgen_mesh_cache_list.addItem(empty_item)
                print("没有找到与左侧XGen生长面匹配的导入几何体")
        
        except Exception as e:
            print(f"筛选匹配几何体时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _hide_top_level_group(self, namespace):
        """隐藏导入的顶层组"""
        try:
            # 查找命名空间下的顶层节点
            top_nodes = []
            # 获取该命名空间下的所有节点
            all_ns_nodes = mc.ls(f"{namespace}:*", long=False) or []
            
            # 寻找顶层节点 - 通常是那些没有父节点或父节点不在同一命名空间的节点
            for node in all_ns_nodes:
                if mc.objectType(node) == "transform":
                    parent = mc.listRelatives(node, parent=True, fullPath=True)
                    # 如果没有父节点或父节点不属于同一命名空间，则认为是顶层节点
                    if not parent or not parent[0].startswith(f"{namespace}:"):
                        top_nodes.append(node)
                        print(f"找到顶层节点: {node}")
            
            # 如果找到顶层节点，则隐藏它们
            if top_nodes:
                for node in top_nodes:
                    try:
                        mc.setAttr(f"{node}.visibility", 0)
                        print(f"已隐藏顶层节点: {node}")
                    except Exception as e:
                        print(f"隐藏节点 {node} 时出错: {str(e)}")
                
                print(f"成功隐藏了 {len(top_nodes)} 个顶层节点")
                
                # 显示消息
                mc.inViewMessage(
                    amg=f"已自动隐藏导入的毛发生长面顶层组",
                    pos='midCenterTop',
                    fade=True,
                    fadeOutTime=3.0
                )
            else:
                print(f"未找到命名空间 {namespace} 下的顶层节点")
        except Exception as e:
            print(f"隐藏顶层组时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def _on_xgen_mesh_cache_item_selected(self, item):
        """当布料几何体列表项被选中时"""
        # 检查是否是提示信息项
        if item.text() == "未找到XGen生长面":
            return
            
        base_name = item.data(QtCore.Qt.UserRole)
        if not base_name:
            return
            
        # 在XGen列表中查找对应项并选中
        for i in range(self.xgen_list.count()):
            xgen_item = self.xgen_list.item(i)
            if xgen_item.text() != "未找到XGen生长面" and xgen_item.data(QtCore.Qt.UserRole) == base_name:
                self.xgen_list.setCurrentItem(xgen_item)
                break
    
    def _on_xgen_item_selected(self, item):
        """当XGen生长面列表项被选中时"""
        # 检查是否是提示信息项
        if item.text() == "未找到XGen生长面":
            return
            
        base_name = item.data(QtCore.Qt.UserRole)
        if not base_name:
            return
            
        # 在布料几何体列表中查找对应项并选中
        for i in range(self.xgen_mesh_cache_list.count()):
            cloth_item = self.xgen_mesh_cache_list.item(i)
            if cloth_item.text() != "未找到布料几何体" and cloth_item.data(QtCore.Qt.UserRole) == base_name:
                self.xgen_mesh_cache_list.setCurrentItem(cloth_item)
                break
                
    def _create_blendshape(self):
        """创建BlendShape节点连接布料几何体和XGen生长面"""
        # 获取当前选中的布料几何体和XGen生长面
        xgen_mesh_cache_item = self.xgen_mesh_cache_list.currentItem()
        xgen_item = self.xgen_list.currentItem()
        
        # 检查是否都有选中项且不是提示信息
        if (not xgen_mesh_cache_item or not xgen_item or
            xgen_mesh_cache_item.text() == "未找到布料几何体" or
            xgen_item.text() == "未找到XGen生长面"):
            QtWidgets.QMessageBox.warning(
                self, 
                "错误", 
                "请先选择一对有效的布料几何体和XGen生长面"
            )
            return
        
        # 获取完整路径
        xgen_mesh_cache_path = xgen_mesh_cache_item.text()
        xgen_path = xgen_item.text()
        
        # 开始创建BlendShape
        try:
            # 检查几何体是否存在
            if not mc.objExists(xgen_mesh_cache_path) or not mc.objExists(xgen_path):
                mc.warning(f"几何体不存在: {xgen_mesh_cache_path} 或 {xgen_path}")
                QtWidgets.QMessageBox.warning(
                    self, 
                    "错误", 
                    f"几何体不存在: \n{xgen_mesh_cache_path} \n或 \n{xgen_path}"
                )
                return
            
            # 提取简短名称用于节点命名
            cloth_short = xgen_mesh_cache_path.split(":")[-1] if ":" in xgen_mesh_cache_path else xgen_mesh_cache_path
            xgen_short = xgen_path.split(":")[-1] if ":" in xgen_path else xgen_path
            bs_name = f"{xgen_short}_to_match_{cloth_short}_BS"
            
            # 创建进度对话框
            progress_dialog = QtWidgets.QProgressDialog("创建BlendShape...", "取消", 0, 100, self)
            progress_dialog.setWindowTitle("进度")
            progress_dialog.setValue(10)
            progress_dialog.show()
            QtWidgets.QApplication.processEvents()
            
            # 检查是否已存在同名的BlendShape节点
            if mc.objExists(bs_name):
                # 询问用户是否替换
                reply = QtWidgets.QMessageBox.question(
                    self, 
                    "确认", 
                    f"BlendShape节点 '{bs_name}' 已存在。\n是否删除并重新创建？",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    # 删除现有节点
                    mc.delete(bs_name)
                else:
                    progress_dialog.close()
                    return
            
            # 更新进度
            progress_dialog.setValue(30)
            QtWidgets.QApplication.processEvents()
            
            # 创建BlendShape节点
            # 正确的顺序：布料几何体作为目标形状，XGen生长面作为要变形的对象
            # 第一个参数是目标形状，第二个参数是要变形的对象
            blendshape = mc.blendShape(xgen_mesh_cache_path, xgen_path, name=bs_name, weight=(0, 1.0))
            
            # 更新进度
            progress_dialog.setValue(70)
            QtWidgets.QApplication.processEvents()
            
            # 设置权重为1.0 - 确保生长面立即匹配到布料几何体的形状
            if blendshape:
                # 获取目标索引名称 - 通常是布料几何体的短名称
                target_alias = cloth_short
                # 设置BlendShape权重为1.0，使XGen生长面完全变形到布料几何体的形状
                mc.setAttr(f"{blendshape[0]}.{target_alias}", 1.0)
            
            # 关闭进度对话框
            progress_dialog.setValue(100)
            progress_dialog.close()
            
            # 显示成功消息
            QtWidgets.QMessageBox.information(
                self, 
                "成功", 
                f"成功创建BlendShape：\n{bs_name}\n\n变形对象：{xgen_path}\n变形目标：{xgen_mesh_cache_path}\n\n权重已设置为1.0"
            )
            
            # 打印日志消息
            mc.inViewMessage(
                amg=f"成功创建BlendShape: <hl>{bs_name}</hl>",
                pos='midCenter',
                fade=True,
                fadeOutTime=3.0
            )
            
        except Exception as e:
            # 处理可能的错误
            error_msg = str(e)
            mc.warning(f"创建BlendShape时出错: {error_msg}")
            QtWidgets.QMessageBox.critical(
                self, 
                "错误", 
                f"创建BlendShape时出错:\n{error_msg}"
            )
            
            # 关闭进度对话框
            if 'progress_dialog' in locals() and progress_dialog.isVisible():
                progress_dialog.close()


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

        self.xgen_blendshape_btn = QtWidgets.QPushButton("毛发生长面 BS")
        self.xgen_blendshape_btn.setToolTip("为XGen生长面和布料几何体创建BlendShape")
        self.xgen_blendshape_btn.clicked.connect(self._show_xgen_blendshape_dialog)
        
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
        
        xgen_btn_layout.addWidget(self.xgen_blendshape_btn)
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

    def _show_xgen_blendshape_dialog(self):
        """显示XGen生长面与布料几何体BlendShape对话框"""
        # 检查是否选择了asset_id
        if not hasattr(self, 'current_asset_id') or not self.current_asset_id:
            # 显示提示对话框
            self._show_import_result_dialog(
                "错误", 
                "请先在资产列表中选择一个角色，然后再使用毛发生长面 BS 功能。", 
                error=True
            )
            return
        
        # 创建并显示对话框，传入当前选中的角色ID
        dialog = XGenBlendShapeDialog(self, self.current_asset_id)
        dialog.exec_() 