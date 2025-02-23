import maya.cmds as mc
import json
import os
from typing import Dict, List, Tuple

class GeometryChecker:
    def __init__(self):
        self.temp_dir = "d:/temp"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
    def get_current_file_prefix(self) -> str:
        """获取当前文件名的前四个字符"""
        current_file = mc.file(q=True, sn=True)
        if not current_file:
            raise RuntimeError("请先保存文件")
        return os.path.basename(current_file)[:4]
        
    def get_geometry_info(self) -> Dict:
        """获取场景中所有 Geometry 组的信息"""
        # 查找所有 Geometry 组
        all_geo_groups = mc.ls("Geometry", type="transform", long=True)
        if not all_geo_groups:
            raise RuntimeError("未找到任何 Geometry 组")
            
        result = {}
        for geo_group in all_geo_groups:
            group_info = {
                "path": geo_group,
                "meshes": []
            }
            
            # 获取组下所有的 mesh
            meshes = mc.listRelatives(geo_group, allDescendents=True, type="mesh", fullPath=True) or []
            for mesh in meshes:
                # 检查是否是中间物体
                if mc.getAttr(f"{mesh}.intermediateObject"):
                    continue
                    
                # 获取变换节点
                transform = mc.listRelatives(mesh, parent=True, fullPath=True)[0]
                
                # 获取顶点数
                vert_count = mc.polyEvaluate(mesh, vertex=True)
                
                mesh_info = {
                    "name": transform.split("|")[-1],
                    "full_path": transform,
                    "vertex_count": vert_count
                }
                group_info["meshes"].append(mesh_info)
                
            result[geo_group] = group_info
            
        return result
        
    def save_check_result(self, data: Dict):
        """保存检查结果到json文件"""
        file_prefix = self.get_current_file_prefix()
        json_path = os.path.join(self.temp_dir, f"{file_prefix}.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return json_path
        
    def compare_with_previous(self, current_data: Dict, previous_file_prefix: str) -> List[str]:
        """与之前的检查结果进行对比"""
        previous_json = os.path.join(self.temp_dir, f"{previous_file_prefix}.json")
        if not os.path.exists(previous_json):
            raise RuntimeError(f"未找到对比文件: {previous_json}")
            
        with open(previous_json, 'r', encoding='utf-8') as f:
            previous_data = json.load(f)
            
        differences = []
        
        # 比较 Geometry 组的数量
        if len(current_data) != len(previous_data):
            differences.append(f"Geometry组数量不同: 当前{len(current_data)}个, 之前{len(previous_data)}个")
            
        # 对比每个组的内容
        for group_path, group_info in current_data.items():
            if group_path not in previous_data:
                differences.append(f"新增Geometry组: {group_path}")
                differences.append("包含以下模型:")
                for mesh in group_info["meshes"]:
                    differences.append(f"  - {mesh['name']} (顶点数: {mesh['vertex_count']})")
                continue
                
            prev_group = previous_data[group_path]
            
            # 比较模型数量
            if len(group_info["meshes"]) != len(prev_group["meshes"]):
                differences.append(f"组 {group_path} 的模型数量不同:")
                current_names = {m["name"] for m in group_info["meshes"]}
                previous_names = {m["name"] for m in prev_group["meshes"]}
                
                # 显示新增的模型
                added_models = current_names - previous_names
                if added_models:
                    differences.append("新增的模型:")
                    for name in added_models:
                        mesh = next(m for m in group_info["meshes"] if m["name"] == name)
                        differences.append(f"  + {name} (顶点数: {mesh['vertex_count']})")
                
                # 显示删除的模型
                removed_models = previous_names - current_names
                if removed_models:
                    differences.append("删除的模型:")
                    for name in removed_models:
                        mesh = next(m for m in prev_group["meshes"] if m["name"] == name)
                        differences.append(f"  - {name} (顶点数: {mesh['vertex_count']})")
                continue
                
            # 比较每个模型
            current_meshes = {m["name"]: m for m in group_info["meshes"]}
            previous_meshes = {m["name"]: m for m in prev_group["meshes"]}
            
            for mesh_name, mesh_info in current_meshes.items():
                if mesh_name not in previous_meshes:
                    differences.append(f"新增模型: {mesh_name} (顶点数: {mesh_info['vertex_count']})")
                    continue
                    
                prev_mesh = previous_meshes[mesh_name]
                if mesh_info["vertex_count"] != prev_mesh["vertex_count"]:
                    differences.append(
                        f"模型 {mesh_name} 的顶点数变化: "
                        f"{prev_mesh['vertex_count']} -> {mesh_info['vertex_count']}"
                    )
                    
        return differences