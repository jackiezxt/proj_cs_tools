#!/usr/bin/env python
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
import traceback
# 移除顶部导入，改为延迟导入避免循环引用
# from core.patterns import WHITELISTED_FILES
from utils.logger import Logger

# 创建默认日志记录器
logger = Logger()

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
# 不再重复定义，改为从core.patterns按需导入
LOCAL_WHITELISTED_FILES = [
    "zxtSCNclearUp.py",
    "zxt_scene_cleaner.py",
    "zxtAntiVirus.py", 
    "README.md", 
    "__init__.py"
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
    """
    创建文件备份，返回备份文件路径
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        backup_path = "{}.{}".format(file_path, datetime.datetime.now().strftime("%Y%m%d_%H%M%S.bak"))
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"创建备份失败: {str(e)}")
        traceback.print_exc()
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

def check_if_file_in_whitelist(file_name):
    """
    检查文件是否在白名单列表中
    使用延迟导入避免循环引用
    """
    try:
        # 先检查本地定义的白名单
        if file_name.lower() in [name.lower() for name in LOCAL_WHITELISTED_FILES]:
            return True
            
        # 再检查patterns.py中的白名单
        from core.patterns import WHITELIST_FILES
        return file_name.lower() in [name.lower() for name in WHITELIST_FILES]
    except ImportError:
        # 如果无法导入，仅使用本地白名单
        return file_name.lower() in [name.lower() for name in LOCAL_WHITELISTED_FILES]
    except Exception as e:
        print(f"检查白名单时出错: {str(e)}")
        traceback.print_exc()
        return False

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

def get_maya_user_script_dir():
    """获取Maya用户脚本目录（我的文档/maya/scripts）"""
    user_docs = os.path.expanduser("~")
    maya_scripts = os.path.join(user_docs, "Documents", "maya", "scripts")
    
    # 标准化路径，确保一致性
    return os.path.normpath(maya_scripts)

def normalize_path(path):
    """标准化路径，确保使用一致的分隔符"""
    return os.path.normpath(path)

def read_file_with_encoding(file_path, logger=None):
    """读取文件内容并自动检测编码"""
    if logger is None:
        from utils.logger import Logger
        logger = Logger()
    
    # 优先尝试的编码列表
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'shift-jis', 'latin1']
    
    # 首先尝试检测文件编码（如果可能）
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)  # 读取前4KB进行编码检测
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            confidence = result['confidence']
            
            if detected_encoding and confidence > 0.7:
                if logger:
                    logger.info(f"检测到文件编码: {detected_encoding}，置信度: {confidence:.2f}")
                # 将检测到的编码添加到尝试列表的最前面
                if detected_encoding.lower() not in [enc.lower() for enc in encodings_to_try]:
                    encodings_to_try.insert(0, detected_encoding)
    except ImportError:
        if logger:
            logger.warning("未安装chardet模块，将依次尝试常见编码")
        
    # 依次尝试不同编码
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                if logger:
                    logger.info(f"成功以 {encoding} 编码读取文件: {file_path}")
                return content, encoding
        except UnicodeDecodeError:
            continue
    
    # 如果所有尝试都失败，使用二进制读取并使用UTF-8解码，忽略错误
    if logger:
        logger.warning(f"所有编码尝试失败，使用二进制模式读取: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='replace')
            if logger:
                logger.warning(f"以替代方式读取文件，可能存在字符问题: {file_path}")
            return content, 'utf-8'
    except Exception as e:
        if logger:
            logger.error(f"读取文件时出错: {str(e)}")
        return None, None

def write_file_with_encoding(file_path, content, encoding='utf-8', logger=None):
    """使用指定编码写入文件内容"""
    if logger is None:
        from utils.logger import Logger
        logger = Logger()
    
    try:
        # 使用传入的编码写入文件
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        if logger:
            logger.info(f"成功以 {encoding} 编码写入文件: {file_path}")
        return True
    except Exception as e:
        if logger:
            logger.error(f"以编码 {encoding} 写入文件时出错: {str(e)}")
        
        # 如果写入失败且不是UTF-8，尝试使用UTF-8作为备选
        if encoding.lower() != 'utf-8':
            try:
                if logger:
                    logger.warning(f"尝试使用UTF-8编码作为备选方案")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                if logger:
                    logger.info(f"成功以UTF-8编码写入文件: {file_path}")
                return True
            except Exception as e2:
                if logger:
                    logger.error(f"备选方案也失败了: {str(e2)}")
        
        traceback.print_exc()
        return False

def handle_exception(exc_type, exc_value, exc_tb, logger=logger):
    """统一的异常处理函数"""
    logger.error("异常类型: {}".format(exc_type.__name__))
    logger.error("异常消息: {}".format(str(exc_value)))
    logger.error("异常堆栈:")
    for line in traceback.format_tb(exc_tb):
        logger.error(line.strip())
    logger.error("请报告此错误。") 

def is_path_safe(path):
    """检查路径是否安全可操作"""
    try:
        # 检查路径是否存在
        if not os.path.exists(path):
            return False, "路径不存在"
            
        # 检查是否有读写权限
        if not os.access(path, os.R_OK):
            return False, "没有读取权限"
            
        if os.path.isfile(path) and not os.access(path, os.W_OK):
            return False, "没有写入权限"
            
        # 确保不是系统关键路径
        system_paths = [
            os.path.expanduser("~/"),  # 不允许直接操作用户根目录
            os.environ.get("SystemRoot", "C:\\Windows"),  # Windows系统目录
            os.environ.get("ProgramFiles", "C:\\Program Files"),  # 程序文件目录
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")  # 32位程序文件目录
        ]
        
        for sys_path in system_paths:
            if os.path.abspath(path) == os.path.abspath(sys_path):
                return False, "不能操作系统关键路径"
        
        return True, "路径安全"
    except Exception as e:
        return False, f"检查路径安全性时出错: {str(e)}" 