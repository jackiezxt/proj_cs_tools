import maya.cmds as cmds
import re


def get_geometry_from_references():
    # 使用字典存储不同角色的 mesh transforms
    character_meshes = {}
    
    # 一次性获取所有 transform 和 mesh
    all_transforms = cmds.ls(type="transform", long=True)
    all_meshes = cmds.ls(type="mesh", long=True, noIntermediate=True)
    pattern = r"^c\d{3}_.*"
    
    # 预先获取所有 mesh 的父级
    mesh_parents = {mesh: cmds.listRelatives(mesh, parent=True, fullPath=True)[0] for mesh in all_meshes}
    
    for node in all_transforms:
        node_name = node.split('|')[-1]
        
        if re.match(pattern, node_name, re.IGNORECASE):
            char_id_match = re.match(r'(c\d{3})_.*', node_name, re.IGNORECASE)
            char_id = char_id_match.group(1).lower()
            
            # 直接使用字符串匹配而不是 ls 命令
            geometry_path = f"{node}|*:Geometry"
            geometry_groups = [t for t in all_transforms if t.startswith(node) and t.endswith("Geometry")]
            
            if geometry_groups:
                if char_id not in character_meshes:
                    character_meshes[char_id] = []
                
                for group in geometry_groups:
                    # 使用字符串匹配找到属于这个组的 mesh
                    group_meshes = [mesh for mesh in all_meshes if mesh.startswith(group)]
                    
                    for mesh in group_meshes:
                        transform = mesh_parents[mesh]
                        if transform not in character_meshes[char_id]:
                            character_meshes[char_id].append(transform)
    
    return character_meshes
