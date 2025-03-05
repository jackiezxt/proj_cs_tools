import os
import json

class PathManager:
    """项目路径管理类，处理所有工具包共用的路径逻辑"""
    
    def __init__(self, project_config_path=None):
        # 加载配置文件
        self.config = self._load_config(project_config_path)
        self.project_root = self.config.get("project_root", "")
        self.anm_path = self.config.get("anm_path", "")
        
    def _load_config(self, config_path=None):
        """加载配置文件"""
        # 如果未指定，使用默认配置路径
        if not config_path:
            module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(module_dir, "data", "project_config.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._create_default_config(config_path)
        except Exception as e:
            print(f"加载配置文件时出错: {str(e)}")
            return {}
    
    def _create_default_config(self, config_path):
        """创建默认配置文件"""
        default_config = {
            "project_root": "X:/projects/CSprojectFiles",
            "anm_path": "X:/projects/CSprojectFiles/Shot/Animation",
            "path_templates": {
                "abc_cache": "{project_root}/Shot/Animation/{episode}/{sequence}/{shot}/work/abc_cache",
                "lighting_work": "{project_root}/Shot/Lighting/{episode}/{sequence}/{shot}/work",
                "lookdev_path": "{project_root}/Asset/{asset_type}/{asset_id}/publish/lookdev"
            }
        }
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 写入默认配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            return default_config
        except Exception as e:
            print(f"创建默认配置文件时出错: {str(e)}")
            return default_config
    
    def get_abc_cache_path(self, episode, sequence, shot, asset_id=None):
        """获取Alembic缓存路径"""
        template = self.config.get("path_templates", {}).get("abc_cache", "")
        if not template:
            return os.path.join(self.anm_path, episode, sequence, shot, "work", "abc_cache")
        
        path = template.format(
            project_root=self.project_root,
            episode=episode,
            sequence=sequence,
            shot=shot
        )
        
        if asset_id:
            return os.path.join(path, asset_id)
        return path
    
    def get_lookdev_path(self, asset_id, asset_type):
        """获取LookDev文件路径"""
        # 查找资产目录
        template = self.config.get("path_templates", {}).get("lookdev_path", "")
        if not template:
            return os.path.join(self.project_root, "Asset", asset_type, asset_id, "publish", "lookdev")
        
        return template.format(
            project_root=self.project_root,
            asset_type=asset_type,
            asset_id=asset_id
        )
    
    def ensure_directory_exists(self, path):
        """确保目录存在，如果不存在则创建"""
        if not os.path.exists(path):
            os.makedirs(path)
            return True
        return False
        
    def get_lighting_work_path(self, episode, sequence, shot):
        """获取Lighting工作目录"""
        template = self.config.get("path_templates", {}).get("lighting_work", "")
        if not template:
            return os.path.join(self.project_root, "Shot", "Lighting", episode, sequence, shot, "work")
        
        return template.format(
            project_root=self.project_root,
            episode=episode,
            sequence=sequence,
            shot=shot
        ) 