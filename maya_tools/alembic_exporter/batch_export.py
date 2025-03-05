import os
import maya.cmds as mc
import maya.mel as mel
from maya_tools.alembic_exporter.core.settings import AlembicExportSettings
from maya_tools.alembic_exporter.core import config as abc_config

def batch_export_chars(project_root=None):
    """批量导出场景中所有角色的Alembic缓存
    
    Args:
        project_root: 项目根目录，如果不提供，将使用配置系统中的设置
    
    Returns:
        导出的文件路径列表
    """
    settings = AlembicExportSettings()
    
    # 使用配置系统中的项目根目录
    if not project_root:
        project_root = abc_config.PROJECT_ROOT
    
    # 如果还没有项目根目录，则使用默认值
    if not project_root:
        project_root = "X:/projects/CSprojectFiles"
    
    print(f"使用项目根目录: {project_root}")
    
    # 查找场景中所有参考文件
    all_refs = mc.file(q=True, reference=True)
    
    # 如果没有参考文件，则返回
    if not all_refs:
        print("场景中没有参考文件")
        return []
    
    # 导出的文件列表
    exported_files = []
    
    # 获取每个参考文件的节点名称
    for ref_file in all_refs:
        ref_nodes = mc.referenceQuery(ref_file, nodes=True)
        
        # 如果没有找到节点，继续下一个
        if not ref_nodes:
            continue
        
        # 过滤出transform节点
        transform_nodes = [node for node in ref_nodes if mc.nodeType(node) == "transform"]
        
        # 如果没有transform节点，继续下一个
        if not transform_nodes:
            continue
        
        # 获取最上层的组节点
        top_groups = []
        for node in transform_nodes:
            if not mc.listRelatives(node, parent=True):
                top_groups.append(node)
        
        # 导出每个顶层组
        for group in top_groups:
            # 导出Alembic缓存
            cache_file = export_group_as_alembic(group, settings)
            if cache_file:
                exported_files.append(cache_file)
    
    return exported_files

def export_group_as_alembic(group, settings=None):
    """将指定的组导出为Alembic缓存
    
    Args:
        group: 要导出的组名
        settings: Alembic导出设置，如果不提供，将创建默认设置
    
    Returns:
        导出的文件路径，如果导出失败则返回None
    """
    if not settings:
        settings = AlembicExportSettings()
    
    # 获取当前帧范围
    start_frame = mc.playbackOptions(q=True, min=True)
    end_frame = mc.playbackOptions(q=True, max=True)
    
    # 获取缓存目录
    cache_dir = os.path.join(mc.workspace(q=True, rootDirectory=True), "alembic")
    
    # 确保缓存目录存在
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # 创建缓存文件路径
    cache_file = os.path.join(cache_dir, f"{group}.abc")
    
    # 构建导出命令
    export_args = [
        f"-frameRange {start_frame} {end_frame}",
        f"-root {group}",
        f"-file {cache_file}",
        "-uvWrite" if settings.uv_write else "",
        "-writeColorSets" if settings.write_color_sets else "",
        "-writeFaceSets" if settings.write_face_sets else "",
        "-worldSpace" if settings.world_space else "",
        "-writeVisibility" if settings.write_visibility else "",
        "-writeCreases" if settings.write_creases else "",
        "-writeUVSets" if settings.write_uv_sets else "",
        "-eulerFilter" if settings.euler_filter else "",
        f"-dataFormat {settings.data_format}",
        "-verbose" if settings.verbose else ""
    ]
    
    # 移除空参数
    export_args = [arg for arg in export_args if arg]
    
    # 执行导出命令
    try:
        export_cmd = f"AbcExport -j \"{' '.join(export_args)}\";"
        mel.eval(export_cmd)
        print(f"成功导出Alembic缓存: {cache_file}")
        return cache_file
    except Exception as e:
        print(f"导出Alembic缓存失败: {str(e)}")
        return None
