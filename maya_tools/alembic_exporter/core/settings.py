import os
import json

class AlembicExportSettings:
    def __init__(self):
        # 默认设置
        self.verbose = True
        self.renderable_only = True
        self.strip_namespaces = False
        self.write_color_sets = True
        self.write_face_sets = True
        self.world_space = True
        self.write_visibility = True
        self.write_creases = True
        self.write_uv_sets = True
        self.uv_write = True
        self.euler_filter = True
        self.data_format = "ogawa"
        
        # 从JSON文件加载设置
        self._load_settings_from_json()
    
    def _load_settings_from_json(self):
        """从JSON文件加载Alembic导出设置"""
        try:
            # 定位data目录下的alembic_settings.json
            module_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            settings_file = os.path.join(module_dir, "data", "alembic_settings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # 更新对象属性
                for key, value in settings.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                        
                print(f"从配置文件加载Alembic导出设置: {settings_file}")
            else:
                print(f"未找到Alembic设置文件，使用默认值: {settings_file}")
        except Exception as e:
            print(f"加载Alembic设置出错，使用默认值: {str(e)}")
    
    def as_dict(self):
        """返回设置字典"""
        return {
            "verbose": self.verbose,
            "renderable_only": self.renderable_only,
            "strip_namespaces": self.strip_namespaces,
            "write_color_sets": self.write_color_sets,
            "write_face_sets": self.write_face_sets,
            "world_space": self.world_space,
            "write_visibility": self.write_visibility,
            "write_creases": self.write_creases,
            "write_uv_sets": self.write_uv_sets,
            "uv_write": self.uv_write,
            "euler_filter": self.euler_filter,
            "data_format": self.data_format
        }
    
    def save_settings(self):
        """将当前设置保存到JSON文件"""
        try:
            module_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            settings_file = os.path.join(module_dir, "data", "alembic_settings.json")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            with open(settings_file, 'w') as f:
                json.dump(self.as_dict(), f, indent=4)
                
            print(f"保存Alembic设置到: {settings_file}")
            return True
        except Exception as e:
            print(f"保存Alembic设置失败: {str(e)}")
            return False
