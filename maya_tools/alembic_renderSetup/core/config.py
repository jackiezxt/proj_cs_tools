"""
渲染设置配置模块

提供统一的配置访问接口，从ConfigManager加载配置
"""

import importlib
import maya.cmds as cmds
from maya_tools.common.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 默认配置
DEFAULT_CONFIG = {
    "resolution": {
        "width": 1920,
        "height": 1080
    },
    "frame_rate": 24,
    "color_space": "ACES - ACEScg",
    "render_settings": {
        "renderer": "arnold",
        "image_format": "exr",
        "color_space": "ACES - ACEScg",
        "bit_depth": 16,
        "compression": "zip"
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

def _load_configurations():
    """加载并合并配置信息
    
    Returns:
        合并后的配置字典
    """
    # 从render_settings.json获取渲染配置
    render_settings = config_manager.render_settings
    
    # 从项目配置获取全局设置
    project_config = config_manager.project_config
    
    # 合并配置到CONFIG字典
    config = {}
    
    # 添加渲染设置
    if "render_settings" in render_settings:
        config["render_settings"] = render_settings["render_settings"]
    
    # 添加全局项目设置
    if "frame_rate" in project_config:
        config["frame_rate"] = project_config["frame_rate"]
    
    if "resolution" in project_config:
        config["resolution"] = project_config["resolution"]
    
    if "color_space" in project_config:
        config["color_space"] = project_config["color_space"]
    
    # 确保所有必要的配置都存在
    config = deep_merge(DEFAULT_CONFIG, config)
    
    print("渲染设置配置已加载完成:")
    print(f"- 帧率: {config.get('frame_rate', 24)}")
    print(f"- 分辨率: {config['resolution']['width']}x{config['resolution']['height']}")
    print(f"- 色彩空间: {config.get('color_space', 'ACES - ACEScg')}")
    print(f"- 渲染器: {config['render_settings'].get('renderer', 'arnold')}")
    
    return config

# 加载配置
CONFIG = _load_configurations()

# 导出常用配置
RENDER_SETTINGS = CONFIG.get("render_settings", {})
RESOLUTION = CONFIG.get("resolution", {"width": 1920, "height": 1080})
FRAME_RATE = CONFIG.get("frame_rate", 24)
COLOR_SPACE = CONFIG.get("color_space", "ACES - ACEScg")

def reload_config():
    """重新加载所有配置
    
    当配置文件被修改后，可以调用此函数重新加载配置，
    而不需要重启Maya或重新导入模块。
    
    Returns:
        重新加载后的配置字典
    """
    global config_manager, CONFIG
    global RENDER_SETTINGS, RESOLUTION, FRAME_RATE, COLOR_SPACE
    
    # 重新导入配置管理器模块
    config_manager_module = importlib.import_module("maya_tools.common.config_manager")
    importlib.reload(config_manager_module)
    
    # 重新创建配置管理器
    config_manager = ConfigManager()
    
    # 重新加载配置
    CONFIG = _load_configurations()
    
    # 更新全局变量
    RENDER_SETTINGS = CONFIG.get("render_settings", {})
    RESOLUTION = CONFIG.get("resolution", {"width": 1920, "height": 1080})
    FRAME_RATE = CONFIG.get("frame_rate", 24)
    COLOR_SPACE = CONFIG.get("color_space", "ACES - ACEScg")
    
    print("渲染设置配置已重新加载")
    return CONFIG

def apply_settings_to_scene():
    """将配置设置应用到当前Maya场景
    
    应用帧率、分辨率和色彩空间设置
    """
    # 设置帧率
    cmds.currentUnit(time='film')  # 默认24 fps
    if FRAME_RATE != 24:
        if FRAME_RATE == 25:
            cmds.currentUnit(time='pal')
        elif FRAME_RATE == 30:
            cmds.currentUnit(time='ntsc')
        elif FRAME_RATE == 48:
            cmds.currentUnit(time='show')
        elif FRAME_RATE == 50:
            cmds.currentUnit(time='palf')
        elif FRAME_RATE == 60:
            cmds.currentUnit(time='ntscf')
        else:
            # 自定义帧率
            cmds.currentUnit(time=f'{FRAME_RATE}fps')
    
    # 设置分辨率
    width = RESOLUTION.get("width", 1920)
    height = RESOLUTION.get("height", 1080)
    cmds.setAttr("defaultResolution.width", width)
    cmds.setAttr("defaultResolution.height", height)
    cmds.setAttr("defaultResolution.deviceAspectRatio", float(width) / height)
    
    # 设置色彩空间
    # 检查是否支持色彩空间设置
    if hasattr(cmds, 'colorManagementPrefs'):
        cmds.colorManagementPrefs(edit=True, cmEnabled=True)
        # 根据渲染器设置不同的色彩空间
        renderer = RENDER_SETTINGS.get("renderer", "arnold")
        
        if renderer == "arnold":
            # 对于Arnold渲染器
            cmds.colorManagementPrefs(edit=True, cmConfigFileEnabled=True)
            cmds.colorManagementPrefs(edit=True, configFilePath="ACES")
            cmds.colorManagementPrefs(edit=True, renderingSpaceName=COLOR_SPACE)
    
    print("已将配置设置应用到当前Maya场景")
    print(f"- 帧率: {FRAME_RATE}")
    print(f"- 分辨率: {width}x{height}")
    print(f"- 色彩空间: {COLOR_SPACE}")

def get_shot_path(episode, sequence, shot, path_type="lighting_work", step="lgt", version=1, ext="ma"):
    """获取镜头路径
    
    Args:
        episode: 集
        sequence: 场次
        shot: 镜头号
        path_type: 路径类型（如"lighting_work"、"render_output"）
        step: 制作步骤（如"lgt"）
        version: 版本号
        ext: 文件扩展名
        
    Returns:
        格式化后的镜头路径
    """
    return config_manager.get_shot_path(episode, sequence, shot, path_type, step, version, ext)