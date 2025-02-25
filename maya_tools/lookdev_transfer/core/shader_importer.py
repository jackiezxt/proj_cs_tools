import maya.cmds as mc
import json
import os
from .path_parser import AssetPathParser


def validate_asset_number(source_name, target_name):
    """验证资产编号是否匹配"""
    def extract_geo_name(name):
        # 处理命名空间
        name = name.split(':')[-1]
        # 处理几何体名称，移除 Geo 后缀
        base_name = name.replace('_Geo', '')
        parts = base_name.split('_')
        # 返回基础名称和方向标识（如果有）
        return parts[0], parts[1] if len(parts) > 1 else ''

    def extract_asset_id(name):
        # 处理命名空间和路径
        parts = name.replace('|', ':').split(':')
        # 检查每个部分
        for part in parts:
            name_parts = part.split('_')
            for np in name_parts:
                if len(np) == 4 and np[0].lower() == 'c' and np[1:].isdigit():
                    return np.lower()
        return None

    # 提取几何体名称（不含命名空间）
    source_base, source_dir = extract_geo_name(source_name)
    target_base, target_dir = extract_geo_name(target_name)

    # 提取资产编号
    source_id = extract_asset_id(source_name)
    target_id = extract_asset_id(target_name)


    # 首先检查几何体基础名称是否匹配
    if source_base != target_base:
        return False

    # 如果有方向标识（U/D/L/R等），检查是否匹配
    if source_dir and target_dir and source_dir != target_dir:
        return False

    # 如果目标物体包含资产编号，则还需要检查资产编号
    if target_id:
        return not source_id or source_id == target_id

    return True


class ShaderImporter:
    def __init__(self, json_path=None):
        self.current_file = mc.file(q=True, sn=True)
        if not self.current_file:
            raise RuntimeError("请先保存场景文件")
            
        self.path_parser = AssetPathParser(self.current_file)
        self.json_path = json_path or os.path.join(
            self.path_parser.get_lookdev_path(),
            f"{self.path_parser.asset_name}_lookdev_info.json"
        )
    def import_shaders(self):
        """导入材质文件"""
        if not os.path.exists(self.json_path):
            raise RuntimeError(f"未找到材质信息文件: {self.json_path}")
            
        # 读取 JSON 文件
        with open(self.json_path, 'r', encoding='utf-8') as f:
            shader_info = json.load(f)
            
        # 导入材质文件
        ma_path = self.json_path.replace('_lookdev_info.json', '_lookdev_shader.ma')
        if not os.path.exists(ma_path):
            raise RuntimeError(f"未找到材质文件: {ma_path}")
            
        # 检查是否已经导入了材质文件
        ref_nodes = mc.ls(type='reference') or []
        for ref in ref_nodes:
            if mc.referenceQuery(ref, filename=True).replace('\\', '/') == ma_path.replace('\\', '/'):
                return shader_info
                
        # 参考材质文件
        mc.file(ma_path, reference=True, namespace="lookdev_shader")
        
        return shader_info

    def apply_shaders(self):
        """应用材质"""
        # 获取选中的物体
        selection = mc.ls(sl=True, long=True) or []
        if not selection:
            raise RuntimeError("请先选择要赋予材质的物体")
            
        # 导入材质信息和文件
        shader_info = self.import_shaders()
        
        # 记录不匹配的物体
        unmatched = []
        
        # 遍历选中的物体
        for obj in selection:
            short_name = obj.split('|')[-1]
            
            # 获取物体的几何信息
            shapes = mc.listRelatives(obj, shapes=True, fullPath=True) or []
            if not shapes:
                unmatched.append(f"{short_name} - 未找到形状节点")
                continue
                
            # 跳过中间物体
            shape = next((s for s in shapes if not mc.getAttr(f"{s}.intermediateObject")), None)
            if not shape:
                continue
                
            # 获取面数
            poly_count = mc.polyEvaluate(shape, face=True)
            
            # 检查资产编号并查找匹配的源模型
            matching_source = None
            match_failed_reason = []
            
            for source_name, source_data in shader_info.items():
                # 检查资产编号
                if not validate_asset_number(source_name, short_name):
                    continue
                    
                # 检查面数是否匹配
                if source_data['poly_count'] == poly_count:
                    matching_source = source_data
                    break
                else:
                    match_failed_reason.append(f"面数不匹配 - 源模型: {source_data['poly_count']}, 目标: {poly_count}")
            
            if not matching_source:
                if match_failed_reason:
                    print(f"\n未能匹配物体: {short_name}")
                    for reason in match_failed_reason:
                        print(f"  {reason}")
                unmatched.append(f"{short_name} - 未找到匹配的源模型（检查资产编号和面数）")
                continue
                
            # 应用材质
            for material in matching_source['materials']:
                shader_name = f"lookdev_shader:{material['name']}"
                if mc.objExists(shader_name):
                    mc.select(obj)
                    mc.hyperShade(assign=shader_name)
                else:
                    print(f"\n材质缺失: {short_name}")
                    print(f"  未找到材质: {shader_name}")
                    unmatched.append(f"{short_name} - 未找到材质 {shader_name}")
                    
        return unmatched