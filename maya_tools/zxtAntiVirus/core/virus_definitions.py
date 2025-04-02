#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
病毒定义模块 - 包含已知的Maya恶意代码类型和特征
"""

# 病毒类型定义
VIRUS_TYPES = {
    "XDFilm": {
        "description": "一种常见的Maya病毒，通常通过scriptNode节点植入场景文件，并在Maya启动或保存文件时执行，会在用户的Maya目录中植入启动脚本。",
        "characteristics": [
            "创建带有uifiguration名称的scriptNode节点",
            "使用base64编码隐藏恶意代码",
            "在maya用户目录下创建启动脚本",
            "在场景保存时自动传播",
            "创建SceneSaved事件触发器",
            "修改userSetup.mel和userSetup.py"
        ],
        "detection_nodes": [
            "uifiguration", 
            "uiConfigurationScriptNode"
        ],
        "impact": "高 - 会感染所有场景文件，植入启动代码，甚至可能导致文件丢失。"
    },
    "MayaBreeder": {
        "description": "一种自我复制型Maya病毒，使用'vaccine'、'breed'或类似名称，通过scriptNode节点复制并感染场景文件。",
        "characteristics": [
            "创建名称包含'vaccine'或'breed'的scriptNode节点",
            "使用函数如'breed()'或'antivirus()'（讽刺性命名）",
            "在场景保存或打开时自动传播",
            "创建SceneSaved或SceneOpened事件触发器"
        ],
        "detection_nodes": [
            "vaccine", 
            "ScriptNode", 
            "userobject"
        ],
        "impact": "中 - 主要感染场景文件，但一般不会造成系统级损害。"
    },
    "MayaBotnet": {
        "description": "高级Maya恶意代码，可能尝试连接远程服务器，执行远程命令或窃取用户信息。",
        "characteristics": [
            "包含网络连接代码（socket, urllib等）",
            "尝试访问外部URL或IP地址",
            "隐蔽地执行系统命令",
            "使用高级编码和混淆技术"
        ],
        "detection_nodes": [
            "scriptNode名称可能很随机"
        ],
        "impact": "严重 - 可能导致信息泄露或远程命令执行。"
    },
    "AutoScriptRunner": {
        "description": "在Maya场景文件中自动执行代码的恶意脚本，通常使用scriptJob机制确保持久性。",
        "characteristics": [
            "使用scriptJob绑定Maya事件",
            "通常附加到SceneOpened或idle事件",
            "可能包含自删除或反检测代码",
            "修改Maya启动文件路径"
        ],
        "detection_nodes": [
            "autoRun", 
            "scriptNodeAutoRun", 
            "runnerNode"
        ],
        "impact": "中 - 会在打开文件时执行代码，但范围有限。"
    },
    "PersistenceVirus": {
        "description": "专注于实现持久性的Maya恶意代码，通过修改启动文件如userSetup.py或userSetup.mel确保持久存在。",
        "characteristics": [
            "修改或创建userSetup文件",
            "可能修改Maya配置文件",
            "使用多种机制确保重启后仍然存在",
            "可能隐藏自身文件或进程"
        ],
        "detection_nodes": [
            "startupScript", 
            "persistentNode", 
            "initializerNode"
        ],
        "impact": "高 - 难以完全清除，会在每次启动Maya时执行。"
    }
}

# XDFilm病毒的特征代码片段
XDFILM_CODE_SIGNATURES = [
    "uifiguration",
    "import base64; _pycode = base64.urlsafe_b64decode",
    "scriptJob(event=[\"SceneSaved\", \"execute()",
    "os.getenv(\"APPDATA\")+base64.urlsafe_b64decode", 
    "KGMScriptProtector",
    "addAttr -ci true -sn \"nts\" -ln \"notes\" -dt \"string\"",
    "python(\"import base64; _pycode = base64.urlsafe_b64decode",
    "os.chmod( usepypath, stat.S_IWRITE )",
    "maya/scripts/userSetup"
]

# MayaBreeder病毒的特征代码片段
MAYABREEDER_CODE_SIGNATURES = [
    "class phage:",
    "def antivirus(self):",
    "def occupation(self):", 
    "leukocyte = phage()",
    "leukocyte.occupation()",
    "cmds.scriptJob(event=[\"SceneSaved\"",
    "import vaccine",
    "vaccine.phage()"
]

# 自动执行脚本节点的特征代码片段
AUTO_SCRIPT_SIGNATURES = [
    "ScriptNode.setAttr(\".st\", 1)",
    "scriptNode -n",
    "scriptJob(event=",
    "createNode script -n",
    "setAttr \".b\" -type \"string\"",
    "setAttr \".st\" 1"
]

# 网络连接相关的可疑代码片段
NETWORK_CODE_SIGNATURES = [
    "socket.connect",
    "urllib",
    "requests.get",
    "requests.post",
    "http://",
    "https://"
]

# 文件操作相关的可疑代码片段
FILE_OPERATION_SIGNATURES = [
    "os.remove",
    "open(",
    "write(",
    "with open(",
    "os.path.join(cmds.internalVar(userAppDir=True)",
    "shutil.copy",
    "shutil.move"
]

# 系统操作相关的可疑代码片段
SYSTEM_OPERATION_SIGNATURES = [
    "os.system", 
    "subprocess.call",
    "subprocess.Popen",
    "exec(",
    "eval(",
    "platform.system"
]

# 编码/混淆技术的可疑代码片段
OBFUSCATION_SIGNATURES = [
    "base64.b64decode",
    "base64.b64encode",
    "base64.urlsafe_b64decode",
    "str.encode",
    "bytes.decode",
    "lambda",
    "exec(eval"
]

# 已知的安全的scriptNode节点名称
KNOWN_SAFE_NODES = [
    "sceneConfigurationScriptNode", 
    "uiConfigurationScriptNode"
]

def get_virus_definitions():
    """返回所有病毒定义数据"""
    return {
        "virus_types": VIRUS_TYPES,
        "xdfilm_signatures": XDFILM_CODE_SIGNATURES,
        "mayabreeder_signatures": MAYABREEDER_CODE_SIGNATURES,
        "auto_script_signatures": AUTO_SCRIPT_SIGNATURES,
        "network_signatures": NETWORK_CODE_SIGNATURES,
        "file_operation_signatures": FILE_OPERATION_SIGNATURES,
        "system_operation_signatures": SYSTEM_OPERATION_SIGNATURES,
        "obfuscation_signatures": OBFUSCATION_SIGNATURES,
        "known_safe_nodes": KNOWN_SAFE_NODES
    }

def get_virus_type_names():
    """返回所有病毒类型名称列表"""
    return list(VIRUS_TYPES.keys())

def get_virus_description(virus_type):
    """根据病毒类型名称返回其描述"""
    if virus_type in VIRUS_TYPES:
        return VIRUS_TYPES[virus_type]["description"]
    return "未知病毒类型"

def get_virus_impact(virus_type):
    """根据病毒类型名称返回其影响程度"""
    if virus_type in VIRUS_TYPES:
        return VIRUS_TYPES[virus_type]["impact"]
    return "未知" 