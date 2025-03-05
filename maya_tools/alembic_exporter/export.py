import maya.cmds as cmds
import maya.mel as mel
from maya_tools.alembic_exporter.core.settings import AlembicExportSettings
from maya_tools.alembic_exporter.core.helpers import get_char_geometry_from_references, get_prop_geometry_from_references
from maya_tools.alembic_exporter.core import config as abc_config
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
    
    # 尝试使用新的配置系统获取项目结构信息
    try:
        # 使用项目根目录和路径模板
        project_root = abc_config.PROJECT_ROOT
        path_templates = abc_config.PATH_TEMPLATES
        
        # 解析路径信息
        normalized_path = current_file.replace('\\', '/').replace('//', '/')
        path_parts = normalized_path.split('/')
        
        # 尝试从文件路径提取信息
        try:
            if project_root:
                # 使用项目根目录
                project_root_normalized = project_root.replace('\\', '/').replace('//', '/')
                if project_root_normalized in normalized_path:
                    relative_path = normalized_path.split(project_root_normalized)[1].strip('/')
                    path_segments = relative_path.split('/')
                    
                    # 假设路径结构为 Shot/Animation/episode/sequence/shot/...
                    # 根据实际情况可能需要调整索引
                    if len(path_segments) >= 5 and "Animation" in path_segments:
                        anim_index = path_segments.index("Animation")
                        episode = path_segments[anim_index + 1]  # 例如 PV
                        sequence = path_segments[anim_index + 2]  # 例如 Sq04
                        shot = path_segments[anim_index + 3]      # 例如 Sc0120
                    else:
                        raise ValueError("无法从路径解析出镜头结构")
                else:
                    raise ValueError("当前文件不在项目根目录下")
            else:
                # 回退到旧的解析方式
                raise ValueError("项目根目录未设置")
                
        except (ValueError, IndexError) as e:
            print(f"使用新配置方式提取路径信息失败: {str(e)}，尝试旧方法")
            # 回退到旧的解析方式
            try:
                project_index = path_parts.index("CSprojectFiles")
                episode = path_parts[project_index + 4]  # PV
                sequence = path_parts[project_index + 5]  # Sq04
                shot = path_parts[project_index + 6]     # Sc0120
            except (ValueError, IndexError):
                raise RuntimeError("文件路径结构不符合预期，请确保文件在正确的项目结构中")
        
        # 使用配置中的路径模板创建缓存目录
        file_dir = os.path.dirname(current_file)
        
        # 尝试使用配置的abc_cache路径模板
        if "abc_cache" in path_templates:
            template = path_templates["abc_cache"]
            cache_dir = template.format(
                project_root=project_root,
                episode=episode,
                sequence=sequence,
                shot=shot
            )
            # 确保路径存在
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
        else:
            # 回退到旧的方式 - 在文件目录下创建abc_cache文件夹
            cache_dir = os.path.join(file_dir, "abc_cache")
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
    
    except Exception as e:
        print(f"使用配置系统处理路径时出错: {str(e)}，使用默认方法")
        # 回退到原始方法
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
    """导出单个资产的Alembic缓存
    
    Args:
        asset_id: 资产ID
        geometry: 要导出的几何体列表
        scene_info: 场景信息字典
        settings: Alembic导出设置
        asset_type_name: 资产类型名称（用于文件命名）
        
    Returns:
        导出的缓存文件路径
    """
    # 如果没有几何体，则返回None
    if not geometry:
        print(f"没有找到{asset_type_name}几何体可导出")
        return None
    
    # 确定资产类型
    asset_type = None
    for type_code, type_name in abc_config.ASSET_TYPES.items():
        if type_name == asset_type_name:
            asset_type = type_code
            break
    
    if not asset_type:
        # 如果找不到匹配的资产类型，使用默认值
        asset_type = "char" if asset_type_name == "角色" else "prop"
    
    # 尝试使用配置的资产路径
    try:
        if "asset_abc" in abc_config.PATH_TEMPLATES:
            # 使用配置的资产路径模板
            asset_cache_dir = abc_config.PATH_TEMPLATES["asset_abc"].format(
                project_root=abc_config.PROJECT_ROOT,
                asset_type=asset_type,
                asset_id=asset_id
            )
            
            # 确保目录存在
            if not os.path.exists(asset_cache_dir):
                os.makedirs(asset_cache_dir)
                print(f"创建资产缓存目录: {asset_cache_dir}")
                
            # 构建缓存文件路径
            cache_file = os.path.join(asset_cache_dir, f"{asset_id}.abc")
        else:
            # 回退到镜头级别的缓存目录
            cache_file = os.path.join(scene_info["cache_dir"], f"{asset_id}.abc")
    except Exception as e:
        print(f"使用资产路径模板时出错: {str(e)}，使用默认路径")
        # 回退到默认路径
        cache_file = os.path.join(scene_info["cache_dir"], f"{asset_id}.abc")
    
    # 构建导出命令参数
    j_flag = " -writeColorSets" if settings.write_color_sets else ""
    j_flag += " -writeFaceSets" if settings.write_face_sets else ""
    j_flag += " -wholeFrameGeo" if settings.world_space else ""
    j_flag += " -writeVisibility" if settings.write_visibility else ""
    j_flag += " -writeCreases" if settings.write_creases else ""
    j_flag += " -writeUVSets" if settings.write_uv_sets else ""
    j_flag += " -uvWrite" if settings.uv_write else ""
    j_flag += " -eulerFilter" if settings.euler_filter else ""
    j_flag += " -worldSpace" if settings.world_space else ""
    j_flag += " -dataFormat " + settings.data_format
    
    # 使用场景帧范围
    frame_range = f"{scene_info['start_export_frame']} {scene_info['end_export_frame']}"
    j_flag = f" -frameRange {frame_range}{j_flag}"
    
    # 添加要导出的对象
    roots = ""
    for geo in geometry:
        roots += f" -root {geo}"
    
    # 完整的导出命令
    cmd = f"AbcExport -verbose{' -v' if settings.verbose else ''} -j \"{j_flag}{roots} -file {cache_file}\";"
    print(f"执行命令: {cmd}")
    
    # 导出Alembic缓存
    try:
        mel.eval(cmd)
        print(f"成功导出{asset_type_name}缓存: {cache_file}")
        return cache_file
    except Exception as e:
        print(f"导出{asset_type_name}缓存失败: {str(e)}")
        return None


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