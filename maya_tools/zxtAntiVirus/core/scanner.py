# -*- coding: utf-8 -*-
"""
扫描器核心模块
负责检测Maya文件中的恶意代码和已知病毒
"""
import os
import re
import json
import datetime
import traceback
from utils.logger import Logger
from utils.common import (
    get_maya_user_dirs,
    check_if_file_in_whitelist,
    decode_base64_content,
    is_maya_ascii_file,
    is_maya_binary_file,
    get_script_node_content,
    get_script_node_name
)
from core.patterns import (
    STANDARD_NODES,
    MALICIOUS_NODE_PREFIXES,
    SUSPICIOUS_NODE_TYPES,
    SUSPICIOUS_NODE_NAMES,
    MALICIOUS_CODE_PATTERNS,
    STANDARD_UI_PATTERNS,
    KNOWN_MALICIOUS_FILES,
    SUSPICIOUS_CODE_PATTERNS,
    SUSPICIOUS_STRING_PATTERNS,
    VIRUS_SIGNATURES,
    get_all_virus_patterns
)
from utils.node_analyzer import extract_script_blocks, analyze_script_node

class VirusScanner:
    """Maya文件病毒扫描器"""
    
    def __init__(self, log_path=None):
        """初始化扫描器"""
        self.logger = Logger(log_path)
        self.logger.info("初始化病毒扫描器")
        self.results = {
            "suspicious_nodes": [],
            "suspicious_code": [],
            "infected_files": [],
            "summary": {}
        }
        self.stop_requested = False
        
        # 加载已知的恶意代码模式
        self.virus_patterns = {
            'malicious_code_patterns': MALICIOUS_CODE_PATTERNS,
            'suspicious_code_patterns': SUSPICIOUS_CODE_PATTERNS,
            'virus_signatures': VIRUS_SIGNATURES
        }
    
    def scan_file(self, file_path):
        """扫描单个Maya文件"""
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return None
        
        # 重置结果
        self.results = {
            "suspicious_nodes": [],
            "suspicious_code": [],
            "infected_files": [],
            "summary": {}
        }
        
        try:
            self.logger.info(f"开始扫描文件: {file_path}")
            
            # 检查文件扩展名
            if not file_path.lower().endswith(('.ma', '.mb')):
                self.logger.warning(f"不是Maya文件: {file_path}")
                return None
            
            # 对于ASCII文件(.ma)，直接扫描文本内容
            if file_path.lower().endswith('.ma'):
                return self._scan_ma_file(file_path)
            
            # 对于二进制文件(.mb)，需要使用Maya API进行处理
            # 但在不能打开Maya的情况下，我们尝试在二进制文件中寻找文本片段
            return self._scan_mb_file(file_path)
        
        except Exception as e:
            self.logger.error(f"扫描文件时出错: {str(e)}")
            return None
    
    def _scan_ma_file(self, file_path):
        """扫描ASCII格式的Maya文件，重点检查script节点内容"""
        try:
            infected = False
            
            # 快速判断：先检查文件大小
            file_size = os.path.getsize(file_path)
            
            # 检查是否在白名单中
            if check_if_file_in_whitelist(file_path):
                self.logger.info(f"跳过白名单文件: {file_path}")
                return {
                    "file": file_path,
                    "suspicious_nodes": [],
                    "suspicious_code": [],
                    "summary": {
                        "scanned": True,
                        "infected": False,
                        "whitelisted": True
                    }
                }
            
            self.logger.info(f"扫描文件: {file_path} ({file_size/1024/1024:.2f} MB)")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 使用公共函数提取脚本块
            script_blocks = extract_script_blocks(content)
            
            # 如果没有找到script节点，直接返回
            if not script_blocks:
                return {
                    "file": file_path,
                    "suspicious_nodes": [],
                    "suspicious_code": [],
                    "summary": {
                        "scanned": True,
                        "infected": False
                    }
                }
            
            # 检查每个脚本块
            for block in script_blocks:
                # 使用分析器分析脚本节点
                analysis = analyze_script_node(block, self.logger)
                
                if analysis["node_name"] is None:
                    continue
                
                # 记录可疑节点
                if analysis["has_malicious_prefix"] or analysis["has_malicious_code"]:
                    if analysis["has_malicious_prefix"]:
                        self.results["suspicious_nodes"].append({
                            "name": analysis["node_name"],
                            "reason": analysis["reason"],
                            "file": file_path
                        })
                    
                    if analysis["has_malicious_code"]:
                        self.results["suspicious_code"].append({
                            "pattern": analysis["malicious_pattern_found"] or "未知恶意模式",
                            "file": file_path
                        })
                    
                    infected = True
                    self.logger.warning(f"发现可疑节点: {analysis['node_name']}, 原因: {analysis['reason']}")
            
            if infected:
                self.results["infected_files"].append(file_path)
                self.logger.warning(f"文件被标记为已感染: {file_path}")
            else:
                self.logger.info(f"文件未检测到病毒: {file_path}")
            
            # 更新扫描摘要
            self.results["summary"] = {
                "file": file_path,
                "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "infected": infected,
                "suspicious_nodes_count": len(self.results["suspicious_nodes"]),
                "suspicious_code_count": len(self.results["suspicious_code"])
            }
            
            return self.results
        
        except Exception as e:
            self.logger.error(f"扫描ASCII文件时出错: {str(e)}")
            import traceback
            self.logger.error(f"详细错误: {traceback.format_exc()}")
            return None
    
    def _scan_mb_file(self, file_path):
        """扫描二进制格式的Maya文件
        注意：这个函数仅进行有限的文本模式匹配，对二进制文件的检查不如对ASCII文件全面
        """
        try:
            infected = False
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 将二进制内容转换为文本进行简单扫描
            text_content = content.decode('latin-1')  # 使用latin-1避免解码错误
            
            # 检查可疑节点名称
            for node_name in STANDARD_NODES:
                if node_name in text_content:
                    self.results["suspicious_nodes"].append({
                        "name": f"检测到可疑节点名称: {node_name}",
                        "file": file_path
                    })
                    infected = True
            
            # 检查可疑代码模式
            for pattern in MALICIOUS_CODE_PATTERNS:
                if re.search(pattern, text_content):
                    self.results["suspicious_code"].append({
                        "pattern": str(pattern),
                        "file": file_path
                    })
                    infected = True
            
            # 检查可疑字符串模式
            for pattern in STANDARD_UI_PATTERNS:
                if re.search(pattern, text_content):
                    self.results["suspicious_code"].append({
                        "pattern": f"可疑字符串: {str(pattern)}",
                        "file": file_path
                    })
                    infected = True
            
            # 检查病毒特征
            for virus_name, patterns in VIRUS_SIGNATURES.items():
                for pattern in patterns:
                    if re.search(pattern, text_content):
                        self.results["suspicious_code"].append({
                            "pattern": f"已知病毒: {virus_name}",
                            "file": file_path
                        })
                        infected = True
                        break
                if infected:
                    break
            
            if infected:
                self.results["infected_files"].append(file_path)
            
            # 更新扫描摘要
            self.results["summary"] = {
                "file": file_path,
                "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "infected": infected,
                "suspicious_nodes_count": len(self.results["suspicious_nodes"]),
                "suspicious_code_count": len(self.results["suspicious_code"]),
                "warning": "二进制文件扫描可能不完整，建议转换为ASCII格式后再扫描"
            }
            
            return self.results
        
        except Exception as e:
            self.logger.error(f"扫描MB文件时出错: {str(e)}")
            return None
    
    def scan_folder(self, folder_path, recursive=True):
        """扫描文件夹中的所有Maya文件"""
        if not os.path.exists(folder_path):
            self.logger.error(f"文件夹不存在: {folder_path}")
            return None
        
        results = {
            "folder": folder_path,
            "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_scanned": 0,
            "files_infected": 0,
            "infected_files": []
        }
        
        try:
            self.logger.info(f"开始扫描文件夹: {folder_path}")
            start_time = datetime.datetime.now()
            files_to_scan = []
            
            # 首先快速收集所有需要扫描的文件路径
            for root, dirs, files in os.walk(folder_path):
                # 检查是否请求停止
                if self.stop_requested:
                    self.logger.info("扫描已停止")
                    break
                
                # 跳过隐藏目录
                if os.path.basename(root).startswith('.'):
                    dirs[:] = []  # 清空子目录列表
                    continue
                
                # 收集所有Maya文件
                for file in files:
                    if file.lower().endswith(('.ma', '.mb')):
                        file_path = os.path.join(root, file)
                        files_to_scan.append(file_path)
                
                # 如果不递归扫描子文件夹，则清空dirs列表
                if not recursive:
                    dirs[:] = []
            
            # 显示要扫描的文件数量
            total_files = len(files_to_scan)
            self.logger.info(f"找到 {total_files} 个Maya文件待扫描")
            
            # 执行扫描
            for i, file_path in enumerate(files_to_scan):
                # 检查是否请求停止
                if self.stop_requested:
                    self.logger.info("扫描已停止")
                    break
                
                # 每10个文件显示一次进度
                if i % 10 == 0 or i == total_files - 1:
                    progress = ((i + 1) / total_files) * 100
                    elapsed = (datetime.datetime.now() - start_time).total_seconds()
                    self.logger.info(f"扫描进度: {progress:.1f}% ({i+1}/{total_files}), 已用时间: {elapsed:.1f}秒")
                
                file_result = self.scan_file(file_path)
                results["files_scanned"] += 1
                
                if file_result and file_result["summary"].get("infected", False):
                    results["files_infected"] += 1
                    results["infected_files"].append({
                        "file": file_path,
                        "suspicious_nodes": file_result.get("suspicious_nodes", []),
                        "suspicious_code": file_result.get("suspicious_code", [])
                    })
            
            # 完成扫描，计算总时间
            end_time = datetime.datetime.now()
            total_time = (end_time - start_time).total_seconds()
            results["total_time"] = total_time
            self.logger.info(f"扫描完成，共耗时 {total_time:.1f} 秒，扫描了 {results['files_scanned']} 个文件，发现 {results['files_infected']} 个感染文件")
            
            return results
        
        except Exception as e:
            self.logger.error(f"扫描文件夹时出错: {str(e)}")
            return None
    
    def scan_system_startup_scripts(self):
        """扫描系统的Maya启动脚本，只限于文档下的scripts文件夹"""
        results = {
            "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "infected_files": []
        }
        
        # 获取Maya用户目录（现在只会返回文档下的maya目录）
        maya_app_dirs = get_maya_user_dirs()
        
        # 检查每个目录中的启动脚本
        for dir_path in maya_app_dirs:
            self.logger.info(f"检查Maya用户目录: {dir_path}")
            
            # 只检查scripts文件夹，不检查maya版本目录
            scripts_dir = os.path.join(dir_path, "scripts")
            if os.path.isdir(scripts_dir):
                self.logger.info(f"扫描scripts目录: {scripts_dir}")
                
                # 检查恶意文件
                for file_name in KNOWN_MALICIOUS_FILES:
                    file_path = os.path.join(scripts_dir, file_name)
                    if os.path.exists(file_path):
                        self.logger.warning(f"发现已知恶意文件: {file_path}")
                        results["infected_files"].append({
                            "file": file_path,
                            "type": "known_malicious_file",
                            "reason": "已知恶意文件名"
                        })
                
                # 检查scripts目录中的其他可疑文件
                results["infected_files"].extend(self._scan_suspicious_files(scripts_dir))
        
        return results
    
    def _scan_startup_script(self, script_path):
        """扫描启动脚本文件"""
        result = {
            "file": script_path,
            "infected": False,
            "suspicious_code": []
        }
        
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 检查可疑代码模式
            for pattern in MALICIOUS_CODE_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    result["suspicious_code"].append({
                        "pattern": str(pattern),
                        "matches": len(matches)
                    })
                    result["infected"] = True
            
            # 检查可疑字符串
            for pattern in STANDARD_UI_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    result["suspicious_code"].append({
                        "pattern": f"可疑字符串: {str(pattern)}",
                        "matches": len(matches)
                    })
                    result["infected"] = True
            
            # 检查已知病毒特征
            for virus_name, patterns in VIRUS_SIGNATURES.items():
                for pattern in patterns:
                    if re.search(pattern, content):
                        result["suspicious_code"].append({
                            "pattern": f"已知病毒: {virus_name}"
                        })
                        result["infected"] = True
                        break
                if result["infected"]:
                    break
            
            # 检查base64编码的数据
            encoded_data = re.findall(r"base64\.[ub]64decode\(['\"]([A-Za-z0-9+/=]+)['\"]", content)
            for data in encoded_data:
                decoded = decode_base64_content(data)
                if decoded:
                    # 检查解码后的内容
                    for pattern in MALICIOUS_CODE_PATTERNS:
                        if re.search(pattern, decoded):
                            result["suspicious_code"].append({
                                "pattern": f"Base64解码内容包含: {str(pattern)}"
                            })
                            result["infected"] = True
                            break
            
        except Exception as e:
            self.logger.error(f"扫描启动脚本时出错: {str(e)}")
        
        return result
    
    def _scan_suspicious_files(self, scripts_dir):
        """扫描目录中的可疑文件"""
        infected_files = []
        
        self.logger.info(f"扫描目录中的可疑文件: {scripts_dir}")
        
        for file_name in os.listdir(scripts_dir):
            file_path = os.path.join(scripts_dir, file_name)
            
            # 检查是否在白名单中
            if check_if_file_in_whitelist(file_name):
                self.logger.info(f"跳过白名单文件: {file_path}")
                continue
            
            # 检查是否是已知恶意文件名
            if file_name.lower() in [name.lower() for name in KNOWN_MALICIOUS_FILES]:
                self.logger.info(f"发现已知恶意文件: {file_path}")
                infected_files.append({
                    "file": file_path,
                    "infected": True,
                    "reason": "已知恶意文件名",
                    "suspicious_code": []
                })
                continue
            
            # 只检查.py和.mel文件
            if not file_name.lower().endswith(('.py', '.mel')):
                continue
            
            # 跳过很大的文件
            if os.path.getsize(file_path) > 1024 * 1024:  # 跳过大于1MB的文件
                continue
            
            # 检查文件内容是否包含可疑代码
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                suspicious_code = []
                
                # 检查可疑代码模式
                for pattern in MALICIOUS_CODE_PATTERNS:
                    matches = re.findall(pattern, content)
                    if matches:
                        suspicious_code.append({
                            "pattern": str(pattern),
                            "matches": len(matches)
                        })
                
                # 检查可疑字符串
                for pattern in STANDARD_UI_PATTERNS:
                    matches = re.findall(pattern, content)
                    if matches:
                        suspicious_code.append({
                            "pattern": f"可疑字符串: {str(pattern)}",
                            "matches": len(matches)
                        })
                
                # 检查已知病毒特征
                for virus_name, patterns in VIRUS_SIGNATURES.items():
                    virus_found = False
                    for pattern in patterns:
                        if re.search(pattern, content):
                            suspicious_code.append({
                                "pattern": f"已知病毒: {virus_name}",
                                "matches": 1
                            })
                            virus_found = True
                            break
                    if virus_found:
                        break
                
                if suspicious_code:
                    self.logger.info(f"发现可疑代码文件: {file_path}")
                    infected_files.append({
                        "file": file_path,
                        "infected": True,
                        "reason": "包含可疑代码",
                        "suspicious_code": suspicious_code
                    })
            except Exception as e:
                self.logger.error(f"扫描文件时出错: {file_path} - {str(e)}")
        
        return infected_files
    
    def export_results(self, output_path):
        """导出扫描结果到JSON文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"扫描结果已导出到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出扫描结果时出错: {str(e)}")
            return False 