"""
alembic_renderSetup 配置模块
从 JSON 文件加载配置参数
"""
import os
import json

# 获取配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONFIG_FILE = os.path.join(CONFIG_DIR, "project_config.json")

# 默认配置
DEFAULT_CONFIG = {
    "render_settings": {
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
    },
    "path_templates": {
        "lighting_work": "X:/projects/CSprojectFiles/Shot/Lighting/{episode}/{sequence}/{shot}/work",
        "lighting_file_pattern": "{sequence}_{shot}_Lgt_v{version:03d}.ma"
    },
    "camera_settings": {
        "namespace": "camera",
        "file_prefix": "cam_"
    }
}

def load_config():
    """从 JSON 文件加载配置，如果文件不存在则使用默认配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if not all(key in config for key in DEFAULT_CONFIG.keys()):
                    print("配置文件不完整，使用默认配置补充缺失项")
                    # 合并配置，保留已有配置，补充缺失项
                    merged_config = DEFAULT_CONFIG.copy()
                    merged_config.update(config)
                    return merged_config
                return config
        else:
            # 确保目录存在
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            
            # 写入默认配置
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"加载配置文件时出错: {str(e)}")
        return DEFAULT_CONFIG

# 加载配置
CONFIG = load_config()

# 导出配置项，方便其他模块使用
RENDER_SETTINGS = CONFIG["render_settings"]
PATH_TEMPLATES = CONFIG["path_templates"]
CAMERA_SETTINGS = CONFIG["camera_settings"]