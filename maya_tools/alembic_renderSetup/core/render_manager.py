import maya.cmds as mc
from .utils import handle_error
from .config import ARNOLD_SETTINGS, GLOBALS_SETTINGS, RESOLUTION_SETTINGS, FRAME_RATE


class RenderManager:
    """渲染设置管理类"""

    @staticmethod
    def get_arnold_version():
        """获取当前 Arnold 渲染器版本"""
        try:
            if mc.pluginInfo("mtoa", query=True, loaded=True):
                arnold_version = mc.pluginInfo("mtoa", query=True, version=True)
                return arnold_version
            return "未知"
        except Exception as e:
            mc.warning(f"获取 Arnold 版本时出错: {str(e)}")
            return "未知"

    @staticmethod
    def get_compatible_arnold_attrs():
        """根据 Arnold 版本返回兼容的属性列表"""
        try:
            version = RenderManager.get_arnold_version()
            
            # 所有版本都应该支持的基本属性
            base_attrs = {
                "AASamples": ARNOLD_SETTINGS.get("AASamples", 3),
                "GIDiffuseSamples": ARNOLD_SETTINGS.get("GIDiffuseSamples", 2),
                "GISpecularSamples": ARNOLD_SETTINGS.get("GISpecularSamples", 2)
            }
            
            # 根据版本确定可选属性
            optional_attrs = []
            
            # 创建版本号的主要和次要版本
            version_parts = version.split('.')
            major_version = int(version_parts[0]) if len(version_parts) > 0 and version_parts[0].isdigit() else 0
            minor_version = int(version_parts[1]) if len(version_parts) > 1 and version_parts[1].isdigit() else 0
            
            # 5.3.1 版本兼容的属性
            if major_version == 5 and minor_version >= 3:
                optional_attrs = [
                    "GITransmissionSamples",
                    "GIVolumeSamples",
                    "enableAdaptiveSampling",
                    "textureMaxMemoryMB"
                    # "textureAutomip" 在 5.3.1 版本中不存在
                ]
            
            # 打印版本信息
            mc.warning(f"当前 Arnold 版本: {version}")
            
            # 返回基本属性
            return base_attrs, optional_attrs
        except Exception as e:
            mc.warning(f"获取兼容属性时出错: {str(e)}")
            return {}, []

    @staticmethod
    def setup_arnold_renderer():
        """设置Arnold渲染器参数"""
        try:
            if not mc.pluginInfo("mtoa", query=True, loaded=True):
                return False, "Arnold插件未加载"
            
            # 打印当前 Arnold 版本
            version = RenderManager.get_arnold_version()
            mc.warning(f"正在为 Arnold {version} 设置渲染参数")
            
            mc.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")

            # 确保arnold设置存在
            if not ARNOLD_SETTINGS:
                return False, "找不到Arnold渲染设置"
            
            if mc.objExists("defaultArnoldDriver"):
                # 设置驱动器参数
                mc.setAttr("defaultArnoldDriver.mergeAOVs", ARNOLD_SETTINGS.get("mergeAOVs", 1))
                
                # 字符串类型属性需要指定类型
                translator = ARNOLD_SETTINGS.get("ai_translator", "exr")
                mc.setAttr("defaultArnoldDriver.ai_translator", translator, type="string")
            
            if mc.objExists("defaultArnoldRenderOptions"):
                # 获取当前 Arnold 版本兼容的属性
                base_attrs, optional_attrs = RenderManager.get_compatible_arnold_attrs()
                
                # 添加可选属性
                attrs_to_set = base_attrs.copy()
                for attr in optional_attrs:
                    if attr in ARNOLD_SETTINGS:
                        attrs_to_set[attr] = ARNOLD_SETTINGS[attr]
                
                # 打印将要设置的属性
                mc.warning(f"将设置以下 Arnold 属性: {', '.join(attrs_to_set.keys())}")
                
                # 安全地设置所有属性
                for attr, value in attrs_to_set.items():
                    try:
                        if mc.attributeQuery(attr, node="defaultArnoldRenderOptions", exists=True):
                            mc.setAttr(f"defaultArnoldRenderOptions.{attr}", value)
                            mc.warning(f"成功设置 {attr} = {value}")
                        else:
                            mc.warning(f"属性 defaultArnoldRenderOptions.{attr} 在当前 Arnold 版本中不存在")
                    except Exception as e:
                        mc.warning(f"设置 defaultArnoldRenderOptions.{attr} 时出错: {str(e)}")
            
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def save_render_settings():
        """保存当前渲染设置"""
        try:
            settings = {}
            
            if mc.objExists("defaultArnoldRenderOptions"):
                settings["AASamples"] = mc.getAttr("defaultArnoldRenderOptions.AASamples")
                settings["GIDiffuseSamples"] = mc.getAttr("defaultArnoldRenderOptions.GIDiffuseSamples")
                settings["GISpecularSamples"] = mc.getAttr("defaultArnoldRenderOptions.GISpecularSamples")
            
            if mc.objExists("defaultArnoldDriver"):
                settings["mergeAOVs"] = mc.getAttr("defaultArnoldDriver.mergeAOVs")
                settings["ai_translator"] = mc.getAttr("defaultArnoldDriver.ai_translator")
            
            return settings
        except Exception as e:
            mc.warning(f"保存渲染设置时出错: {str(e)}")
            return {}

    @staticmethod
    def setup_resolution():
        """设置渲染分辨率"""
        try:
            # 获取分辨率设置
            width = RESOLUTION_SETTINGS.get("width", 1920)
            height = RESOLUTION_SETTINGS.get("height", 1080)
            aspect_ratio = RESOLUTION_SETTINGS.get("deviceAspectRatio", 1.778)
            
            # 打印使用的分辨率值
            mc.warning(f"使用配置中的分辨率: {width}x{height}, 宽高比: {aspect_ratio}")
            
            # 获取当前分辨率
            current_width = mc.getAttr("defaultResolution.width")
            current_height = mc.getAttr("defaultResolution.height")
            current_aspect = mc.getAttr("defaultResolution.deviceAspectRatio")
            
            mc.warning(f"当前分辨率: {current_width}x{current_height}, 宽高比: {current_aspect}")
            
            # 设置分辨率
            mc.setAttr("defaultResolution.width", width)
            mc.setAttr("defaultResolution.height", height)
            mc.setAttr("defaultResolution.deviceAspectRatio", aspect_ratio)
            
            # 打印日志
            mc.warning(f"已更新渲染分辨率: {width}x{height}, 宽高比: {aspect_ratio}")
            
            return True, None
        except Exception as e:
            mc.warning(f"设置渲染分辨率时出错: {str(e)}")
            return False, str(e)

    @staticmethod
    def setup_render_globals(start_frame, end_frame):
        """设置渲染全局参数"""
        if start_frame is None or end_frame is None:
            return False, "无效的帧范围"
        
        if not isinstance(start_frame, (int, float)) or not isinstance(end_frame, (int, float)):
            return False, "帧范围必须是数字"
        
        if start_frame > end_frame:
            return False, "起始帧不能大于结束帧"
        
        try:
            # 设置帧范围
            mc.setAttr("defaultRenderGlobals.startFrame", start_frame)
            mc.setAttr("defaultRenderGlobals.endFrame", end_frame)

            # 设置帧率
            mc.currentUnit(time=FRAME_RATE)

            # 设置分辨率
            RenderManager.setup_resolution()

            # 使用配置文件中的全局渲染参数
            for attr, value in GLOBALS_SETTINGS.items():
                try:
                    # 为常见的字符串属性添加类型标志
                    if attr in ["imageFilePrefix", "preRenderMel", "postRenderMel", "renderingEngine"]:
                        mc.setAttr(f"defaultRenderGlobals.{attr}", value, type="string")
                    else:
                        mc.setAttr(f"defaultRenderGlobals.{attr}", value)
                except Exception as e:
                    mc.warning(f"设置 {attr} 时出错: {str(e)}")
                    
            return True, None
        except Exception as e:
            return False, str(e)

