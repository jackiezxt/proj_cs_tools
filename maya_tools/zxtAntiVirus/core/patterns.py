#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
病毒特征检测模式定义
"""

# 已知恶意节点名称（总是清理）
ALWAYS_SUSPICIOUS_NODES = [
    "breed_gene", 
    "uifiguration"
]

# 为了兼容性，添加旧的变量名
SUSPICIOUS_NODE_NAMES = ALWAYS_SUSPICIOUS_NODES

# 条件判断的脚本节点（需要检查内容）
CONDITIONAL_SUSPICIOUS_NODES = [
    "uiConfigurationScriptNode", 
    "sceneConfigurationScriptNode"
]

# 恶意节点名称前缀
MALICIOUS_NODE_PREFIXES = [
    "breed",
    "vacc", 
    "fuckVirus", 
    "uifigur", 
    "phage", 
    "leukocyte"
]

# 恶意代码模式
SUSPICIOUS_CODE_PATTERNS = [
    "eval(", 
    "exec(", 
    "import os", 
    "import sys", 
    "subprocess", 
    "writeFile", 
    "python.exe", 
    "powershell", 
    "cmd.exe", 
    "http://", 
    "https://", 
    "ftp://", 
    "socket", 
    "connect(",
    "import base64", 
    "base64.b64decode", 
    "base64.decode"
]

# 兼容性别名
MALICIOUS_CODE_PATTERNS = SUSPICIOUS_CODE_PATTERNS
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
    "leukocyte.pyc"
]

# 白名单文件
WHITELISTED_FILES = [
    "userSetup_backup.py", 
    "userSetup_clean.py", 
    "__init__.py", 
    "readme.txt"
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