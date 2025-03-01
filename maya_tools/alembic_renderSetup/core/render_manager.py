import maya.cmds as mc
from .utils import handle_error
from .config import RENDER_SETTINGS


class RenderManager:
    """渲染设置管理类"""

    @staticmethod
    def setup_arnold_renderer():
        """设置Arnold渲染器参数"""
        try:
            if not mc.pluginInfo("mtoa", query=True, loaded=True):
                return False, "Arnold插件未加载"
            
            mc.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")

            arnold_settings = RENDER_SETTINGS["arnold"]
            
            if mc.objExists("defaultArnoldDriver"):
                mc.setAttr("defaultArnoldDriver.mergeAOVs", arnold_settings["mergeAOVs"])
                mc.setAttr("defaultArnoldDriver.ai_translator", arnold_settings["ai_translator"], type="string")
            
            if mc.objExists("defaultArnoldRenderOptions"):
                mc.setAttr("defaultArnoldRenderOptions.AASamples", arnold_settings["AASamples"])
                mc.setAttr("defaultArnoldRenderOptions.GIDiffuseSamples", arnold_settings["GIDiffuseSamples"])
                mc.setAttr("defaultArnoldRenderOptions.GISpecularSamples", arnold_settings["GISpecularSamples"])
            
            return True, None
            
        except Exception as e:
            return False, str(e)

    @staticmethod
    def save_render_settings():
        """保存当前渲染设置"""
        settings = {}
        try:
            if mc.objExists("defaultRenderGlobals"):
                settings["startFrame"] = mc.getAttr("defaultRenderGlobals.startFrame")
                settings["endFrame"] = mc.getAttr("defaultRenderGlobals.endFrame")
                settings["currentRenderer"] = mc.getAttr("defaultRenderGlobals.currentRenderer")
            
            # 保存Arnold设置
            if mc.objExists("defaultArnoldDriver"):
                settings["mergeAOVs"] = mc.getAttr("defaultArnoldDriver.mergeAOVs")
                settings["ai_translator"] = mc.getAttr("defaultArnoldDriver.ai_translator")
            
            return settings
        except Exception as e:
            mc.warning(f"保存渲染设置时出错: {str(e)}")
            return {}

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

            # 使用配置文件中的全局渲染参数
            globals_settings = RENDER_SETTINGS["globals"]

            for attr, value in globals_settings.items():
                mc.setAttr(f"defaultRenderGlobals.{attr}", value)
            return True, None
        except Exception as e:
            return False, str(e)

