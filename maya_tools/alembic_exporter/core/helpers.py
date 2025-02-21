import maya.cmds as cmds
import re


def get_geometry_from_references():
    # 使用字典存储不同角色的信息
    character_meshes = {}
    
    # 获取所有 transform 节点
    all_transforms = cmds.ls(type="transform", long=True)
    pattern = r"^c\d{3}_.*"
    
    for node in all_transforms:
        node_name = node.split('|')[-1]
        
        if re.match(pattern, node_name, re.IGNORECASE):
            char_id_match = re.match(r'(c\d{3})_.*', node_name, re.IGNORECASE)
            char_id = char_id_match.group(1).lower()
            
            # 检查是否存在 Geometry 组
            geometry_path = f"{node}|*:Geometry"
            geometry_groups = cmds.ls(geometry_path, long=True)
            
            if geometry_groups:
                # 确保字典中有这个角色的条目
                if char_id not in character_meshes:
                    character_meshes[char_id] = []
                
                # 只添加 Geometry 组本身，不需要单独添加内部的 mesh
                for geo_group in geometry_groups:
                    if geo_group not in character_meshes[char_id]:
                        character_meshes[char_id].append(geo_group)
    
    return character_meshes
