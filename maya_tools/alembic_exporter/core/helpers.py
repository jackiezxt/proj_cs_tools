import maya.cmds as cmds
import re
from maya_tools.common.asset_manager import AssetManager

def _get_geometry_by_pattern(pattern_prefix, id_group=1):
    """
    通用函数，根据指定的前缀模式查找几何体
    
    Args:
        pattern_prefix: 模式前缀，如 "c" 表示角色，"p" 表示道具
        id_group: 正则表达式中ID的分组索引
        
    Returns:
        dict: 资产ID到几何体组的映射
    """
    asset_meshes = {}
    
    # 获取所有 transform 节点
    all_transforms = cmds.ls(type="transform", long=True)
    pattern = f"^{pattern_prefix}\\d{{3}}_.*"
    
    for node in all_transforms:
        node_name = node.split('|')[-1]
        
        if re.match(pattern, node_name, re.IGNORECASE):
            asset_id_match = re.match(f'({pattern_prefix}\\d{{3}})_.*', node_name, re.IGNORECASE)
            asset_id = asset_id_match.group(id_group).lower()
            
            # 检查是否存在 Geometry 组
            geometry_path = f"{node}|*:Geometry"
            geometry_groups = cmds.ls(geometry_path, long=True)
            
            if geometry_groups:
                # 确保字典中有这个资产的条目
                if asset_id not in asset_meshes:
                    asset_meshes[asset_id] = []
                
                # 只添加几何体组本身，不需要单独添加内部的 mesh
                for geo_group in geometry_groups:
                    if geo_group not in asset_meshes[asset_id]:
                        asset_meshes[asset_id].append(geo_group)
    
    return asset_meshes

def get_char_geometry_from_references():
    """获取场景中的角色几何体"""
    asset_manager = AssetManager()
    return asset_manager.get_char_geometry()

def get_prop_geometry_from_references():
    """获取场景中的道具几何体"""
    asset_manager = AssetManager()
    return asset_manager.get_prop_geometry()

def get_all_asset_geometry():
    """
    获取场景中所有资产(角色和道具)的几何体
    
    Returns:
        dict: 包含角色和道具的几何体信息的字典
    """
    # 获取角色和道具的几何体
    character_meshes = get_char_geometry_from_references()
    prop_meshes = get_prop_geometry_from_references()
    
    # 合并结果
    all_assets = {}
    all_assets.update(character_meshes)
    all_assets.update(prop_meshes)
    
    return all_assets