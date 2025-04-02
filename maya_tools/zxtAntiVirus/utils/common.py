# -*- coding: utf-8 -*-
"""
通用模块
提供共享的常量、函数和配置项
"""
import os
import re
import datetime
import base64
import shutil
from core.patterns import WHITELISTED_FILES

# 已知的可疑脚本节点名称
SUSPICIOUS_NODES = ["uifiguration", "uiConfigurationScriptNode", "sceneConfigurationScriptNode", "scriptNode"]

# 已知的可疑代码片段
SUSPICIOUS_CODE_PATTERNS = [
    # base64编码/解码相关
    r"base64\.urlsafe_b64decode",
    r"base64\.b64decode",
    
    # 常见病毒类和函数命名
    r"class\s+phage",
    r"leukocyte\s*=\s*phage\(\)",
    r"leukocyte\.occupation\(\)",
    r"antivirus",
    
    # 文件操作
    r"userSetup\.mel",
    r"userSetup\.py",
    r"os\.chmod",
    r"stat\.S_IWRITE",
    
    # 自动启动机制
    r"scriptJob.*SceneSaved",
    
    # 使用eval或exec执行代码
    r"eval\s*\(\s*cmds\.getAttr\(",
    r"exec\s*\(\s*_?pycode\s*\)",
    
    # 可疑的外部连接
    r"http://"
]

# 已知恶意文件名 - 这些文件如果存在应该直接删除
KNOWN_MALICIOUS_FILES = [
    'vaccine.py', 
    'vaccine.pyc', 
    'userSetup.py', 
    'userSetup.pyc', 
    'fuckVirus.py', 
    'fuckVirus.pyc', 
    'userSetup.mel',
    'leukocyte.py',
    'leukocyte.pyc'    
]

# 替换原来的SUSPICIOUS_FILE_NAMES
SUSPICIOUS_FILE_NAMES = KNOWN_MALICIOUS_FILES

# 白名单文件（用户自己编写的安全文件）
WHITELISTED_FILES = [
    "zxtSCNclearUp.py",
    "zxt_scene_cleaner.py"
]

# 白名单目录（整个目录都不会被扫描）
WHITELISTED_DIRS = [
    "backup",
    "cache",
    "sourceimages",
    "renderData"
]

# 恶意代码识别模式（更严格的标准，用于确认有害文件）
HARMFUL_CODE_PATTERNS = [
    r"class\s+phage",
    r"leukocyte\s*=\s*phage\(\)",
    r"import\s+base64.*exec\s*\(",
    r"cmds\.scriptJob\(.*SceneSaved"
]

def get_maya_user_dirs():
    """获取Maya用户目录，只返回文档目录下的maya路径"""
    maya_app_dirs = []
    
    # Windows: 只返回用户文档目录下的maya文件夹
    doc_path = os.path.expanduser("~/Documents/maya")
    if os.path.exists(doc_path):
        maya_app_dirs.append(doc_path)
    
    # 不再包含AppData目录
    # app_data_path = os.path.expanduser("~/AppData/Roaming/Autodesk/maya")
    # if os.path.exists(app_data_path):
    #     maya_app_dirs.append(app_data_path)
    
    return maya_app_dirs

def create_backup(file_path):
    """创建文件备份"""
    try:
        # 在原位置创建备份，添加时间戳和.bak后缀
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        return None

def decode_base64_content(encoded_data):
    """尝试解码base64内容并返回结果"""
    try:
        decoded = base64.b64decode(encoded_data).decode('utf-8', errors='ignore')
        return decoded
    except:
        try:
            # 尝试urlsafe_b64decode
            decoded = base64.urlsafe_b64decode(encoded_data).decode('utf-8', errors='ignore')
            return decoded
        except:
            return None

def check_if_file_in_whitelist(file_path, whitelist=None):
    """检查文件是否在白名单中"""
    # 懒加载patterns模块，避免循环导入
    if whitelist is None:
        # 导入放在函数内部
        try:
            from core.patterns import WHITELISTED_FILES
            whitelist = WHITELISTED_FILES
        except ImportError:
            # 如果导入失败，使用默认白名单
            whitelist = ["zxtSCNclearUp.py", "zxt_scene_cleaner.py"]
    
    # 去除路径，只保留文件名
    base_name = os.path.basename(file_path)
    return base_name.lower() in [name.lower() for name in whitelist]

def is_maya_ascii_file(file_path):
    """检查文件是否为Maya ASCII格式"""
    return file_path.lower().endswith('.ma')

def is_maya_binary_file(file_path):
    """检查文件是否为Maya Binary格式"""
    return file_path.lower().endswith('.mb')

def is_maya_file(file_path):
    """检查文件是否为Maya文件(ASCII或二进制)"""
    return is_maya_ascii_file(file_path) or is_maya_binary_file(file_path)

def get_script_node_content(script_block, logger=None):
    """从脚本节点块中提取代码内容"""
    try:
        # 尝试多种模式匹配脚本内容
        # 模式1: setAttr ".b" -type "string" ("code");
        pattern1 = r'setAttr\s+"\.[a-z]{1,5}"\s+-type\s+"string"\s+\(\s*"(.*?)"\s*\)\s*;'
        match1 = re.search(pattern1, script_block, re.DOTALL)
        if match1:
            return match1.group(1).replace("\\\"", "\"").replace("\\n", "\n")
            
        # 模式2: setAttr ".b" -type "string" "code";
        pattern2 = r'setAttr\s+"\.[a-z]{1,5}"\s+-type\s+"string"\s+"(.*?)"[\s\n]*;'
        match2 = re.search(pattern2, script_block, re.DOTALL)
        if match2:
            return match2.group(1).replace("\\\"", "\"").replace("\\n", "\n")
        
        if logger:
            logger.warning("无法提取脚本节点内容")
        return None
    except Exception as e:
        if logger:
            logger.error(f"提取脚本内容时出错: {str(e)}")
        return None

def get_script_node_name(script_block, logger=None):
    """从脚本节点块中提取节点名称"""
    try:
        pattern = r'createNode\s+script\s+-n\s+"([^"]+)"'
        match = re.search(pattern, script_block)
        if match:
            return match.group(1)
        
        if logger:
            logger.warning("无法提取脚本节点名称")
        return None
    except Exception as e:
        if logger:
            logger.error(f"提取节点名称时出错: {str(e)}")
        return None 