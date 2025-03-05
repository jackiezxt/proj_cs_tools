import os
import json
import maya.cmds as mc

class ConfigManager:
    """配置和数据管理类，处理所有工具包的配置文件"""
    
    def __init__(self, config_dir=None, project_config_path=None):
        # 如果未指定配置目录，使用默认目录
        if not config_dir:
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        else:
            self.config_dir = config_dir
            
        # 确保目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 设置项目配置路径
        self.project_config_path = project_config_path
        
        # 如果未指定项目配置路径，使用默认路径
        if not self.project_config_path:
            self.project_config_path = os.path.join(self.config_dir, "project_config.json")
            
            # 检查环境变量中是否指定了项目配置路径
            env_project_config = os.environ.get("CS_PROJECT_CONFIG_PATH")
            if env_project_config and os.path.exists(env_project_config):
                self.project_config_path = env_project_config
                print(f"从环境变量加载项目配置: {self.project_config_path}")
            
        # 基于项目配置路径所在的目录确定其他配置文件的位置
        config_base_dir = os.path.dirname(self.project_config_path)
        
        # 设置资产配置路径
        self.asset_config_path = os.path.join(config_base_dir, "asset_config.json")
        env_asset_config = os.environ.get("CS_ASSET_CONFIG_PATH")
        if env_asset_config and os.path.exists(env_asset_config):
            self.asset_config_path = env_asset_config
            
        # 设置镜头配置路径
        self.shot_config_path = os.path.join(config_base_dir, "shot_config.json")
        env_shot_config = os.environ.get("CS_SHOT_CONFIG_PATH")
        if env_shot_config and os.path.exists(env_shot_config):
            self.shot_config_path = env_shot_config
            
        # 设置渲染设置路径
        self.render_settings_path = os.path.join(config_base_dir, "render_settings.json")
        env_render_settings = os.environ.get("CS_RENDER_SETTINGS_PATH")
        if env_render_settings and os.path.exists(env_render_settings):
            self.render_settings_path = env_render_settings
        
        # 尝试加载alembic设置
        self.alembic_settings_path = os.path.join(config_base_dir, "alembic_settings.json")
        env_alembic_settings = os.environ.get("CS_ALEMBIC_SETTINGS_PATH")
        if env_alembic_settings and os.path.exists(env_alembic_settings):
            self.alembic_settings_path = env_alembic_settings
            
        # 加载配置
        self.project_config = self._load_or_create_config(self.project_config_path, self._get_default_project_config())
        self.asset_config = self._load_or_create_config(self.asset_config_path, self._get_default_asset_config())
        self.shot_config = self._load_or_create_config(self.shot_config_path, self._get_default_shot_config())
        self.render_settings = self._load_or_create_config(self.render_settings_path, self._get_default_render_settings())
        self.alembic_settings = self._load_or_create_config(self.alembic_settings_path, self._get_default_alembic_settings())
        
        # 打印加载的配置文件路径
        print("配置管理器初始化完成:")
        print(f"- 项目配置: {self.project_config_path}")
        print(f"- 资产配置: {self.asset_config_path}")
        print(f"- 镜头配置: {self.shot_config_path}")
        print(f"- 渲染设置: {self.render_settings_path}")
        print(f"- Alembic设置: {self.alembic_settings_path}")
        
        # 合并项目配置中的路径到渲染设置
        self._merge_project_paths_to_render_settings()
        
        # 其他配置
        self.shot_data_path = os.path.join(self.config_dir, "shot_data.json")
        self.shot_data = self._load_or_create_config(self.shot_data_path, self._get_default_shot_data())
        
        print(f"配置管理器初始化成功")
        
    def _merge_project_paths_to_render_settings(self):
        """
        将项目配置中的路径合并到渲染设置中，以便在渲染时使用项目特定的路径
        """
        render_settings = self.render_settings.get("render_settings", {})
        
        # 获取项目根目录
        project_root = self.project_config.get("project_root", "")
        
        # 更新输出目录
        if "output_directories" in self.shot_config:
            output_dirs = self.shot_config["output_directories"]
            if "render_settings" not in self.render_settings:
                self.render_settings["render_settings"] = {}
            
            # 将项目配置中的输出目录合并到渲染设置中
            if "output_directories" not in render_settings:
                render_settings["output_directories"] = {}
            
            for key, path in output_dirs.items():
                # 替换路径中的项目根目录变量
                if project_root and "{project_root}" in path:
                    path = path.replace("{project_root}", project_root)
                render_settings["output_directories"][key] = path
        
        # 添加项目配置中的分辨率、帧率和色彩空间设置
        if "resolution" in self.project_config:
            render_settings["resolution"] = self.project_config["resolution"]
            
        if "frame_rate" in self.project_config:
            render_settings["frame_rate"] = self.project_config["frame_rate"]
            
        if "color_space" in self.project_config:
            render_settings["color_space"] = self.project_config["color_space"]
        
        return render_settings
        
    def _load_or_create_config(self, file_path, default_config):
        """加载配置文件，如果不存在则创建默认配置
        
        Args:
            file_path: 配置文件路径
            default_config: 默认配置
            
        Returns:
            配置字典
        """
        config = default_config.copy()
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    loaded_config = json.load(f)
                    config.update(loaded_config)
                print(f"已加载配置文件: {file_path}")
            else:
                with open(file_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                print(f"已创建默认配置文件: {file_path}")
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
        
        return config
        
    def _get_default_project_config(self):
        """获取默认项目配置
        
        Returns:
            默认项目配置字典
        """
        return {
            "project_name": "默认项目",
            "project_root": "",
            "frame_rate": 25.0,
            "resolution": {
                "width": 1920,
                "height": 1080,
                "device_aspect_ratio": 1.778
            },
            "color_space": {
                "working_space": "ACEScg",
                "display_space": "ACES 1.0 SDR-video",
                "view_transform": "ACES 1.0 SDR-video"
            },
            "camera_settings": {
                "namespace": "camera",
                "file_prefix": "cam_",
                "focalLength": 35,
                "nearClipPlane": 0.1,
                "farClipPlane": 10000
            }
        }
    
    def _get_default_asset_config(self):
        """获取默认资产配置
        
        Returns:
            默认资产配置字典
        """
        return {
            "types": {
                "char": "角色",
                "prop": "道具",
                "env": "场景",
                "veh": "载具"
            },
            "steps": {
                "mod": "模型",
                "rig": "绑定",
                "shd": "材质",
                "lkd": "外观",
                "abc": "缓存"
            },
            "path_templates": {
                "work": "{project_root}/Asset/{asset_type}/{asset_id}/work",
                "publish": "{project_root}/Asset/{asset_type}/{asset_id}/publish",
                "model": "{project_root}/Asset/{asset_type}/{asset_id}/publish/model",
                "rig": "{project_root}/Asset/{asset_type}/{asset_id}/publish/rig",
                "lookdev": "{project_root}/Asset/{asset_type}/{asset_id}/publish/lookdev",
                "abc": "{project_root}/Asset/{asset_type}/{asset_id}/publish/cache/alembic"
            },
            "file_patterns": {
                "work": "{asset_id}_{asset_type}_{step}_work_v{version:03d}.ma",
                "publish": "{asset_id}_{asset_type}_{step}_publish_v{version:03d}.ma"
            }
        }
    
    def _get_default_shot_config(self):
        """获取默认镜头配置
        
        Returns:
            默认镜头配置字典
        """
        return {
            "steps": {
                "anm": "动画",
                "lgt": "灯光",
                "rnd": "渲染",
                "comp": "合成"
            },
            "path_templates": {
                "animation_work": "{project_root}/Shot/Animation/{episode}/{sequence}/{shot}/work",
                "lighting_work": "{project_root}/Shot/Lighting/{episode}/{sequence}/{shot}/work",
                "lighting_publish": "{project_root}/Shot/Lighting/{episode}/{sequence}/{shot}/publish",
                "render_output": "{project_root}/Shot/Lighting/{episode}/{sequence}/{shot}/output/images",
                "abc_cache": "{project_root}/Shot/Animation/{episode}/{sequence}/{shot}/work/cache/alembic"
            },
            "file_patterns": {
                "animation_work": "{sequence}_{shot}_Anm_work_v{version:03d}.ma",
                "lighting_work": "{sequence}_{shot}_Lgt_work_v{version:03d}.ma"
            },
            "output_directories": {
                "images": "{project_root}/Shot/Lighting/{episode}/{sequence}/{shot}/output/images",
                "aovs": "{project_root}/Shot/Lighting/{episode}/{sequence}/{shot}/output/aovs"
            }
        }
        
    def _get_default_shot_data(self):
        """获取默认镜头数据
        
        Returns:
            默认镜头数据字典
        """
        return {
            "episode": "ep01",
            "sequence": "sc001",
            "shot": "sh010",
            "frame_start": 1001,
            "frame_end": 1100,
            "handle_start": 8,
            "handle_end": 8
        }
        
    def _get_default_alembic_settings(self):
        """获取默认Alembic缓存设置
        
        Returns:
            默认Alembic设置字典
        """
        return {
            "format": "Ogawa",
            "exportUVs": 1,
            "exportNormals": 1,
            "exportMaterialNamespace": 1,
            "exportFaceSets": 1,
            "exportShapeDeformation": 1,
            "exportVisibility": 1
        }
        
    def _get_default_render_settings(self):
        """获取默认渲染设置
        
        Returns:
            默认渲染设置字典
        """
        return {
            "arnold": {
                "AASamples": 3,
                "GIDiffuseSamples": 2,
                "GISpecularSamples": 2,
                "GITransmissionSamples": 2,
                "GISSSSamples": 2,
                "GIVolumeSamples": 2,
                "enableAdaptiveSampling": True,
                "adaptiveThreshold": 0.015,
                "textureMaxMemoryMB": 2048,
                "textureAutomip": True,
                "mergeAOVs": 1,
                "ai_translator": "exr",
                "ignoreSurfaces": False,
                "ignoreDisplacements": False,
                "ignoreMotion": False
            },
            "globals": {
                "imageFilePrefix": "<Scene>/<RenderLayer>/<Scene>_<RenderLayer>",
                "animation": 1,
                "outFormatControl": 0,
                "putFrameBeforeExt": 1,
                "extensionPadding": 4,
                "periodInExt": 1
            },
            "resolution": {
                "width": 1920,
                "height": 1080,
                "deviceAspectRatio": 1.778
            },
            "frame_rate": "pal"
        }
        
    def save_config(self, config_type, data=None):
        """保存配置到文件
        
        Args:
            config_type: 配置类型 ('project', 'asset', 'shot', 'render', 'shot_data', 'alembic')
            data: 要保存的数据，如果为None则使用当前加载的配置
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            if config_type == 'project':
                file_path = self.project_config_path
                if data:
                    self.project_config = data
                config_data = self.project_config
            elif config_type == 'asset':
                file_path = self.asset_config_path
                if data:
                    self.asset_config = data
                config_data = self.asset_config
            elif config_type == 'shot':
                file_path = self.shot_config_path
                if data:
                    self.shot_config = data
                config_data = self.shot_config
            elif config_type == 'render':
                file_path = self.render_settings_path
                if data:
                    self.render_settings = data
                config_data = self.render_settings
            elif config_type == 'shot_data':
                file_path = self.shot_data_path
                if data:
                    self.shot_data = data
                config_data = self.shot_data
            elif config_type == 'alembic':
                file_path = self.alembic_settings_path
                if data:
                    self.alembic_settings = data
                config_data = self.alembic_settings
            else:
                print(f"未知的配置类型: {config_type}")
                return False
                
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"已保存配置到: {file_path}")
            return True
        except Exception as e:
            print(f"保存配置时出错: {e}")
            return False
            
    def get_complete_render_settings(self):
        """获取完整的渲染设置，包括项目特定的路径
        
        Returns:
            合并了项目路径和全局设置的完整渲染设置
        """
        # 合并项目路径到渲染设置
        render_settings = self._merge_project_paths_to_render_settings()
        
        # 输出完整的渲染设置
        merged_settings = {
            "render_settings": render_settings
        }
        
        return merged_settings
    
    def get_frame_rate(self):
        """获取项目帧率设置
        
        Returns:
            帧率值，如果未设置则返回25.0
        """
        return self.project_config.get("frame_rate", 25.0)
    
    def get_resolution(self):
        """获取项目分辨率设置
        
        Returns:
            分辨率字典，包含宽度、高度和宽高比
        """
        return self.project_config.get("resolution", {
            "width": 1920,
            "height": 1080,
            "device_aspect_ratio": 1.778
        })
    
    def get_color_space(self):
        """获取项目色彩空间设置
        
        Returns:
            色彩空间字典，包含工作空间和显示空间
        """
        return self.project_config.get("color_space", {
            "working_space": "ACEScg",
            "display_space": "ACES 1.0 SDR-video",
            "view_transform": "ACES 1.0 SDR-video"
        })
    
    def get_asset_path(self, asset_type, asset_id, path_type="work", step="mod", version=1, ext="ma"):
        """获取资产路径
        
        Args:
            asset_type: 资产类型（如"char"、"prop"）
            asset_id: 资产ID
            path_type: 路径类型（如"work"、"publish"、"abc"）
            step: 制作步骤（如"mod"、"rig"）
            version: 版本号
            ext: 文件扩展名（仅用于文件模式）
            
        Returns:
            格式化后的资产路径
        """
        # 检查路径模板是否存在
        path_templates = self.asset_config.get("path_templates", {})
        file_patterns = self.asset_config.get("file_patterns", {})
        
        if path_type not in path_templates:
            print(f"未知的资产路径类型: {path_type}")
            return ""
            
        # 获取路径模板
        path_template = path_templates[path_type]
        
        # 获取项目根目录
        project_root = self.project_config.get("project_root", "")
        
        # 替换模板变量
        path = path_template.replace("{project_root}", project_root)
        path = path.replace("{asset_type}", asset_type)
        path = path.replace("{asset_id}", asset_id)
        path = path.replace("{step}", step)
        
        # 如果是文件模式，则应用文件模板
        if path_type in file_patterns:
            file_pattern = file_patterns[path_type]
            file_name = file_pattern.format(
                asset_id=asset_id,
                asset_type=asset_type,
                step=step,
                version=version,
                ext=ext
            )
            path = os.path.join(path, file_name)
            
        return path
    
    def get_shot_path(self, episode, sequence, shot, path_type="animation_work", step="anm", version=1, ext="ma"):
        """获取镜头路径
        
        Args:
            episode: 集
            sequence: 场次
            shot: 镜头号
            path_type: 路径类型（如"animation_work"、"lighting_work"）
            step: 制作步骤（如"anm"、"lgt"）
            version: 版本号
            ext: 文件扩展名（仅用于文件模式）
            
        Returns:
            格式化后的镜头路径
        """
        # 检查路径模板是否存在
        path_templates = self.shot_config.get("path_templates", {})
        file_patterns = self.shot_config.get("file_patterns", {})
        
        if path_type not in path_templates:
            print(f"未知的镜头路径类型: {path_type}")
            return ""
            
        # 获取路径模板
        path_template = path_templates[path_type]
        
        # 获取项目根目录
        project_root = self.project_config.get("project_root", "")
        
        # 替换模板变量
        path = path_template.replace("{project_root}", project_root)
        path = path.replace("{episode}", episode)
        path = path.replace("{sequence}", sequence)
        path = path.replace("{shot}", shot)
        path = path.replace("{step}", step)
        
        # 如果是文件模式，则应用文件模板
        if path_type in file_patterns:
            file_pattern = file_patterns[path_type]
            file_name = file_pattern.format(
                episode=episode,
                sequence=sequence,
                shot=shot,
                step=step,
                version=version,
                ext=ext
            )
            path = os.path.join(path, file_name)
            
        return path
    
    def get_asset_step_display_name(self, step_code):
        """获取资产步骤的显示名称
        
        Args:
            step_code: 步骤代码（如"mod"、"rig"）
            
        Returns:
            步骤显示名称（如"模型"、"绑定"）
        """
        steps = self.asset_config.get("steps", {})
        return steps.get(step_code, step_code)
    
    def get_shot_step_display_name(self, step_code):
        """获取镜头步骤的显示名称
        
        Args:
            step_code: 步骤代码（如"anm"、"lgt"）
            
        Returns:
            步骤显示名称（如"动画"、"灯光"）
        """
        steps = self.shot_config.get("steps", {})
        return steps.get(step_code, step_code)
    
    def get_asset_type_display_name(self, type_code):
        """获取资产类型的显示名称
        
        Args:
            type_code: 类型代码（如"char"、"prop"）
            
        Returns:
            类型显示名称（如"角色"、"道具"）
        """
        types = self.asset_config.get("types", {})
        return types.get(type_code, type_code)
    
    def apply_global_settings_to_maya(self):
        """将项目的全局设置应用到Maya场景中
        
        应用帧率、分辨率等全局设置
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 应用分辨率设置
            resolution = self.get_resolution()
            if resolution:
                width = resolution.get("width", 1920)
                height = resolution.get("height", 1080)
                aspect_ratio = resolution.get("device_aspect_ratio", 1.778)
                
                mc.setAttr("defaultResolution.width", width)
                mc.setAttr("defaultResolution.height", height)
                mc.setAttr("defaultResolution.deviceAspectRatio", aspect_ratio)
                print(f"已应用分辨率设置: {width}x{height}, 宽高比: {aspect_ratio}")
            
            # 应用帧率设置
            frame_rate = self.get_frame_rate()
            if frame_rate:
                try:
                    # 根据帧率设置时间单位
                    if frame_rate == 24:
                        mc.currentUnit(time='film')
                    elif frame_rate == 25:
                        mc.currentUnit(time='pal')
                    elif frame_rate == 30:
                        mc.currentUnit(time='ntsc')
                    elif frame_rate == 48:
                        mc.currentUnit(time='show')
                    elif frame_rate == 50:
                        mc.currentUnit(time='palf')
                    elif frame_rate == 60:
                        mc.currentUnit(time='ntscf')
                    else:
                        # 自定义帧率
                        mc.currentUnit(time=f'{frame_rate}fps')
                    print(f"已应用帧率设置: {frame_rate} fps")
                except Exception as e:
                    print(f"设置帧率时出错: {e}")
            
            # 应用色彩空间设置（如果Maya支持）
            color_space = self.get_color_space()
            if color_space and hasattr(mc, 'colorManagementPrefs'):
                working_space = color_space.get("working_space")
                if working_space:
                    try:
                        mc.colorManagementPrefs(e=True, cmEnabled=True)
                        mc.colorManagementPrefs(e=True, configFilePath="")  # ACES配置
                        mc.colorManagementPrefs(e=True, renderingSpaceName=working_space)
                        print(f"已应用色彩空间设置: 工作空间={working_space}")
                    except Exception as e:
                        print(f"设置色彩空间时出错: {e}")
            
            return True
        except Exception as e:
            print(f"应用全局设置时出错: {e}")
            return False 