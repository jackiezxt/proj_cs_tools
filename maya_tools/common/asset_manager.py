import os
import json
import maya.cmds as mc
from .path_manager import PathManager

class AssetManager:
    """资产管理类，处理角色和道具等资产的共用逻辑"""
    
    def __init__(self, shot_data_path=None):
        self.path_manager = PathManager()
        self.shot_data = self._load_shot_data(shot_data_path)
        self.current_episode = None
        self.current_sequence = None
        self.current_shot = None
        
    def _load_shot_data(self, data_file=None):
        """加载镜头数据"""
        if not data_file:
            module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_file = os.path.join(module_dir, "data", "shot_data.json")
            
        try:
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"anm_path": self.path_manager.anm_path, "Episode": {}}
        except Exception as e:
            print(f"加载镜头数据时出错: {str(e)}")
            return {"anm_path": self.path_manager.anm_path, "Episode": {}}
    
    def get_shot_assets(self, episode, sequence, shot_id):
        """获取指定镜头的所有资产"""
        self.current_episode = episode
        self.current_sequence = sequence
        self.current_shot = shot_id
        
        shot_data = self.shot_data.get("Episode", {}).get(episode, {}).get("Sequences", {}).get(sequence, {}).get("Shots", {}).get(shot_id, {})
        
        return {
            "Chars": shot_data.get("Chars", []),
            "Props": shot_data.get("Props", []),
            "Environment": shot_data.get("Environment", "")
        }
    
    def is_character(self, asset_id):
        """判断是否为角色资产"""
        return asset_id.lower().startswith('c')
    
    def is_prop(self, asset_id):
        """判断是否为道具资产"""
        return asset_id.lower().startswith('p')
    
    def get_asset_type(self, asset_id):
        """根据ID获取资产类型"""
        if self.is_character(asset_id):
            return "Chars"
        elif self.is_prop(asset_id):
            return "Props"
        else:
            return "Unknown"
    
    def find_geometry_by_pattern(self, pattern_prefix):
        """根据前缀模式查找几何体"""
        import re
        asset_meshes = {}
        
        # 获取所有 transform 节点
        all_transforms = mc.ls(type="transform", long=True)
        
        # 正则表达式模式
        pattern = rf"{pattern_prefix.lower()}(\d+)"
        
        for node in all_transforms:
            # 获取节点的短名称
            short_name = node.split('|')[-1].lower()
            
            # 查找匹配的节点
            match = re.search(pattern, short_name)
            if match:
                asset_id = f"{pattern_prefix.upper()}{match.group(1)}"
                
                # 判断是否有子几何体
                shapes = mc.listRelatives(node, shapes=True, fullPath=True)
                if shapes:
                    asset_meshes[asset_id] = node
        
        return asset_meshes
    
    def get_char_geometry(self):
        """获取场景中所有角色几何体"""
        return self.find_geometry_by_pattern('c')
    
    def get_prop_geometry(self):
        """获取场景中所有道具几何体"""
        return self.find_geometry_by_pattern('p') 