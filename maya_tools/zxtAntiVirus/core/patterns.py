#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
病毒特征检测模式定义 - 集中管理所有配置和常量
"""

# 白名单文件列表 - 这些文件不会被删除
WHITELIST_FILES = [
    "zxtAntiVirus.py",  # 杀毒工具本身
    "zxtSCNclearUp.py", # 场景清理工具
    "README.md",
    "__init__.py",
    "main.py",
    "cleaner.py",
    "scanner.py",
    "patterns.py",
    "logger.py",
    "common.py",
    "command_executor.py"
]

# 始终可疑的节点名称
ALWAYS_SUSPICIOUS_NODES = [
    "vaccine_gene",
    "breed_gene",  # 添加breed_gene作为已知恶意节点
    "xxx_hacker",
    "maya_exec_spy",
    "fuckVirus_gene",
    "uifiguration"
]

# 兼容性别名
SUSPICIOUS_NODE_NAMES = ALWAYS_SUSPICIOUS_NODES

# 条件可疑的节点名称（需要额外检查）
CONDITIONAL_SUSPICIOUS_NODES = [
    "checker",
    "scriptNode",
    "zScriptNode",
    "sceneConfigurationScriptNode",
    "vaccine",
    "antivirus"
]

# 恶意节点前缀
MALICIOUS_NODE_PREFIXES = [
    "hackerNode",
    "exploit_",
    "rootkit_",
    "malware_",
    "backdoor_"
]

# 可疑代码模式
SUSPICIOUS_CODE_PATTERNS = [
    r"import\s+os\s*;.*?os\.system\(|os\.popen\(",  # 系统命令执行
    r"import\s+subprocess.*?subprocess\.(?:call|Popen|run)\(",  # 子进程执行
    r"eval\s*\(",  # eval执行
    r"exec\s*\(",  # exec执行
    r"__import__\s*\([\"']os[\"']\)",  # 动态导入os
    r"maya\.mel\.eval\(",  # MEL评估
    r"import\s+shutil.*?shutil\.(?:copy|move|rmtree)",  # 文件操作
    r"open\s*\([^)]*?[\"']w[\"']",  # 写入文件
    r"urllib",  # 网络访问
    r"urllib2",  # 网络访问
    r"requests",  # 网络访问
    r"socket\.",  # 网络访问
    r"ftplib",  # FTP访问
    r"importlib",  # 动态导入
    r"base64\..*?decode",  # Base64解码
    r"import\s+sys.*?sys\.path\.(?:append|insert)"  # 修改Python路径
]

# 明确恶意的代码模式（这些直接删除）
MALICIOUS_CODE_PATTERNS = [
    r"os\.remove\s*\([^)]*?userSetup",  # 删除用户启动脚本
    r"os\.rmdir\s*\([^)]*?maya[/\\\\]scripts",  # 删除脚本目录
    r"shutil\.rmtree\s*\([^)]*?maya",  # 删除maya目录
    r"urllib\.request\.urlopen\s*\([^)]*?\.exe",  # 下载可执行文件
    r"while\s+True.*?os\.fork\s*\(",  # 创建无限进程
    r"multiprocessing.*?Process\(.*?daemon=True",  # 后台进程
    r"socket\.[^)]*?connect\([^)]*?\.onion",  # 连接暗网
    r"\"powershell\".*?\"-e",  # 执行PowerShell编码命令
    r"user-agents.*?urllib",  # 伪造用户代理
    r"data\s*=\s*b'.*?'\s*exec\(compile\(",  # 编译执行代码
    r"str\.translate.*?__import__",  # 字符转换混淆后导入
    r"__builtins__\[.*?\]=",  # 修改内置函数
    r"with\s+open\([^)]*?[\"']w[\"']\).*?for\s+root.*?os\.walk",  # 遍历并修改文件
    r"keylogger",  # 键盘记录
    r"mail[tT]o:"  # 可疑的邮件链接
]

# 兼容性别名
SUSPICIOUS_STRING_PATTERNS = SUSPICIOUS_CODE_PATTERNS

# 标准Maya节点类型
STANDARD_NODES = [
    "transform", 
    "mesh", 
    "nurbsCurve", 
    "joint", 
    "camera", 
    "light"
]

# 可疑节点类型
SUSPICIOUS_NODE_TYPES = [
    "script", 
    "unknown"
]

# 标准UI模式
STANDARD_UI_PATTERNS = [
    "defaultNavigation", 
    "defaultOptions", 
    "standardPreferences"
]

# 已知恶意文件
KNOWN_MALICIOUS_FILES = [
    "vaccine.py", 
    "vaccine.pyc", 
    "fuckVirus.py", 
    "fuckVirus.pyc", 
    "antivirus.py", 
    "antivirus.pyc", 
    "av.py", 
    "av.pyc", 
    "phage.py", 
    "phage.pyc", 
    "leukocyte.py", 
    "leukocyte.pyc",
    "userSetup.mel",  # 添加已知恶意启动脚本
    "userSetup.py"    # 添加已知恶意启动脚本
]

# 白名单文件
WHITELISTED_FILES = [
    "zxtSCNclearUp.py"
]

# 病毒签名
VIRUS_SIGNATURES = {
    "breed_gene": {
        "pattern": "createNode script -n \"breed_gene\"",
        "description": "Maya脚本病毒：breed_gene节点"
    },
    "uifiguration": {
        "pattern": "createNode script -n \"uifiguration\"",
        "description": "Maya脚本病毒：uifiguration节点"
    },
    "base64_imports": {
        "pattern": "import base64",
        "description": "可疑的base64编码/解码操作"
    }
}

# Maya用户脚本目录
USER_SCRIPT_DIR = "Documents/maya/scripts"

def get_all_virus_patterns():
    """获取所有病毒检测模式的汇总列表"""
    return {
        'standard_nodes': STANDARD_NODES,
        'malicious_node_prefixes': MALICIOUS_NODE_PREFIXES,
        'suspicious_node_types': SUSPICIOUS_NODE_TYPES,
        'suspicious_node_names': CONDITIONAL_SUSPICIOUS_NODES,
        'malicious_code_patterns': SUSPICIOUS_CODE_PATTERNS,
        'standard_ui_patterns': STANDARD_UI_PATTERNS,
        'known_malicious_files': KNOWN_MALICIOUS_FILES,
        'whitelisted_files': WHITELISTED_FILES,
        'virus_signatures': VIRUS_SIGNATURES
    } 