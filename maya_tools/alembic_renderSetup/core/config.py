"""
alembic_renderSetup 配置模块
从 JSON 文件加载配置参数，提供默认值并确保配置完整
"""
import os
import json
from maya_tools.common.config_manager import ConfigManager

# 创建配置管理器实例
config_manager = ConfigManager()

# 默认配置 - 包含所有必要的配置项
DEFAULT_CONFIG = {
    "render_settings": {
        "arnold": {
            "AASamples": 3,
            "GIDiffuseSamples": 2,
            "GISpecularSamples": 2,
            "GITransmissionSamples": 2,
            "GIVolumeSamples": 2,
            "enableAdaptiveSampling": True,
            "textureMaxMemoryMB": 2048,
            "mergeAOVs": 1,
            "ai_translator": "exr"
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
    },
    "camera_settings": {
        "namespace": "camera",
        "file_prefix": "cam_",
        "focalLength": 35,
        "nearClipPlane": 0.1,
        "farClipPlane": 10000
    },
    "path_templates": {
        "lighting_work": "X:/projects/CSprojectFiles/Shot/Lighting/{episode}/{sequence}/{shot}/work",
        "render_output": "X:/projects/CSprojectFiles/Shot/Lighting/{episode}/{sequence}/{shot}/output/images",
        "cloth_sim_path": "X:/projects/CSprojectFiles/Shot/CFX/{sequence}/{shot}",
        "xgen_sim_path": "X:/projects/CSprojectFiles/Shot/CFX/{sequence}/{shot}"
    }
}

def deep_merge(source, destination):
    """深度合并两个字典，用source中的值填充destination中不存在的键
    
    Args:
        source: 源字典（默认值）
        destination: 目标字典（用户配置）
        
    Returns:
        合并后的字典
    """
    for key, value in source.items():
        if key not in destination:
            destination[key] = value
        elif isinstance(value, dict) and isinstance(destination[key], dict):
            destination[key] = deep_merge(value, destination[key])
    return destination

# 加载配置
original_settings = config_manager.render_settings

# 获取项目配置中的路径模板
project_config = config_manager.project_config
project_path_templates = project_config.get("path_templates", {})

# 检测配置结构并适配
if "render_settings" in original_settings:
    # 新版本配置格式
    user_config = original_settings
    print("检测到新版配置格式，使用外层结构")
else:
    # 旧版本配置格式 - 包装一层
    user_config = {"render_settings": original_settings, "camera_settings": {}, "path_templates": {}}
    print("检测到旧版配置格式，进行结构转换")

# 确保项目配置中的路径模板被包含在用户配置中
if project_path_templates:
    if "path_templates" not in user_config:
        user_config["path_templates"] = {}
    user_config["path_templates"].update(project_path_templates)
    print(f"合并项目配置中的路径模板: {', '.join(project_path_templates.keys())}")

CONFIG = deep_merge(DEFAULT_CONFIG, user_config)

# 打印配置结构进行调试
print("配置合并后的 CONFIG 结构:")
print(CONFIG)

# 导出配置，以便其他模块使用
# 简化配置访问，使用统一结构
RENDER_SETTINGS = CONFIG["render_settings"]
ARNOLD_SETTINGS = RENDER_SETTINGS["arnold"]
GLOBALS_SETTINGS = RENDER_SETTINGS["globals"]
RESOLUTION_SETTINGS = RENDER_SETTINGS.get("resolution", {"width": 1920, "height": 1080, "deviceAspectRatio": 1.778})
CAMERA_SETTINGS = CONFIG["camera_settings"]
PATH_TEMPLATES = CONFIG["path_templates"]
FRAME_RATE = RENDER_SETTINGS["frame_rate"]

# 打印最终使用的分辨率设置
print("\n最终使用的分辨率设置:")
print(RESOLUTION_SETTINGS)

# 打印配置加载信息
print("成功加载渲染设置")