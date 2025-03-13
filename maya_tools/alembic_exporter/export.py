import maya.cmds as cmds
import maya.mel as mel
from maya_tools.alembic_exporter.core.settings import AlembicExportSettings
from maya_tools.alembic_exporter.core.helpers import get_char_geometry_from_references, get_prop_geometry_from_references, get_fur_groups
import os
import json
import re

# 导入ConfigManager
from maya_tools.common.config_manager import ConfigManager


def _get_scene_info():
    """获取场景信息，包括帧范围、文件路径和项目结构信息"""
    # 加载配置
    config_manager = ConfigManager()
    
    # 获取当前时间线的起始帧和结束帧
    start_frame = cmds.playbackOptions(q=True, min=True)
    end_frame = cmds.playbackOptions(q=True, max=True)
    
    # 计算导出帧范围
    start_export_frame = 50
    end_export_frame = end_frame + 4
    
    # 获取当前Maya文件路径并创建缓存目录
    current_file = cmds.file(q=True, sn=True)
    if not current_file:
        raise RuntimeError("请先保存Maya文件")
        
    # 解析路径信息
    normalized_path = current_file.replace('\\', '/').replace('//', '/')
    path_parts = normalized_path.split('/')
    print(f"\n======== Maya文件路径解析 ========")
    print(f"Maya文件路径: {normalized_path}")
    print(f"路径部分: {path_parts}")
    
    # 常规路径解析（用于普通的角色和道具导出）
    try:
        project_index = path_parts.index("CSprojectFiles")
        
        # 提取标准路径组件 - 用于角色和道具（原始索引）
        char_prop_episode = path_parts[project_index + 4] 
        char_prop_sequence = path_parts[project_index + 5] 
        char_prop_shot = path_parts[project_index + 6]
        print(f"角色和道具路径解析: episode={char_prop_episode}, sequence={char_prop_sequence}, shot={char_prop_shot}")
        
        # 为毛发生长面提取正确的路径组件（修正后的索引）
        fur_episode = path_parts[project_index + 3] 
        fur_sequence = path_parts[project_index + 4] 
        fur_shot = path_parts[project_index + 5] 
        print(f"毛发生长面路径解析: episode={fur_episode}, sequence={fur_sequence}, shot={fur_shot}")
        
    except (ValueError, IndexError) as e:
        print(f"路径解析错误: {str(e)}")
        print(f"路径部分: {path_parts}")
        raise RuntimeError("文件路径结构不符合预期，请确保文件在正确的项目结构中")
        
    file_dir = os.path.dirname(current_file)
    cache_dir = os.path.join(file_dir, "abc_cache")
    
    # 创建缓存主目录
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # 从文件名中提取额外信息
    file_name = os.path.basename(current_file)
    print(f"\n======== 文件名分析 ========")
    print(f"Maya文件名: {file_name}")
    
    # 尝试从文件名提取sequence和shot
    seq_match = re.search(r'(Sq\d+)', file_name)
    shot_match = re.search(r'(Sc\d+)', file_name)
    
    file_sequence = None
    file_shot = None
    
    if seq_match:
        file_sequence = seq_match.group(1)
        print(f"从文件名提取的sequence: {file_sequence}")
        # 如果从路径中提取失败，使用文件名中的
        if not fur_sequence:
            fur_sequence = file_sequence
    
    if shot_match:
        file_shot = shot_match.group(1)
        print(f"从文件名提取的shot: {file_shot}")
        # 如果从路径中提取失败，使用文件名中的
        if not fur_shot:
            fur_shot = file_shot

    # 分析期望的路径与当前路径的差异
    print(f"\n======== 路径结构分析 ========")
    print(f"角色和道具: episode={char_prop_episode}, sequence={char_prop_sequence}, shot={char_prop_shot}")
    print(f"毛发生长面: episode={fur_episode}, sequence={fur_sequence}, shot={fur_shot}")
    print(f"从文件名提取: sequence={file_sequence}, shot={file_shot}")
    
    # 从配置中获取毛发生长面路径模板
    xgen_mesh_cache_template = config_manager.project_config.get("path_templates", {}).get(
        "xgen_mesh_cache", 
        "X:/projects/CSprojectFiles/Shot/CFX/{episode}/{sequence}/{shot}"
    )
    
    # 使用模板生成毛发生长面导出路径
    fur_cache_dir = xgen_mesh_cache_template.format(
        episode=fur_episode,
        sequence=fur_sequence,
        shot=fur_shot
    )
    
    # 添加publish/xgen_mesh子目录
    fur_cache_dir = os.path.join(fur_cache_dir, "publish", "xgen_mesh")
    print(f"\n毛发生长面导出路径: {fur_cache_dir}")
    
    # 创建目录（如果不存在）
    if not os.path.exists(fur_cache_dir):
        try:
            os.makedirs(fur_cache_dir)
            print(f"成功创建目录: {fur_cache_dir}")
        except Exception as e:
            print(f"创建目录出错: {str(e)}")
    
    print("======== 路径分析结束 ========\n")
        
    return {
        "start_frame": start_frame,
        "end_frame": end_frame,
        "start_export_frame": start_export_frame,
        "end_export_frame": end_export_frame,
        "current_file": current_file,
        "file_dir": file_dir,
        "cache_dir": cache_dir,
        "fur_cache_dir": fur_cache_dir,
        "episode": char_prop_episode,  # 保留原有的episode用于角色和道具
        "sequence": char_prop_sequence,  # 保留原有的sequence用于角色和道具
        "shot": char_prop_shot,  # 保留原有的shot用于角色和道具
        "fur_episode": fur_episode,  # 毛发专用episode
        "fur_sequence": fur_sequence,  # 毛发专用sequence
        "fur_shot": fur_shot,  # 毛发专用shot
        "file_name": file_name  # 添加文件名
    }


def _find_asset_geometry(asset_type="char"):
    """查找场景中指定类型资产的几何体
    
    Args:
        asset_type: 资产类型，"char"表示角色，"prop"表示道具，"fur"表示毛发生长面
        
    Returns:
        dict: 资产ID到几何体组的映射
    """
    if asset_type == "char":
        # 使用现有的helper函数获取角色几何体
        return get_char_geometry_from_references()
    
    elif asset_type == "prop":
        # 查找道具几何体
        return get_prop_geometry_from_references()
    
    elif asset_type == "fur":
        # 查找毛发生长面组
        return get_fur_groups()
    
    else:
        raise ValueError(f"不支持的资产类型: {asset_type}")


def _make_geometries_visible(nodes, restore_info=None):
    """临时设置几何体为可见状态，并返回原始状态信息用于恢复
    
    Args:
        nodes: 要处理的节点列表/字符串
        restore_info: 之前保存的状态信息，如果提供则用于恢复状态
        
    Returns:
        dict: 包含原始可见性状态的字典，用于后续恢复
    """
    if restore_info is not None:
        # 恢复模式 - 恢复之前的状态
        print("正在恢复几何体原始可见性状态...")
        for node, vis_value in restore_info.items():
            if cmds.objExists(node):
                try:
                    cmds.setAttr(f"{node}.visibility", vis_value)
                except Exception as e:
                    print(f"恢复节点 {node} 的可见性时出错: {str(e)}")
        return None
    
    # 保存当前状态并设置为可见
    visibility_info = {}
    all_nodes = []
    
    # 处理输入可能是单个节点或节点列表
    if isinstance(nodes, str):
        # 获取节点及其所有子节点
        all_nodes.append(nodes)
        children = cmds.listRelatives(nodes, allDescendents=True, fullPath=True) or []
        all_nodes.extend(children)
    else:
        # 输入已经是节点列表
        all_nodes = nodes
        for node in nodes:
            children = cmds.listRelatives(node, allDescendents=True, fullPath=True) or []
            all_nodes.extend(children)
    
    # 获取所有变换节点和形状节点
    transform_nodes = [n for n in all_nodes if cmds.objectType(n) == "transform"]
    
    # 处理所有找到的节点
    processed_nodes = 0
    hidden_nodes = 0
    
    for node in transform_nodes:
        try:
            # 检查当前可见性
            if cmds.attributeQuery("visibility", node=node, exists=True):
                current_vis = cmds.getAttr(f"{node}.visibility")
                visibility_info[node] = current_vis
                
                # 如果当前隐藏，则设置为可见
                if not current_vis:
                    cmds.setAttr(f"{node}.visibility", True)
                    hidden_nodes += 1
                
                processed_nodes += 1
        except Exception as e:
            print(f"处理节点 {node} 时出错: {str(e)}")
    
    print(f"处理了 {processed_nodes} 个节点，临时显示了 {hidden_nodes} 个隐藏的几何体")
    return visibility_info


def _export_abc_file(asset_id, geometry, scene_info, settings, asset_type_name="角色"):
    """导出单个资产的ABC缓存文件
    
    Args:
        asset_id: 资产ID，如 "C001" 或 "P001"，或带序号的"c001_01"
        geometry: 几何体组节点
        scene_info: 场景信息字典
        settings: 导出设置
        asset_type_name: 资产类型名称，用于日志显示
        
    Returns:
        str: 导出的文件路径
    """
    # 选择正确的缓存目录
    if asset_type_name == "毛发生长面" and scene_info.get("fur_cache_dir"):
        # 使用配置的毛发缓存目录
        base_cache_dir = scene_info["fur_cache_dir"]
        print(f"使用毛发专用缓存路径: {base_cache_dir}")
        
        # 毛发生长面不需要创建资产子目录，直接使用base_cache_dir
        asset_cache_dir = base_cache_dir
        
        # 从asset_id中提取基础ID和序号部分
        # 例如: "c001_02" -> 基础ID="c001", 序号="02"
        if "_" in asset_id:
            # 如果asset_id中已有序号（如c001_01），则拆分它
            base_id, index = asset_id.rsplit("_", 1)
            print(f"拆分资产ID: 基础ID={base_id}, 序号={index}")
        else:
            # 如果asset_id中没有序号，则使用基础ID和默认序号01
            base_id = asset_id
            index = "01"
            print(f"使用基础资产ID: {base_id}, 默认序号: {index}")
        
        # 使用毛发专用的sequence和shot构建文件名
        sequence = scene_info.get("fur_sequence", "Sq03")  # 毛发专用sequence
        shot = scene_info.get("fur_shot", "Sc0090")         # 毛发专用shot
        
        print(f"毛发文件命名使用: sequence={sequence}, shot={shot}")
        
        # 构建文件名
        cache_name = f"{sequence}_{shot}_xgenMesh_{base_id}_{index}.abc"
        print(f"最终输出文件名: {cache_name}")
    else:
        # 使用默认缓存目录
        base_cache_dir = scene_info["cache_dir"]
        
        # 创建资产专属缓存子目录
        asset_cache_dir = os.path.join(base_cache_dir, asset_id)
        if not os.path.exists(asset_cache_dir):
            os.makedirs(asset_cache_dir)
        
        # 构建常规缓存文件路径（使用原有的episode、sequence和shot）
        cache_name = f"{scene_info['episode']}_{scene_info['sequence']}_{scene_info['shot']}_{asset_id}.abc"
    
    # 确保目录存在
    if not os.path.exists(asset_cache_dir):
        os.makedirs(asset_cache_dir)
    
    # 构建完整的导出路径
    export_path = os.path.join(asset_cache_dir, cache_name).replace('\\', '/')
    print(f"最终完整导出路径: {export_path}")
    
    # 为毛发生长面特别处理：确保renderableOnly为false，导出所有几何体
    renderable_only_value = 'false' if asset_type_name == "毛发生长面" else settings.renderable_only
    # 必须同时处理其他可能阻止隐藏几何体导出的参数
    no_intermediates_value = 'false' if asset_type_name == "毛发生长面" else 'true'
    
    if asset_type_name == "毛发生长面":
        print("⚠️ 毛发生长面导出：设置特殊参数确保隐藏几何体被导出")
        print("  - renderableOnly=false: 包括不可渲染的对象")
        print("  - noIntermediate=false: 包括中间对象")
        
        # 临时修改所有几何体的可见性（毛发生长面特殊处理）
        visibility_backup = _make_geometries_visible(geometry)
        print("已临时设置所有几何体为可见状态，将在导出后恢复")
    
    # 构建导出命令
    command = (
        f'AbcExport -j "-frameRange {scene_info["start_export_frame"]} {scene_info["end_export_frame"]} '
        f'-root {geometry} -file {export_path} '
        f'-verbose {settings.verbose} '
        f'-renderableOnly {renderable_only_value} '
        f'-noIntermediate {no_intermediates_value} '
        f'-writeColorSets {settings.write_color_sets} '
        f'-writeFaceSets {settings.write_face_sets} '
        f'-worldSpace {settings.world_space} '
        f'-writeVisibility {settings.write_visibility} '
        f'-writeCreases {settings.write_creases} '
        f'-writeUVSets {settings.write_uv_sets} '
        f'-uvWrite {settings.uv_write} '
        f'-eulerFilter {settings.euler_filter} '
        f'-dataFormat {settings.data_format} "'
    )
    
    try:
        print(f"正在导出{asset_type_name} {asset_id} 的 Alembic 缓存...")
        print(f"导出命令: {command}")
        result = mel.eval(command)
        
        # 导出后恢复可见性状态（如果是毛发生长面）
        if asset_type_name == "毛发生长面" and visibility_backup:
            _make_geometries_visible(None, visibility_backup)
            print("已恢复几何体的原始可见性状态")
        
        if os.path.exists(export_path):
            print(f"成功导出{asset_type_name} {asset_id} 的 Alembic 缓存到: {export_path}")
            return export_path
        else:
            raise RuntimeError(f"导出命令执行成功但未找到输出文件: {export_path}")
            
    except Exception as e:
        # 确保异常情况下也恢复可见性
        if asset_type_name == "毛发生长面" and visibility_backup:
            _make_geometries_visible(None, visibility_backup)
            print("已恢复几何体的原始可见性状态")
        
        raise RuntimeError(f"导出{asset_type_name} {asset_id} 的 Alembic 缓存时发生错误: {str(e)}")


def _export_assets(asset_type, asset_type_name):
    """导出指定类型的资产
    
    Args:
        asset_type: 资产类型，"char"表示角色，"prop"表示道具
        asset_type_name: 资产类型名称，用于日志显示
        
    Returns:
        list: 导出的文件路径列表
    """
    # 获取场景信息
    scene_info = _get_scene_info()
    
    # 获取导出设置
    settings = AlembicExportSettings()
    
    # 获取资产几何体
    asset_geometries = _find_asset_geometry(asset_type)
    
    # 检查是否找到资产
    if not asset_geometries:
        raise RuntimeError(f"场景中未找到任何{asset_type_name}模型")
    
    # 为每个资产创建单独的缓存
    exported_files = []
    for asset_id, geometry_groups in asset_geometries.items():
        if not geometry_groups:
            print(f"警告：未找到{asset_type_name} {asset_id} 的几何体组")
            continue
        
        for index, geometry in enumerate(geometry_groups, 1):
            try:
                # 如果有多个几何体组，添加后缀
                export_id = asset_id
                if len(geometry_groups) > 1:
                    export_id = f"{asset_id}_{index:02d}"
                
                export_path = _export_abc_file(export_id, geometry, scene_info, settings, asset_type_name)
                exported_files.append(export_path)
            except Exception as e:
                print(f"导出{asset_type_name} {asset_id} 时出错: {str(e)}")
    
    return exported_files


def export_char_alembic():
    """导出场景中的角色模型到Alembic缓存"""
    return _export_assets("char", "角色")


def export_prop_alembic():
    """导出场景中的道具模型到Alembic缓存"""
    return _export_assets("prop", "道具")


def export_fur_alembic():
    """导出场景中的毛发生长面(Fur_Grp)到Alembic缓存"""
    print("\n==== 毛发生长面导出 ====")
    print("将导出所有毛发生长面几何体，包括隐藏的几何体")
    print("⚠️ 注意：如果有隐藏几何体，会临时设置为可见状态进行导出，导出后将恢复原始状态")
    
    # 运行标准导出流程
    result = _export_assets("fur", "毛发生长面")
    
    # 导出后提供路径信息
    if result:
        print(f"\n成功导出 {len(result)} 个毛发生长面")
        print(f"首个导出路径: {result[0] if result else '无'}")
    else:
        print("\n未能导出任何毛发生长面，请检查是否有Fur_Grp节点")
    
    return result

def export_alembic():
    """导出所有角色和道具的Alembic缓存"""
    char_files = []
    prop_files = []
    
    try:
        char_files = export_char_alembic()
        print(f"成功导出 {len(char_files)} 个角色的 Alembic 缓存")
    except Exception as e:
        print(f"导出角色时出错: {str(e)}")
    
    try:
        prop_files = export_prop_alembic()
        print(f"成功导出 {len(prop_files)} 个道具的 Alembic 缓存")
    except Exception as e:
        print(f"导出道具时出错: {str(e)}")
    
    return char_files + prop_files

def export_xgen_guides(guides_list, asset_id=None, collection=None, start_frame=None, end_frame=None, export_dir=None):
    """导出XGen Guides到Alembic缓存，每个guide物体单独导出一个abc文件
    
    Args:
        guides_list (list): 要导出的guides物体列表
        asset_id (str): 资产ID，如c001_01
        collection (str): Collection名称，如COL_Hair
        start_frame (int, optional): 开始帧. Defaults to None.
        end_frame (int, optional): 结束帧. Defaults to None.
        export_dir (str): 导出目录路径
    
    Returns:
        list: 导出的文件路径列表
    """
    if not guides_list or not asset_id or not collection or not export_dir:
        return []
    
    # 如果未指定帧范围，使用当前时间线范围
    if start_frame is None:
        start_frame = cmds.playbackOptions(query=True, minTime=True)
    if end_frame is None:
        end_frame = cmds.playbackOptions(query=True, maxTime=True)
        
    exported_files = []
    
    # 遍历每个guides物体进行导出
    for guide in guides_list:
        try:
            # 移除namespace
            guide_name = guide.split(':')[-1] if ':' in guide else guide
            
            # 构建文件名 - 使用传入的asset_id（已包含序号）
            file_name = f"{collection}_{guide_name}_{asset_id}.abc"
            export_path = os.path.join(export_dir, file_name).replace('\\', '/')
            
            # 构建导出命令，只包含必要的参数
            command = (
                f'AbcExport -j "-frameRange {start_frame} {end_frame} '
                f'-root {guide} -file {export_path} '
                f'-worldSpace -writeVisibility -writeUVSets -uvWrite"'
            )
            
            print(f"执行导出命令: {command}")
            
            # 执行导出
            result = mel.eval(command)
            
            # 验证文件是否真正创建
            if os.path.exists(export_path):
                exported_files.append(export_path)
                print(f"成功导出并验证文件存在: {export_path}")
            else:
                print(f"警告：导出命令执行成功但文件未找到: {export_path}")
                continue
            
        except Exception as e:
            print(f"导出 {guide_name} 失败: {str(e)}")
            continue
    
    return exported_files