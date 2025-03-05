"""
Alembic导出器配置模块

提供统一的配置访问接口，从ConfigManager加载设置
"""

import os
import importlib
from maya_tools.common.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 默认配置
DEFAULT_CONFIG = {
    "alembic_settings": {
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
    # 从alembic_settings.json获取Alembic配置
    alembic_settings = config_manager.alembic_settings
    
    # 从项目配置获取基础信息
    project_config = config_manager.project_config
    
    # 从资产配置获取资产类型和步骤
    asset_config = config_manager.asset_config
    
    # 从镜头配置获取路径模板
    shot_config = config_manager.shot_config
    
    # 合并配置到CONFIG字典
    config = {}
    
    # 添加Alembic设置
    config["alembic_settings"] = alembic_settings
    
    # 添加项目根目录
    if "project_root" in project_config:
        config["project_root"] = project_config["project_root"]
    
    # 添加资产类型和步骤
    if "types" in asset_config:
        config["types"] = asset_config["types"]
    
    if "steps" in asset_config:
        config["steps"] = asset_config["steps"]
    
    # 添加路径模板
    config["path_templates"] = {}
    
    # 添加镜头路径模板
    if "path_templates" in shot_config:
        for key, value in shot_config["path_templates"].items():
            config["path_templates"][key] = value
    
    # 添加资产路径模板
    if "path_templates" in asset_config:
        for key, value in asset_config["path_templates"].items():
            config["path_templates"][f"asset_{key}"] = value
    
    # 添加文件模式
    if "file_patterns" in asset_config:
        config["file_patterns"] = asset_config["file_patterns"]
    
    # 确保所有必要的配置都存在
    config = deep_merge(DEFAULT_CONFIG, config)
    
    print("Alembic导出器配置已加载完成:")
    print(f"- 项目根路径: {config.get('project_root', '未设置')}")
    print(f"- 数据格式: {config['alembic_settings'].get('data_format', 'ogawa')}")
    
    if "types" in config:
        print(f"- 支持的资产类型: {', '.join(config['types'].keys())}")
    
    if "steps" in config:
        print(f"- 支持的资产步骤: {', '.join(config['steps'].keys())}")
    
    return config

# 加载配置
CONFIG = _load_configurations()

# 导出常用配置
ALEMBIC_SETTINGS = CONFIG.get("alembic_settings", {})
PATH_TEMPLATES = CONFIG.get("path_templates", {})
PROJECT_ROOT = CONFIG.get("project_root", "")
ASSET_TYPES = CONFIG.get("types", {})
ASSET_STEPS = CONFIG.get("steps", {})
FILE_PATTERNS = CONFIG.get("file_patterns", {})

def reload_config():
    """重新加载所有配置
    
    当配置文件被修改后，可以调用此函数重新加载配置，
    而不需要重启Maya或重新导入模块。
    
    Returns:
        重新加载后的配置字典
    """
    global config_manager, CONFIG
    global ALEMBIC_SETTINGS, PATH_TEMPLATES, PROJECT_ROOT, ASSET_TYPES, ASSET_STEPS, FILE_PATTERNS
    
    # 重新导入配置管理器模块
    config_manager_module = importlib.import_module("maya_tools.common.config_manager")
    importlib.reload(config_manager_module)
    
    # 重新创建配置管理器
    config_manager = ConfigManager()
    
    # 重新加载配置
    CONFIG = _load_configurations()
    
    # 更新全局变量
    ALEMBIC_SETTINGS = CONFIG.get("alembic_settings", {})
    PATH_TEMPLATES = CONFIG.get("path_templates", {})
    PROJECT_ROOT = CONFIG.get("project_root", "")
    ASSET_TYPES = CONFIG.get("types", {})
    ASSET_STEPS = CONFIG.get("steps", {})
    FILE_PATTERNS = CONFIG.get("file_patterns", {})
    
    print("Alembic导出器配置已重新加载")
    return CONFIG

def get_asset_path(asset_type, asset_id, path_type="work", step="mod", version=1, ext="ma"):
    """获取资产路径
    
    Args:
        asset_type: 资产类型（如"char"、"prop"）
        asset_id: 资产ID
        path_type: 路径类型（如"work"、"publish"、"abc"）
        step: 制作步骤（如"mod"、"rig"）
        version: 版本号
        ext: 文件扩展名
        
    Returns:
        格式化后的资产路径
    """
    return config_manager.get_asset_path(asset_type, asset_id, path_type, step, version, ext)

def get_shot_path(episode, sequence, shot, path_type="animation_work", step="anm", version=1, ext="ma"):
    """获取镜头路径
    
    Args:
        episode: 集
        sequence: 场次
        shot: 镜头号
        path_type: 路径类型（如"animation_work"、"lighting_work"）
        step: 制作步骤（如"anm"、"lgt"）
        version: 版本号
        ext: 文件扩展名
        
    Returns:
        格式化后的镜头路径
    """
    return config_manager.get_shot_path(episode, sequence, shot, path_type, step, version, ext)

def get_asset_step_display_name(step_code):
    """获取资产步骤的显示名称
    
    Args:
        step_code: 步骤代码（如"mod"、"rig"）
        
    Returns:
        步骤显示名称（如"模型"、"绑定"）
    """
    return config_manager.get_asset_step_display_name(step_code)

def get_asset_type_display_name(type_code):
    """获取资产类型的显示名称
    
    Args:
        type_code: 类型代码（如"char"、"prop"）
        
    Returns:
        类型显示名称（如"角色"、"道具"）
    """
    return config_manager.get_asset_type_display_name(type_code) 