import os
import re

class AssetPathParser:
    def __init__(self, file_path):
        self.file_path = file_path.replace('\\', '/')
        self.project_root = None
        self.asset_type = None
        self.asset_category = None
        self.asset_name = None
        self.pipeline_step = None
        self._parse_path()
        
    def _parse_path(self):
        """解析文件路径"""
        try:
            # 查找项目根目录
            pattern = r"(.*?CSprojectFiles)/([^/]+)/([^/]+)/([^/]+)/([^/]+)/"
            match = re.search(pattern, self.file_path)
            if not match:
                raise ValueError("无效的项目路径结构")
                
            self.project_root = match.group(1)
            self.asset_category = match.group(2)  # Asset
            self.asset_type = match.group(3)      # Chars/Props/Sets
            self.asset_name = match.group(4)      # C003_TongZH
            self.pipeline_step = match.group(5)   # Fur/Rig/Texture etc.
            
        except Exception as e:
            raise ValueError(f"路径解析失败: {str(e)}")
            
    def get_lookdev_path(self):
        """获取 Lookdev 工作目录路径"""
        if not all([self.project_root, self.asset_category, self.asset_type, self.asset_name]):
            raise ValueError("路径信息不完整")
            
        return f"{self.project_root}/{self.asset_category}/{self.asset_type}/{self.asset_name}/Lookdev/work"