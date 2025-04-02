#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
病毒扫描器模块
负责扫描和检测Maya文件中的恶意代码
"""
import os
import re
import base64
import traceback
from utils.logger import Logger
from utils.common import (
    check_if_file_in_whitelist,
    is_maya_ascii_file,
    is_maya_binary_file,
    get_script_node_content,
    get_script_node_name,
    get_maya_user_script_dir,
    normalize_path,
    read_file_with_encoding,
    is_path_safe
)
from core.patterns import (
    ALWAYS_SUSPICIOUS_NODES,
    CONDITIONAL_SUSPICIOUS_NODES,
    MALICIOUS_NODE_PREFIXES,
    SUSPICIOUS_CODE_PATTERNS,
    MALICIOUS_CODE_PATTERNS,
    KNOWN_MALICIOUS_FILES,
    WHITELISTED_FILES,
    VIRUS_SIGNATURES
)

class VirusScanner:
    """Maya病毒扫描器"""
    
    def __init__(self, log_path=None):
        """初始化扫描器"""
        self.logger = Logger(log_path) if log_path else Logger()
        
        # 导入恶意代码模式
        self.suspicious_nodes = ALWAYS_SUSPICIOUS_NODES
        self.conditional_suspicious_nodes = CONDITIONAL_SUSPICIOUS_NODES
        self.malicious_node_prefixes = MALICIOUS_NODE_PREFIXES
        self.suspicious_code_patterns = SUSPICIOUS_CODE_PATTERNS
        self.malicious_code_patterns = MALICIOUS_CODE_PATTERNS
        self.known_malicious_files = KNOWN_MALICIOUS_FILES
        
        # 扫描结果
        self.results = {
            "infected_files": [],
            "cleaned_files": [],
            "failed_files": [],
            "summary": {}
        }
        self.virus_count = 0
        self.stop_requested = False
    
    def is_suspicious_code(self, content):
        """检查代码是否包含可疑内容"""
        if not content:
            return False
            
        # 检查可疑代码模式
        for pattern in self.suspicious_code_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
                
        # 检查明确恶意的代码
        for pattern in self.malicious_code_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
                
        return False
    
    def scan_file(self, file_path):
        """扫描单个文件是否包含恶意代码"""
        self.logger.info("开始扫描文件: {}".format(file_path))
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.logger.error("文件不存在: {}".format(file_path))
            return {"infected_files": [], "error": "文件不存在"}
        
        # 检查文件类型
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # 初始化结果
        results = {
            "file_path": file_path,
            "file": file_path,  # 确保同时包含file和file_path字段
            "infected": False,
            "suspicious_nodes": [],
            "suspicious_code": [],
            "error": None
        }
        
        # 检查是否是已知恶意文件名
        if file_name.lower() in [name.lower() for name in self.known_malicious_files]:
            self.logger.warning("发现已知恶意文件: {}".format(file_path))
            results["infected"] = True
            results["malicious_file"] = True
            self.results["infected_files"].append(results)
            self.virus_count += 1
            return {"infected_files": [results]}
        
        # 对于Python和MEL脚本文件，直接检查内容
        if file_ext in ['.py', '.mel']:
            content, encoding = read_file_with_encoding(file_path, self.logger)
            if content is None:
                self.logger.error(f"无法读取文件: {file_path}")
                results["error"] = "无法读取文件"
                self.results["failed_files"].append(results)
                return {"infected_files": [], "failed_files": [results]}
            
            if self.is_suspicious_code(content):
                self.logger.warning("发现包含可疑代码的脚本文件: {}".format(file_path))
                results["infected"] = True
                results["suspicious_code"].append({
                    "type": "script_file",
                    "file": file_path
                })
                self.results["infected_files"].append(results)
                self.virus_count += 1
                return {"infected_files": [results]}
            
            self.logger.info("文件正常: {}".format(file_path))
            return {"infected_files": []}
        
        # 对于Maya ASCII文件
        elif is_maya_ascii_file(file_path):
            try:
                # 读取文件
                content, encoding = read_file_with_encoding(file_path, self.logger)
                if content is None:
                    self.logger.error(f"无法读取Maya文件: {file_path}")
                    results["error"] = "无法读取Maya文件"
                    self.results["failed_files"].append(results)
                    return {"infected_files": [], "failed_files": [results]}
                
                # 保存检测到的编码信息到结果中，供后续清理时使用
                results["detected_encoding"] = encoding
                self.logger.info(f"文件编码: {encoding}")
                
                # 先检查文件内容中的已知病毒签名
                for virus_name, signature_info in VIRUS_SIGNATURES.items():
                    pattern = signature_info.get("pattern")
                    if pattern and pattern in content:
                        self.logger.warning(f"文件中直接发现病毒签名: {virus_name} - {signature_info.get('description')}")
                        # 创建一个对应的可疑节点记录
                        results["infected"] = True
                        results["suspicious_nodes"].append({
                            "name": virus_name,
                            "suspicious_name": True,
                            "suspicious_content": True,
                            "description": signature_info.get("description")
                        })
                        self.virus_count += 1
                
                # 提取所有脚本节点
                script_nodes = []
                for match in re.finditer(r'createNode\s+script\s+-n\s+"([^"]+)"', content):
                    node_name = match.group(1)
                    # 找到节点的内容范围
                    node_start = match.start()
                    # 找到节点结束位置（下一个节点开始或文件结束）
                    next_node = re.search(r'createNode\s+\w+\s+-n', content[node_start + len(match.group(0)):])
                    if next_node:
                        node_end = node_start + len(match.group(0)) + next_node.start()
                    else:
                        node_end = len(content)
                    
                    node_content = content[node_start:node_end]
                    script_nodes.append((node_name, node_content))
                
                # 检查每个脚本节点
                for node_name, node_content in script_nodes:
                    # 提取脚本代码
                    code = get_script_node_content(node_content, self.logger)
                    
                    # 检查节点名称是否可疑 - 先检查已知恶意节点列表
                    is_suspicious_name = False
                    
                    # 直接匹配已知恶意节点名称
                    if node_name in self.suspicious_nodes:
                        is_suspicious_name = True
                        self.logger.warning("发现已知恶意节点: {}，该节点将被清理".format(node_name))
                    else:
                        # 检查恶意节点前缀
                        for prefix in self.malicious_node_prefixes:
                            if prefix.lower() in node_name.lower():
                                is_suspicious_name = True
                                self.logger.warning("发现前缀可疑的脚本节点: {}".format(node_name))
                                break
                    
                    # 检查节点内容是否可疑 - 只有当节点名称不在已知恶意列表时才需要检查内容
                    is_suspicious_content = False
                    if not is_suspicious_name and node_name in self.conditional_suspicious_nodes:
                        # 只检查条件可疑节点的内容
                        is_suspicious_content = self.is_suspicious_code(code) if code else False
                        if is_suspicious_content:
                            self.logger.warning("节点 {} 包含可疑代码，需要清理".format(node_name))
                    
                    # 如果节点名称或内容可疑，标记为感染
                    if is_suspicious_name or is_suspicious_content:
                        results["infected"] = True
                        results["suspicious_nodes"].append({
                            "name": node_name,
                            "suspicious_name": is_suspicious_name,
                            "suspicious_content": is_suspicious_content,
                            "is_always_suspicious": node_name in self.suspicious_nodes
                        })
                        self.virus_count += 1
                
                if results["infected"]:
                    self.logger.warning("文件包含可疑节点: {}".format(file_path))
                    self.results["infected_files"].append(results)
                    return {"infected_files": [results]}
                else:
                    self.logger.info("文件不含可疑节点: {}".format(file_path))
                    return {"infected_files": []}
                
            except Exception as e:
                self.logger.error("扫描Maya文件时出错: {} - {}".format(file_path, str(e)))
                self.logger.error(traceback.format_exc())
                results["error"] = str(e)
                self.results["failed_files"].append(results)
                return {"infected_files": [], "failed_files": [results]}
        
        # 对于其他类型文件，暂不处理
        else:
            self.logger.info("跳过不支持的文件类型: {}".format(file_path))
            return {"infected_files": []}
    
    def scan_directory(self, dir_path, recursive=True, max_depth=5, current_depth=0):
        """扫描目录中的所有Maya和脚本文件"""
        self.logger.info("开始扫描目录: {} (深度: {})".format(dir_path, current_depth))
        
        results = {
            "infected_files": [],
            "failed_files": []
        }
        
        # 检查目录是否存在
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            self.logger.error("目录不存在: {}".format(dir_path))
            return results
        
        # 检查是否达到最大深度
        if current_depth > max_depth:
            self.logger.warning("已达到最大扫描深度: {}".format(dir_path))
            return results
        
        # 确保目录路径安全可访问
        is_safe, reason = is_path_safe(dir_path)
        if not is_safe:
            self.logger.warning(f"跳过不安全的目录: {dir_path} - {reason}")
            return results
        
        try:
            # 遍历目录中的所有文件
            for item in os.listdir(dir_path):
                # 检查是否请求停止
                if self.stop_requested:
                    self.logger.info("扫描已停止")
                    break
                
                item_path = os.path.join(dir_path, item)
                
                # 如果是目录且允许递归，则递归扫描
                if os.path.isdir(item_path) and recursive:
                    # 跳过特定的系统目录
                    if item.startswith('.') or item in ["node_modules", "venv", "env", "cache"]:
                        continue
                    
                    # 递归扫描子目录
                    sub_results = self.scan_directory(item_path, recursive, max_depth, current_depth + 1)
                    results["infected_files"].extend(sub_results["infected_files"])
                    results["failed_files"].extend(sub_results["failed_files"])
                
                # 如果是文件，则根据文件类型进行扫描
                elif os.path.isfile(item_path):
                    # 只扫描Maya文件和脚本文件
                    if item.lower().endswith(('.ma', '.mb', '.py', '.mel')):
                        # 跳过白名单文件
                        if check_if_file_in_whitelist(item):
                            self.logger.info("跳过白名单文件: {}".format(item_path))
                            continue
                        
                        # 扫描文件
                        file_results = self.scan_file(item_path)
                        
                        # 确保每个infected_file结果同时包含file和file_path字段
                        for file_info in file_results.get("infected_files", []):
                            if "file_path" in file_info and "file" not in file_info:
                                file_info["file"] = file_info["file_path"]
                            elif "file" in file_info and "file_path" not in file_info:
                                file_info["file_path"] = file_info["file"]
                        
                        results["infected_files"].extend(file_results.get("infected_files", []))
                        results["failed_files"].extend(file_results.get("failed_files", []))
        
        except Exception as e:
            self.logger.error("扫描目录时出错: {} - {}".format(dir_path, str(e)))
            self.logger.error(traceback.format_exc())
            results["failed_files"].append({
                "path": dir_path,
                "error": str(e)
            })
        
        self.logger.info("目录扫描完成: {} - 发现 {} 个感染文件".format(dir_path, len(results["infected_files"])))
        return results
    
    def scan_maya_scripts_directory(self):
        """专门扫描Maya脚本目录"""
        self.logger.info("开始扫描Maya脚本目录")
        
        # 获取Maya用户脚本目录（只扫描我的文档/maya/scripts）
        scripts_dir = get_maya_user_script_dir()
        
        if not os.path.exists(scripts_dir):
            self.logger.warning("Maya脚本目录不存在: {}".format(scripts_dir))
            return {"infected_files": []}
        
        # 不递归扫描，只扫描当前目录中的文件
        return self.scan_directory(scripts_dir, recursive=False)
    
    def scan_all(self):
        """扫描所有相关目录"""
        self.logger.info("开始全面扫描")
        
        # 存储所有结果
        all_results = {
            "infected_files": [],
            "failed_files": [],
            "summary": {}
        }
        
        # 1. 扫描Maya脚本目录
        scripts_results = self.scan_maya_scripts_directory()
        all_results["infected_files"].extend(scripts_results.get("infected_files", []))
        all_results["failed_files"].extend(scripts_results.get("failed_files", []))
        
        # 2. 可以添加其他目录的扫描
        # ...
        
        # 更新扫描摘要
        all_results["summary"] = {
            "total_scanned": len(all_results["infected_files"]) + len(all_results["failed_files"]),
            "infected_count": len(all_results["infected_files"]),
            "failed_count": len(all_results["failed_files"]),
            "virus_count": self.virus_count
        }
        
        self.results = all_results
        self.logger.info("全面扫描完成。检测到 {} 个感染文件".format(len(all_results["infected_files"])))
        
        return all_results
    
    def stop_scan(self):
        """停止扫描过程"""
        self.logger.info("收到停止扫描请求")
        self.stop_requested = True 