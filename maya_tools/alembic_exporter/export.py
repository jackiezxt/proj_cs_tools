import maya.cmds as cmds
import maya.mel as mel
from maya_tools.alembic_exporter.core.settings import AlembicExportSettings
from maya_tools.alembic_exporter.core.helpers import get_char_geometry_from_references, get_prop_geometry_from_references
import os


def _get_scene_info():
    """获取场景信息，包括帧范围、文件路径和项目结构信息"""
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
    try:
        project_index = path_parts.index("CSprojectFiles")
        episode = path_parts[project_index + 4]  # PV
        sequence = path_parts[project_index + 5]  # Sq04
        shot = path_parts[project_index + 6]     # Sc0120
    except (ValueError, IndexError):
        raise RuntimeError("文件路径结构不符合预期，请确保文件在正确的项目结构中")
        
    file_dir = os.path.dirname(current_file)
    cache_dir = os.path.join(file_dir, "abc_cache")
    
    # 创建缓存主目录
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    return {
        "start_frame": start_frame,
        "end_frame": end_frame,
        "start_export_frame": start_export_frame,
        "end_export_frame": end_export_frame,
        "current_file": current_file,
        "file_dir": file_dir,
        "cache_dir": cache_dir,
        "episode": episode,
        "sequence": sequence,
        "shot": shot
    }


def _find_asset_geometry(asset_type="char"):
    """查找场景中指定类型资产的几何体
    
    Args:
        asset_type: 资产类型，"char"表示角色，"prop"表示道具
        
    Returns:
        dict: 资产ID到几何体组的映射
    """
    if asset_type == "char":
        # 使用现有的helper函数获取角色几何体
        return get_char_geometry_from_references()
    
    elif asset_type == "prop":
        # 查找道具几何体
        return get_prop_geometry_from_references()
    
    else:
        raise ValueError(f"不支持的资产类型: {asset_type}")


def _export_abc_file(asset_id, geometry, scene_info, settings, asset_type_name="角色"):
    """导出单个资产的ABC缓存文件
    
    Args:
        asset_id: 资产ID，如 "C001" 或 "P001"
        geometry: 几何体组节点
        scene_info: 场景信息字典
        settings: 导出设置
        asset_type_name: 资产类型名称，用于日志显示
        
    Returns:
        str: 导出的文件路径
    """
    # 创建资产专属缓存目录
    asset_cache_dir = os.path.join(scene_info["cache_dir"], asset_id)
    if not os.path.exists(asset_cache_dir):
        os.makedirs(asset_cache_dir)
    
    # 构建缓存文件路径
    cache_name = f"{scene_info['episode']}_{scene_info['sequence']}_{scene_info['shot']}_{asset_id}.abc"
    export_path = os.path.join(asset_cache_dir, cache_name).replace('\\', '/')
    
    # 构建导出命令
    command = (
        f'AbcExport -j "-frameRange {scene_info["start_export_frame"]} {scene_info["end_export_frame"]} '
        f'-root {geometry} -file {export_path} '
        f'-verbose {settings.verbose} '
        f'-renderableOnly {settings.renderable_only} '
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
        
        if os.path.exists(export_path):
            print(f"成功导出{asset_type_name} {asset_id} 的 Alembic 缓存到: {export_path}")
            return export_path
        else:
            raise RuntimeError(f"导出命令执行成功但未找到输出文件: {export_path}")
            
    except Exception as e:
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