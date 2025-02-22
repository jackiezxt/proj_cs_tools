import maya.cmds as cmds
import maya.mel as mel
from maya_tools.alembic_exporter.core.settings import AlembicExportSettings
from maya_tools.alembic_exporter.core.helpers import get_geometry_from_references
import os


def export_alembic():
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
    # 统一路径分隔符并分割
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
    
    # 获取所有角色的 mesh transforms
    character_meshes = get_geometry_from_references()
    
    # 获取导出设置
    settings = AlembicExportSettings()
    
    # 统计每个角色ID出现的次数
    char_count = {}
    for char_id in character_meshes.keys():
        base_id = char_id[:4]  # 获取基础角色ID (c001)
        char_count[base_id] = char_count.get(base_id, 0) + 1
    
    # 为每个角色创建单独的缓存
    processed_chars = {}
    for char_id, geometry_groups in character_meshes.items():
        if not geometry_groups:
            print(f"警告：未找到角色 {char_id} 的 Geometry 组")
            continue

        for index, geometry in enumerate(geometry_groups, 1):
            base_id = char_id
            suffix = f"_{index:02d}"
                
            # 创建角色专属缓存目录
            char_cache_dir = os.path.join(cache_dir, base_id)
            if not os.path.exists(char_cache_dir):
                os.makedirs(char_cache_dir)
                
            # 构建缓存文件路径
            cache_name = f"{episode}_{sequence}_{shot}_{base_id}{suffix}.abc"
            char_export_path = os.path.join(char_cache_dir, cache_name).replace('\\', '/')
            
            # 构建导出命令，使用 Geometry 组作为根节点
            roots = " ".join(f"-root {geo}" for geo in geometry_groups)
            command = (
                f'AbcExport -j "-frameRange {start_export_frame} {end_export_frame} '
                
                f'-root {geometry} -file {char_export_path} '
                f'-verbose {settings.verbose} '
                f'-renderableOnly {settings.renderable_only} '
                f'-writeColorSets {settings.write_color_sets} '
                f'-writeFaceSets {settings.write_face_sets} '
                f'-worldSpace {settings.world_space} '
                f'-writeVisibility {settings.write_visibility} '
                f'-writeCreases {settings.write_creases} '
                f'-writeUVSets {settings.write_uv_sets}'
                f'-uvWrite {settings.write_uv_sets} '
                f'-eulerFilter {settings.euler_filter} '
                f'-dataFormat {settings.data_format} "'

            )
            
            try:
                print(f"正在导出 {char_id} 的 Alembic 缓存...")
                print(f"导出命令: {command}")
                result = mel.eval(command)
                
                if os.path.exists(char_export_path):
                    print(f"成功导出 {char_id} 的 Alembic 缓存到: {char_export_path}")
                else:
                    raise RuntimeError(f"导出命令执行成功但未找到输出文件: {char_export_path}")
                    
            except Exception as e:
                raise RuntimeError(f"导出 {char_id} 的 Alembic 缓存时发生错误: {str(e)}")
