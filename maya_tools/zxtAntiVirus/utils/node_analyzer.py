# -*- coding: utf-8 -*-
"""
脚本节点分析模块
提供共享的节点分析函数，被扫描器和清理器共同使用
"""
import re
from utils.common import get_script_node_name, get_script_node_content
from core.patterns import (
    STANDARD_NODES,
    MALICIOUS_NODE_PREFIXES,
    MALICIOUS_CODE_PATTERNS,
    STANDARD_UI_PATTERNS
)

def analyze_script_node(script_block, logger=None):
    """分析脚本节点，判断是否包含恶意代码
    
    Args:
        script_block (str): 脚本节点文本块
        logger: 可选的日志记录器
    
    Returns:
        dict: 包含节点分析结果的字典
    """
    result = {
        "node_name": None,
        "is_standard_node": False,
        "has_malicious_prefix": False,
        "has_malicious_code": False,
        "malicious_pattern_found": None,
        "should_clean": False,
        "reason": None
    }
    
    # 提取节点名称
    node_name = get_script_node_name(script_block, logger)
    if not node_name:
        return result
    
    result["node_name"] = node_name
    
    # 检查是否为标准节点
    result["is_standard_node"] = node_name in STANDARD_NODES
    
    # 检查节点前缀是否恶意
    for prefix in MALICIOUS_NODE_PREFIXES:
        if node_name.lower().startswith(prefix.lower()):
            result["has_malicious_prefix"] = True
            result["reason"] = f"恶意节点名称前缀: {prefix}"
            if logger:
                logger.warning(f"节点 {node_name} 含有恶意前缀: {prefix}")
            break
    
    # 提取脚本内容
    code = get_script_node_content(script_block, logger)
    if not code:
        # 无法提取内容，根据前缀判断
        result["should_clean"] = result["has_malicious_prefix"]
        return result
    
    # 检查代码内容是否恶意
    for pattern in MALICIOUS_CODE_PATTERNS:
        if pattern in code:
            # 对于标准节点，进一步验证是否为正常UI代码
            if result["is_standard_node"]:
                # 检查是否包含正常UI配置模式
                is_normal_ui_code = False
                for ui_pattern in STANDARD_UI_PATTERNS:
                    if ui_pattern in code:
                        is_normal_ui_code = True
                        break
                
                # 对于可能的假阳性，继续检查
                if is_normal_ui_code:
                    continue
            
            result["has_malicious_code"] = True
            result["malicious_pattern_found"] = pattern
            if not result["reason"]:
                result["reason"] = f"包含恶意代码特征: {pattern}"
            if logger:
                logger.warning(f"节点 {node_name} 包含恶意代码特征: {pattern}")
            break
    
    # 决定是否清理节点
    if result["is_standard_node"]:
        # 标准节点的判断逻辑
        if node_name == "sceneConfigurationScriptNode" and "playbackOptions" in code and len(code) < 100:
            # 场景配置节点通常包含这些内容，是安全的
            result["should_clean"] = False
            if logger:
                logger.info(f"保留标准场景配置节点: {node_name}")
        elif node_name == "uiConfigurationScriptNode" and any(ui_pattern in code for ui_pattern in STANDARD_UI_PATTERNS):
            # UI配置节点通常包含这些内容，是安全的
            result["should_clean"] = False
            if logger:
                logger.info(f"保留标准UI配置节点: {node_name}")
        elif result["has_malicious_code"]:
            # 标准节点包含恶意代码，需要清理
            result["should_clean"] = True
            if logger:
                logger.warning(f"标准节点 {node_name} 包含恶意代码，将被清理")
        else:
            # 其他情况，保留标准节点
            result["should_clean"] = False
            if logger:
                logger.info(f"保留正常标准节点: {node_name}")
    else:
        # 非标准节点的判断逻辑
        result["should_clean"] = result["has_malicious_prefix"] or result["has_malicious_code"]
        if result["should_clean"] and logger:
            logger.warning(f"发现需要清理的节点: {node_name}, 原因: {result['reason']}")
    
    return result

def extract_script_blocks(file_content):
    """从文件内容中提取所有脚本节点块
    
    Args:
        file_content (str): 文件的完整内容
    
    Returns:
        list: 包含所有脚本节点块的列表
    """
    script_blocks = []
    
    # 查找所有createNode script开头的块
    start_indices = [m.start() for m in re.finditer(r'createNode\s+script\s+-n', file_content)]
    
    for i, start_idx in enumerate(start_indices):
        # 确定当前块的结束位置
        if i < len(start_indices) - 1:
            # 如果不是最后一个块，则到下一个块的开始
            end_idx = start_indices[i + 1]
        else:
            # 如果是最后一个块，则找到下一个createNode
            next_node = file_content.find("createNode", start_idx + 15)
            if next_node == -1:
                # 没有下一个节点，到文件末尾
                end_idx = len(file_content)
            else:
                end_idx = next_node
        
        # 提取脚本块
        script_block = file_content[start_idx:end_idx]
        script_blocks.append(script_block)
    
    return script_blocks

def process_maya_file(file_content, callback_func, logger=None):
    """处理Maya文件内容
    
    Args:
        file_content (str): 文件内容
        callback_func (callable): 回调函数，参数为提取的脚本块，返回处理后的块或None（删除）
        logger (Logger): 可选的日志记录器
    
    Returns:
        tuple: (processed_content, processed_blocks)
            processed_content (str): 处理后的文件内容
            processed_blocks (list): 处理过的块列表
    """
    # 提取所有脚本块
    script_blocks = extract_script_blocks(file_content)
    
    # 如果没有脚本块，直接返回原内容
    if not script_blocks:
        if logger:
            logger.info("文件中没有发现脚本节点")
        return file_content, []
    
    # 处理后的块列表
    processed_blocks = []
    
    # 处理每个脚本块
    for block in script_blocks:
        # 获取节点名称用于日志
        node_name = get_script_node_name(block, logger)
        
        # 调用回调函数处理块
        processed_block = callback_func(block)
        
        # 如果返回None，表示删除该块
        if processed_block is None:
            if logger and node_name:
                logger.info(f"删除脚本节点: {node_name}")
            processed_blocks.append((node_name, None))
        else:
            processed_blocks.append((node_name, processed_block))
    
    # 重建文件内容
    result_content = file_content
    
    # 从后向前替换，避免索引错位
    for i in range(len(script_blocks) - 1, -1, -1):
        original_block = script_blocks[i]
        node_name, new_block = processed_blocks[i]
        
        # 如果new_block是None，删除该块
        if new_block is None:
            block_start = result_content.find(original_block)
            if block_start != -1:
                block_end = block_start + len(original_block)
                result_content = result_content[:block_start] + result_content[block_end:]
                if logger:
                    logger.info(f"已从文件中删除节点: {node_name}")
    
    return result_content, processed_blocks 