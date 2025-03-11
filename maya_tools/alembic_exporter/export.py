import maya.cmds as cmds
import maya.mel as mel
from maya_tools.alembic_exporter.core.settings import AlembicExportSettings
from maya_tools.alembic_exporter.core.helpers import get_char_geometry_from_references, get_prop_geometry_from_references, get_fur_groups
import os
import json
import re


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
    print(f"Maya文件路径: {normalized_path}")
    print(f"路径部分: {path_parts}")
    
    # 常规路径解析（用于普通的角色和道具导出）
    try:
        project_index = path_parts.index("CSprojectFiles")
        episode = path_parts[project_index + 4]  # PV
        sequence = path_parts[project_index + 5]  # Sq04
        shot = path_parts[project_index + 6]     # Sc0120
        print(f"提取的镜头信息: episode={episode}, sequence={sequence}, shot={shot}")
    except (ValueError, IndexError) as e:
        print(f"路径解析错误: {str(e)}")
        print(f"路径部分: {path_parts}")
        raise RuntimeError("文件路径结构不符合预期，请确保文件在正确的项目结构中")
        
    file_dir = os.path.dirname(current_file)
    cache_dir = os.path.join(file_dir, "abc_cache")
    
    # 创建缓存主目录
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # 尝试从文件名中提取shot信息作为备用
    file_name = os.path.basename(current_file)
    print(f"Maya文件名: {file_name}")
    
    # 为毛发生长面专门解析sequence和shot（可能与上面的不同）
    fur_sequence = sequence  # 默认使用上面解析的sequence
    fur_shot = shot          # 默认使用上面解析的shot
    
    # 从文件名中尝试提取镜头信息（如果文件名包含类似Sq03_Sc0090的格式）
    seq_shot_match = re.search(r'(Sq\d+).*?(Sc\d+)', file_name)
    if seq_shot_match:
        fur_sequence = seq_shot_match.group(1)
        fur_shot = seq_shot_match.group(2)
        print(f"从文件名提取的毛发专用镜头信息: sequence={fur_sequence}, shot={fur_shot}")
    else:
        # 硬编码为Sq03（如果需要）
        fur_sequence = "Sq03"
        print(f"使用硬编码的毛发专用sequence: {fur_sequence}")
    
    # 毛发生长面使用硬编码的正确路径格式，但使用上面解析的sequence和shot变量
    fur_cache_dir = f"X:/projects/CSprojectFiles/Shot/CFX/{fur_sequence}/{fur_shot}/publish/xgen_mesh"
    print(f"毛发生长面导出路径: {fur_cache_dir}")
    
    # 创建目录（如果不存在）
    if not os.path.exists(fur_cache_dir):
        try:
            os.makedirs(fur_cache_dir)
            print(f"成功创建目录: {fur_cache_dir}")
        except Exception as e:
            print(f"创建目录出错: {str(e)}")
        
    return {
        "start_frame": start_frame,
        "end_frame": end_frame,
        "start_export_frame": start_export_frame,
        "end_export_frame": end_export_frame,
        "current_file": current_file,
        "file_dir": file_dir,
        "cache_dir": cache_dir,
        "fur_cache_dir": fur_cache_dir,  # 添加毛发缓存专用目录
        "episode": episode,
        "sequence": sequence,
        "shot": shot,
        "fur_sequence": fur_sequence,  # 毛发专用sequence
        "fur_shot": fur_shot          # 毛发专用shot
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
        # 格式: Sq03_Sc0090_xgenMesh_c001_01.abc
        sequence = scene_info.get("fur_sequence", scene_info["sequence"])  # 优先使用毛发专用sequence
        shot = scene_info.get("fur_shot", scene_info["shot"])              # 优先使用毛发专用shot
        
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
        
        # 构建常规缓存文件路径
        cache_name = f"{scene_info['episode']}_{scene_info['sequence']}_{scene_info['shot']}_{asset_id}.abc"
    
    # 确保目录存在
    if not os.path.exists(asset_cache_dir):
        os.makedirs(asset_cache_dir)
    
    # 构建完整的导出路径
    export_path = os.path.join(asset_cache_dir, cache_name).replace('\\', '/')
    print(f"最终完整导出路径: {export_path}")
    
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


def export_fur_alembic():
    """导出场景中的毛发生长面(Fur_Grp)到Alembic缓存"""
    # 先调试路径问题
    debug_export_path()
    
    return _export_assets("fur", "毛发生长面")


def debug_export_path():
    """调试导出路径和文件名"""
    try:
        # 获取场景信息
        scene_info = _get_scene_info()
        
        # 打印关键信息
        print("\n======== 调试路径信息 ========")
        print(f"常规序列: {scene_info.get('sequence')}")
        print(f"常规镜头: {scene_info.get('shot')}")
        print(f"毛发专用序列: {scene_info.get('fur_sequence')}")
        print(f"毛发专用镜头: {scene_info.get('fur_shot')}")
        
        # 检查毛发缓存路径
        fur_cache_dir = scene_info.get("fur_cache_dir", "未设置")
        print(f"毛发缓存目录: {fur_cache_dir}")
        
        # 模拟一个示例文件名
        example_id = "c001"
        example_index = "01"
        
        # 使用毛发专用sequence和shot
        fur_sequence = scene_info.get("fur_sequence", scene_info["sequence"])
        fur_shot = scene_info.get("fur_shot", scene_info["shot"])
        
        example_filename = f"{fur_sequence}_{fur_shot}_xgenMesh_{example_id}_{example_index}.abc"
        print(f"示例文件名: {example_filename}")
        
        # 完整路径示例
        full_path = os.path.join(fur_cache_dir, example_filename).replace('\\', '/')
        print(f"示例完整路径: {full_path}")
        print("==============================\n")
    except Exception as e:
        print(f"调试路径时出错: {str(e)}")


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