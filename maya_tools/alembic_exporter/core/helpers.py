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

def get_fur_groups():
    """
    获取场景中所有毛发生长面Fur_Grp组
    
    Returns:
        dict: 角色ID到Fur_Grp节点的映射
    """
    fur_groups = {}
    
    # 查找所有名称包含Fur_Grp的transform节点 - 使用多种大小写变体
    search_patterns = [
        "*:*Fur_Grp*", "*Fur_Grp*",           # 标准格式
        "*:*FUR_GRP*", "*FUR_GRP*",           # 全大写格式
        "*:*fur_grp*", "*fur_grp*",           # 全小写格式
        "*:*Fur_grp*", "*Fur_grp*",           # 混合格式1
        "*:*fur_Grp*", "*fur_Grp*",           # 混合格式2
        "*:*fur*grp*", "*fur*grp*"            # 变种格式（中间可能有其他字符）
    ]
    
    # 查找所有可能的毛发组
    all_fur_groups = []
    for pattern in search_patterns:
        found_groups = cmds.ls(pattern, type="transform", long=True)
        if found_groups:
            all_fur_groups.extend(found_groups)
    
    # 去重
    all_fur_groups = list(set(all_fur_groups))
    
    print(f"找到 {len(all_fur_groups)} 个可能的Fur_Grp节点")
    if len(all_fur_groups) > 0:
        print(f"第一个找到的节点: {all_fur_groups[0]}")
    
    for fur_group in all_fur_groups:
        # 提取节点名称（不包含路径）
        node_name = fur_group.split('|')[-1]
        print(f"处理节点: {node_name}")
        
        # 尝试匹配角色ID (c001, C001等格式) - 支持命名空间
        # 先检查完整名称
        asset_id_match = re.search(r'[cC](\d{3})', node_name)
        
        # 如果没找到，尝试分割命名空间后再匹配
        if not asset_id_match and ':' in node_name:
            namespace = node_name.split(':')[0]
            print(f"从命名空间获取角色ID: {namespace}")
            asset_id_match = re.search(r'[cC](\d{3})', namespace)
        
        if asset_id_match:
            # 标准化资产ID格式 (c001)
            asset_id = f"c{asset_id_match.group(1)}"
            print(f"匹配到角色ID: {asset_id}")
            
            # 确保字典中有这个资产的条目
            if asset_id not in fur_groups:
                fur_groups[asset_id] = []
            
            # 添加到相应资产的列表中
            fur_groups[asset_id].append(fur_group)
        else:
            print(f"未能从节点 {node_name} 中提取角色ID")
            # 如果没有明确的角色ID，将其放在"unknown"类别中
            if "unknown" not in fur_groups:
                fur_groups["unknown"] = []
            fur_groups["unknown"].append(fur_group)
    
    # 打印找到的组信息
    if fur_groups:
        print("\n找到的毛发生长面组:")
        for asset_id, groups in fur_groups.items():
            print(f"- 角色 {asset_id}: {len(groups)} 个组")
            for group in groups:
                print(f"  - {group}")
    else:
        print("未找到任何毛发生长面Fur_Grp组")
    
    # 如果有未归类的Fur_Grp，打印警告
    if "unknown" in fur_groups and fur_groups["unknown"]:
        print(f"警告: 找到{len(fur_groups['unknown'])}个未能识别角色ID的Fur_Grp节点")
    
    return fur_groups