import os
import json
import maya.cmds as mc

class ConfigManager:
    """配置和数据管理类，处理所有工具包的配置文件"""
    
    def __init__(self, config_dir=None):
        # 如果未指定配置目录，使用默认目录
        if not config_dir:
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        else:
            self.config_dir = config_dir
            
        # 确保目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # 常用配置文件路径
        self.project_config_path = os.path.join(self.config_dir, "project_config.json")
        self.shot_data_path = os.path.join(self.config_dir, "shot_data.json")
        self.alembic_settings_path = os.path.join(self.config_dir, "alembic_settings.json")
        self.render_settings_path = os.path.join(self.config_dir, "render_settings.json")
        
        # 加载配置
        self.project_config = self._load_or_create_config(self.project_config_path, self._get_default_project_config())
        self.shot_data = self._load_or_create_config(self.shot_data_path, self._get_default_shot_data())
        self.alembic_settings = self._load_or_create_config(self.alembic_settings_path, self._get_default_alembic_settings())
        self.render_settings = self._load_or_create_config(self.render_settings_path, self._get_default_render_settings())
    
    def _load_or_create_config(self, file_path, default_config):
        """加载配置文件，如果不存在则创建默认配置"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建默认配置文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                return default_config
        except Exception as e:
            mc.warning(f"加载配置文件时出错: {str(e)}")
            return default_config
    
    def _get_default_project_config(self):
        """获取默认项目配置"""
        return {
            "project_root": "X:/projects/CSprojectFiles",
            "anm_path": "X:/projects/CSprojectFiles/Shot/Animation",
            "path_templates": {
                "abc_cache": "{project_root}/Shot/Animation/{episode}/{sequence}/{shot}/work/abc_cache",
                "lighting_work": "{project_root}/Shot/Lighting/{episode}/{sequence}/{shot}/work",
                "lookdev_path": "{project_root}/Asset/{asset_type}/{asset_id}/publish/lookdev"
            }
        }
    
    def _get_default_shot_data(self):
        """获取默认镜头数据"""
        return {
            "anm_path": "X:/projects/CSprojectFiles/Shot/Animation",
            "Episode": {
                "PV": {
                    "Sequences": {
                        "Sq01": {
                            "Shots": {
                                "sc0010": { "Chars": ["C001"], "Props": [], "Environment": "" }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_default_alembic_settings(self):
        """获取默认Alembic导出设置"""
        return {
            "verbose": True,
            "renderable_only": True,
            "strip_namespaces": False,
            "write_color_sets": True,
            "write_face_sets": True,
            "world_space": True,
            "write_visibility": True,
            "write_creases": True,
            "write_uv_sets": True,
            "uv_write": True,
            "euler_filter": True,
            "data_format": "ogawa"
        }
    
    def _get_default_render_settings(self):
        """获取默认渲染设置"""
        return {
            "arnold": {
                "AASamples": 3,
                "GIDiffuseSamples": 2,
                "GISpecularSamples": 2,
                "mergeAOVs": 1,
                "ai_translator": "exr"
            },
            "globals": {
                "outFormatControl": 0,
                "animation": 1,
                "putFrameBeforeExt": 1,
                "periodInExt": 1,
                "extensionPadding": 4
            },
            "frame_rate": "pal"
        }
    
    def save_config(self, config_type, data=None):
        """保存配置到文件"""
        config_map = {
            "project": (self.project_config_path, self.project_config),
            "shot_data": (self.shot_data_path, self.shot_data),
            "alembic": (self.alembic_settings_path, self.alembic_settings),
            "render": (self.render_settings_path, self.render_settings)
        }
        
        if config_type not in config_map:
            raise ValueError(f"未知的配置类型: {config_type}")
            
        file_path, current_data = config_map[config_type]
        
        # 如果提供了新数据，更新当前数据
        if data:
            if config_type == "project":
                self.project_config = data
            elif config_type == "shot_data":
                self.shot_data = data
            elif config_type == "alembic":
                self.alembic_settings = data
            elif config_type == "render":
                self.render_settings = data
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            # 使用当前数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False) 