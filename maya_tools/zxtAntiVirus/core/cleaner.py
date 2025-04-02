#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理器核心模块
负责清理Maya文件中的恶意代码和系统启动脚本
"""
import os
import re
import datetime
import shutil
import traceback
from utils.logger import Logger
from utils.common import (
    get_maya_user_dirs,
    create_backup,
    check_if_file_in_whitelist,
    decode_base64_content,
    is_maya_ascii_file,
    is_maya_binary_file,
    get_script_node_content,
    get_script_node_name,
    get_maya_user_script_dir,
    read_file_with_encoding,
    write_file_with_encoding,
    normalize_path
)
from core.patterns import (
    ALWAYS_SUSPICIOUS_NODES,
    CONDITIONAL_SUSPICIOUS_NODES,
    MALICIOUS_NODE_PREFIXES,
    SUSPICIOUS_CODE_PATTERNS,
    STANDARD_NODES,
    MALICIOUS_CODE_PATTERNS,
    STANDARD_UI_PATTERNS,
    KNOWN_MALICIOUS_FILES,
    WHITELISTED_FILES,
    VIRUS_SIGNATURES
)

class VirusCleaner:
    """Maya文件病毒清理器"""
    
    def __init__(self, log_path=None):
        """初始化清理器"""
        self.logger = Logger(log_path) if log_path else Logger()
        
        # 不再重复导入，使用类模块级别导入的变量
        self.always_suspicious_nodes = ALWAYS_SUSPICIOUS_NODES
        self.conditional_suspicious_nodes = CONDITIONAL_SUSPICIOUS_NODES
        self.malicious_node_prefixes = MALICIOUS_NODE_PREFIXES
        self.suspicious_code_patterns = SUSPICIOUS_CODE_PATTERNS
        self.malicious_code_patterns = MALICIOUS_CODE_PATTERNS
        
        self.logger.info("病毒清理器初始化")
        self.results = {
            "cleaned_files": [],
            "backup_files": [],
            "failed_files": [],
            "deleted_files": [],
            "summary": {}
        }
        self.stop_requested = False
        self._current_file_encoding = 'utf-8'  # 默认文件编码
    
    def is_node_suspicious(self, node_name, node_content):
        """判断节点是否可疑"""
        # 已知恶意节点，直接清理
        if node_name in self.always_suspicious_nodes:
            self.logger.warning("节点 {} 确定为恶意节点，将被清理".format(node_name))
            return True
        
        # 检查其他可能的恶意节点名称
        for prefix in self.malicious_node_prefixes:
            if prefix.lower() in node_name.lower():
                self.logger.warning("节点名称 {} 包含可疑前缀: {}".format(node_name, prefix))
                return True
        
        # 条件判断的脚本节点，需要检查内容
        if node_name in self.conditional_suspicious_nodes or "ConfigurationScriptNode" in node_name:
            # 检查是否包含可疑代码特征
            for pattern in self.suspicious_code_patterns:
                if pattern in node_content:
                    self.logger.warning("节点 {} 包含恶意代码特征: {}".format(node_name, pattern))
                    return True
            
            # 如果没有可疑特征，保留该节点
            self.logger.info("节点不含恶意代码，保留: {}".format(node_name))
            return False
        
        # 对于所有节点检查恶意代码特征
        for pattern in self.suspicious_code_patterns:
            if pattern in node_content:
                self.logger.warning("节点 {} 包含恶意代码特征: {}".format(node_name, pattern))
                return True
        
        # 其他节点暂不处理
        self.logger.info("节点不含恶意代码，保留: {}".format(node_name))
        return False
    
    def clean_file(self, file_path, make_backup=True, detected_encoding=None):
        """清理单个Maya文件中的病毒代码
        
        Args:
            file_path: 文件路径
            make_backup: 是否创建备份
            detected_encoding: 预先检测到的文件编码，如果提供则优先使用
        
        Returns:
            bool: 清理成功返回True，否则返回False
        """
        self.logger.info("开始清理文件: {}".format(file_path))
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.logger.error("文件不存在: {}".format(file_path))
            return False
        
        # 创建备份
        if make_backup:
            backup_path = "{}.{}".format(file_path, datetime.datetime.now().strftime("%Y%m%d_%H%M%S.bak"))
            self.logger.info("已创建备份: {}".format(backup_path))
            shutil.copy2(file_path, backup_path)
        
        # 如果提供了编码信息，先记录下来
        if detected_encoding:
            self._current_file_encoding = detected_encoding
            self.logger.info(f"使用预先检测到的编码: {detected_encoding}")
        
        # 读取文件内容，正确处理编码
        file_content = self._read_file_with_encoding(file_path)
        if file_content is None:
            return False
        
        # 初始化日志记录器
        self.logger.info("初始化日志记录器，日志文件: {}".format(self.logger.log_path))
        
        # 采用更精确的节点解析方法
        # 具体做法：查找所有createNode开始和结束的句子，然后对内容分析
        cleaned_content = file_content
        has_changes = False
        
        # 正则表达式查找所有创建节点的语句块
        # 格式: createNode script -n "节点名";
        # 注意：Maya ASCII文件中，节点定义通常从createNode开始到下一个createNode或分号结束
        node_pattern = r'createNode\s+script\s+-n\s+"([^"]+)";'
        
        # 查找所有匹配的节点创建语句
        node_matches = list(re.finditer(node_pattern, file_content))
        
        # 如果找到节点
        if node_matches:
            # 收集需要删除的节点块的范围
            sections_to_delete = []
            
            # 遍历所有节点
            for i, match in enumerate(node_matches):
                node_name = match.group(1)
                node_start = match.start()
                
                # 查找当前节点的结束位置 - 是下一个createNode开始，或者文件结束
                if i < len(node_matches) - 1:
                    # 下一个节点的起始位置
                    next_node_start = node_matches[i + 1].start()
                    
                    # 可能存在其他类型的createNode，查看当前节点和下一个节点之间是否有其他createNode
                    intermediate_node = re.search(r'\bcreateNode\b', file_content[node_start + len(match.group(0)):next_node_start])
                    if intermediate_node:
                        # 有中间节点，结束位置是中间节点的开始
                        node_end = node_start + len(match.group(0)) + intermediate_node.start()
                    else:
                        # 没有中间节点，结束位置是下一个匹配节点的开始
                        node_end = next_node_start
                else:
                    # 最后一个节点，查找下一个createNode或文件结束
                    next_create = re.search(r'\bcreateNode\b', file_content[node_start + len(match.group(0)):])
                    if next_create:
                        node_end = node_start + len(match.group(0)) + next_create.start()
                    else:
                        # 没有找到下一个createNode，使用文件结束
                        node_end = len(file_content)
                
                # 提取完整的节点内容
                node_content = file_content[node_start:node_end].strip()
                
                # 检查节点是否为可疑节点
                is_suspicious = False
                
                # 检查是否为已知恶意节点 - ALWAYS_SUSPICIOUS_NODES中的节点
                if node_name in self.always_suspicious_nodes:
                    self.logger.warning(f"发现已知恶意节点: {node_name}，将被删除")
                    is_suspicious = True
                
                # 检查节点名称是否包含可疑前缀
                if not is_suspicious:
                    for prefix in self.malicious_node_prefixes:
                        if prefix.lower() in node_name.lower():
                            self.logger.warning(f"节点名称 {node_name} 包含可疑前缀: {prefix}，将被删除")
                            is_suspicious = True
                            break
                
                # 条件判断的节点（需要检查内容）
                if not is_suspicious and (node_name in self.conditional_suspicious_nodes or "ConfigurationScriptNode" in node_name):
                    # 检查是否包含可疑代码特征
                    for pattern in self.suspicious_code_patterns:
                        if re.search(pattern, node_content, re.IGNORECASE):
                            self.logger.warning(f"节点 {node_name} 包含恶意代码特征: {pattern}，将被删除")
                            is_suspicious = True
                            break
                
                # 如果节点被判定为可疑，记录其范围，准备删除
                if is_suspicious:
                    sections_to_delete.append((node_start, node_end))
                    self.logger.info(f"已标记恶意节点供删除: {node_name}")
            
            # 如果找到了可疑节点，从后向前删除（避免位置变化）
            if sections_to_delete:
                sections_to_delete.sort(reverse=True)  # 从后向前排序
                
                for start, end in sections_to_delete:
                    # 记录原始长度，用于验证删除是否成功
                    original_length = len(cleaned_content)
                    
                    # 删除节点块
                    cleaned_content = cleaned_content[:start] + cleaned_content[end:]
                    
                    # 验证删除是否成功
                    if len(cleaned_content) < original_length:
                        deleted_size = original_length - len(cleaned_content)
                        self.logger.info(f"已删除恶意节点块 ({deleted_size} 字节)")
                        has_changes = True
                    else:
                        self.logger.error(f"节点块删除失败，内容长度未变")
        
        # 如果没有做任何更改
        if not has_changes:
            self.logger.info(f"文件不含可疑节点，无需清理: {file_path}")
            return True
        
        # 写入清理后的内容
        try:
            success = self._write_file_with_encoding(file_path, cleaned_content)
            if success:
                self.logger.info("清理完成")
                return True
            else:
                self.logger.error("保存清理结果失败")
                return False
        except Exception as e:
            self.logger.error("保存文件时出错: {}".format(str(e)))
            return False
    
    def _read_file_with_encoding(self, file_path):
        """读取文件内容并尝试保留原始编码"""
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
                    self.logger.info(f"检测到文件编码: {detected_encoding}，置信度: {confidence:.2f}")
                    # 将检测到的编码添加到尝试列表的最前面
                    if detected_encoding.lower() not in [enc.lower() for enc in encodings_to_try]:
                        encodings_to_try.insert(0, detected_encoding)
        except ImportError:
            self.logger.warning("未安装chardet模块，将依次尝试常见编码")
        
        # 依次尝试不同编码
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    self._current_file_encoding = encoding
                    self.logger.info(f"成功以 {encoding} 编码读取文件: {file_path}")
                    return content
            except UnicodeDecodeError:
                continue
        
        # 如果所有尝试都失败，使用二进制读取并使用UTF-8解码，忽略错误
        self.logger.warning(f"所有编码尝试失败，使用二进制模式读取: {file_path}")
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
                self._current_file_encoding = 'utf-8'
                self.logger.warning(f"以替代方式读取文件，可能存在字符问题: {file_path}")
                return content
        except Exception as e:
            self.logger.error(f"读取文件时出错: {str(e)}")
            return None

    def _write_file_with_encoding(self, file_path, content):
        """使用原始文件编码写入文件内容"""
        # 获取之前检测到的文件编码
        encoding = self._current_file_encoding if hasattr(self, '_current_file_encoding') else 'utf-8'
        
        try:
            # 使用检测到的原始编码写回文件
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            self.logger.info(f"成功以原始编码 {encoding} 写入文件: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"以编码 {encoding} 写入文件时出错: {str(e)}")
            
            # 如果写入失败且不是UTF-8，尝试使用UTF-8作为备选
            if encoding.lower() != 'utf-8':
                try:
                    self.logger.warning(f"尝试使用UTF-8编码作为备选方案")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.logger.info(f"成功以UTF-8编码写入文件: {file_path}")
                    return True
                except Exception as e2:
                    self.logger.error(f"备选方案也失败了: {str(e2)}")
            
            return False
    
    def create_clean_node(self, node_name):
        """创建干净的节点替换内容
        
        Args:
            node_name: 节点名称
            
        Returns:
            替换原节点的内容字符串
        """
        # 对于已知恶意节点（ALWAYS_SUSPICIOUS_NODES中的节点），完全删除
        if node_name in self.always_suspicious_nodes:
            self.logger.warning(f"完全删除已知恶意节点: {node_name}")
            return ""  # 直接返回空字符串，不添加任何注释
        
        # 对于带有可疑前缀的节点，也完全删除
        for prefix in self.malicious_node_prefixes:
            if prefix.lower() in node_name.lower():
                self.logger.warning(f"完全删除带有可疑前缀的节点: {node_name}")
                return ""  # 直接返回空字符串，不添加任何注释
        
        # 对于条件检查的节点，如果它们包含恶意代码，替换为空节点
        if "ConfigurationScriptNode" in node_name:
            # 为配置脚本节点创建安全版本，保留节点但清除内容
            self.logger.info(f"节点不含恶意代码，保留: {node_name}")
            return f'\ncreateNode script -n "{node_name}";\n'  # 不添加注释
        
        # 其他情况，完全移除节点
        self.logger.warning(f"删除可疑节点: {node_name}")
        return ""  # 直接返回空字符串，不添加任何注释
    
    def clean_startup_scripts(self, make_backup=True):
        """清理Maya启动脚本中的恶意代码"""
        results = {
            "cleaned_files": [],
            "backup_files": [],
            "failed_files": [],
            "deleted_files": [],
            "summary": {}
        }
        
        # 获取Maya用户目录
        maya_app_dirs = get_maya_user_dirs()
        
        # 清理每个目录中的启动脚本
        for dir_path in maya_app_dirs:
            # 检查是否请求停止
            if self.stop_requested:
                self.logger.info("清理操作已停止")
                break
                
            self.logger.info(f"检查Maya用户目录: {dir_path}")
            
            # 检查所有可能的Maya版本目录
            for maya_ver_dir in os.listdir(dir_path):
                # 检查是否请求停止
                if self.stop_requested:
                    self.logger.info("清理操作已停止")
                    break
                    
                scripts_dir = os.path.join(dir_path, maya_ver_dir, "scripts")
                if os.path.isdir(scripts_dir):
                    # 检查并清理userSetup.py
                    usersetup_py = os.path.join(scripts_dir, "userSetup.py")
                    if os.path.exists(usersetup_py):
                        if self._clean_startup_script(usersetup_py, make_backup):
                            results["cleaned_files"].append(usersetup_py)
                    
                    # 检查并清理userSetup.mel
                    usersetup_mel = os.path.join(scripts_dir, "userSetup.mel")
                    if os.path.exists(usersetup_mel):
                        if self._clean_startup_script(usersetup_mel, make_backup):
                            results["cleaned_files"].append(usersetup_mel)
                    
                    # 清理脚本目录中的恶意文件
                    delete_results = self._clean_suspicious_files(scripts_dir, results)
                    results["deleted_files"].extend(delete_results.get("deleted_files", []))
                    results["backup_files"].extend(delete_results.get("backup_files", []))
                    results["failed_files"].extend(delete_results.get("failed_files", []))
            
            # 清理maya根目录下的scripts文件夹
            scripts_dir = os.path.join(dir_path, "scripts")
            if os.path.isdir(scripts_dir):
                delete_results = self._clean_suspicious_files(scripts_dir, results)
                results["deleted_files"].extend(delete_results.get("deleted_files", []))
                results["backup_files"].extend(delete_results.get("backup_files", []))
                results["failed_files"].extend(delete_results.get("failed_files", []))
        
        # 更新扫描摘要
        results["summary"] = {
            "scan_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cleaned_files_count": len(results["cleaned_files"]),
            "deleted_files_count": len(results["deleted_files"]),
            "backup_files_count": len(results["backup_files"]),
            "failed_files_count": len(results["failed_files"])
        }
        
        self.results = results
        return results
    
    def _clean_startup_script(self, script_path, make_backup=True):
        """清理启动脚本文件"""
        try:
            self.logger.info(f"开始清理启动脚本: {script_path}")
            
            # 创建备份
            if make_backup:
                backup_path = create_backup(script_path)
                if backup_path:
                    self.results["backup_files"].append(backup_path)
                    self.logger.info(f"已创建备份: {backup_path}")
                else:
                    self.logger.warning(f"创建备份失败，取消清理操作")
                    return False
            
            # 读取文件内容 - 使用统一的读取方法
            content = self._read_file_with_encoding(script_path)
            if content is None:
                self.logger.error(f"无法读取文件内容，跳过清理: {script_path}")
                return False
            
            # 检查是否有恶意代码
            cleaned_content = content
            found_malicious = False
            
            for pattern in self.suspicious_code_patterns:
                if re.search(pattern, content):
                    found_malicious = True
                    cleaned_content = re.sub(pattern, "# 已移除可疑代码", cleaned_content)
                    self.logger.info(f"在启动脚本中发现并清理了可疑代码: {pattern}")
            
            # 如果没有找到恶意代码，则不需要写回
            if not found_malicious:
                self.logger.info(f"未在启动脚本中发现可疑代码: {script_path}")
                return False
            
            # 写回清理后的内容
            if self._write_file_with_encoding(script_path, cleaned_content):
                self.logger.info(f"已成功清理启动脚本: {script_path}")
                return True
            else:
                self.logger.error(f"写入清理后的启动脚本失败: {script_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"清理启动脚本时出错: {script_path} - {str(e)}")
            self.logger.error(traceback.format_exc())
            return False
    
    def _clean_suspicious_files(self, scripts_dir, results):
        """清理目录中的可疑文件"""
        try:
            self.logger.info(f"清理目录中的可疑文件: {scripts_dir}")
            
            if not os.path.exists(scripts_dir) or not os.path.isdir(scripts_dir):
                self.logger.warning(f"目录不存在或不是有效目录: {scripts_dir}")
                return results
            
            for file_name in os.listdir(scripts_dir):
                file_path = os.path.join(scripts_dir, file_name)
                
                # 跳过目录
                if os.path.isdir(file_path):
                    continue
                
                # 检查是否在白名单中
                if check_if_file_in_whitelist(file_name):
                    self.logger.info(f"保留白名单文件: {file_path}")
                    continue
                
                # 检查是否是已知恶意文件名
                if file_name.lower() in [name.lower() for name in self.conditional_suspicious_nodes]:
                    self.logger.info(f"发现已知恶意文件: {file_path}")
                    
                    try:
                        # 恶意文件备份（为了安全）
                        backup_path = create_backup(file_path)
                        if backup_path:
                            results["backup_files"].append(backup_path)
                            self.logger.info(f"已创建恶意文件备份: {backup_path}")
                        
                        # 删除恶意文件
                        os.remove(file_path)
                        results["deleted_files"].append(file_path)
                        self.logger.info(f"已删除恶意文件: {file_path}")
                    except Exception as e:
                        self.logger.error(f"删除恶意文件时出错: {file_path} - {str(e)}")
                        results["failed_files"].append({
                            "file": file_path,
                            "reason": str(e)
                        })
                    
                    continue
                
                # 只检查.py和.mel文件
                if not file_name.lower().endswith(('.py', '.mel')):
                    continue
                
                # 检查文件内容是否包含可疑代码
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    self.logger.warning(f"UTF-8读取失败，尝试替代方案: {file_path}")
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('utf-8', errors='replace')
                    except Exception as e:
                        self.logger.error(f"无法读取文件内容: {file_path} - {str(e)}")
                        continue
                except Exception as e:
                    self.logger.error(f"读取文件时出错: {file_path} - {str(e)}")
                    continue
                
                # 检查内容是否明显有害（通过简单的模式识别）
                is_harmful = False
                
                for pattern in self.malicious_code_patterns:
                    if re.search(pattern, content):
                        is_harmful = True
                        self.logger.warning(f"发现含有恶意代码的文件: {file_path}")
                        break
                
                if is_harmful:
                    try:
                        # 恶意代码文件备份（为了安全）
                        backup_path = create_backup(file_path)
                        if backup_path:
                            results["backup_files"].append(backup_path)
                            self.logger.info(f"已创建恶意代码文件备份: {backup_path}")
                        
                        # 删除恶意代码文件
                        os.remove(file_path)
                        results["deleted_files"].append(file_path)
                        self.logger.info(f"已删除恶意代码文件: {file_path}")
                    except Exception as e:
                        self.logger.error(f"删除恶意代码文件时出错: {file_path} - {str(e)}")
                        results["failed_files"].append({
                            "file": file_path,
                            "reason": str(e)
                        })
        
            return results
            
        except Exception as e:
            self.logger.error(f"清理可疑文件时出错: {scripts_dir} - {str(e)}")
            self.logger.error(traceback.format_exc())
            return results

    def integrate_scene_cleanup(self, import_maya=False):
        """集成zxtSCNclearUp.py中的清理功能
        
        Args:
            import_maya: 是否导入maya.cmds，这是为了在非Maya环境中避免导入错误
        
        Returns:
            dict: 包含清理结果的字典
        """
        results = {
            "cleaned_script_nodes": [],
            "cleaned_job_nodes": [],
            "cleaned_plugins": [],
            "cleaned_unknown_nodes": [],
            "cleaned_editor_callbacks": []
        }
        
        # 修改导入方式，防止变量未定义错误
        try:
            import maya.cmds as mc
            import maya.mel as mm
        except ImportError:
            if import_maya:
                self.logger.error("无法导入Maya模块，确保在Maya环境中运行")
                return results
            else:
                self.logger.info("非Maya环境，跳过场景清理")
                return results
        
        try:
            # 1. 清理scriptNode节点
            self.logger.info("开始清理Maya场景中的scriptNode节点")
            scripts = mc.ls(type="script")
            for script in scripts:
                try:
                    # 检查是否包含可疑关键字
                    suspicious = False
                    virus_prefixes = ['vacc', 'breed', 'fuckVirus', 'vaccine_gene', 'breed_gene', 
                                     'uifiguration', 'phage', 'leukocyte', 'antivirus']
                    
                    for prefix in virus_prefixes:
                        if prefix.lower() in script.lower():
                            suspicious = True
                            break
                    
                    if suspicious:
                        mc.lockNode(script, l=False)
                        mc.setAttr(f'{script}.scriptType', 0)  # 设置为无类型，防止运行
                        mc.delete(script)
                        results["cleaned_script_nodes"].append(script)
                        self.logger.info(f"已删除可疑脚本节点: {script}")
                except Exception as e:
                    self.logger.error(f"删除脚本节点时出错: {script} - {str(e)}")
            
            # 2. 清理scriptJob
            self.logger.info("清理可疑的scriptJob")
            for job in mc.scriptJob(listJobs=True):
                try:
                    suspicious_keywords = ["leukocyte", "antivirus", "vaccine", "breed", "phage"]
                    if any(keyword in job for keyword in suspicious_keywords):
                        job_num = int(job.split(":")[0])
                        mc.scriptJob(kill=job_num, force=True)
                        results["cleaned_job_nodes"].append(job)
                        self.logger.info(f"已终止可疑scriptJob: {job}")
                except Exception as e:
                    self.logger.error(f"终止scriptJob时出错: {job} - {str(e)}")
            
            # 3. 清理未知插件
            self.logger.info("清理未知插件")
            try:
                unknown_plugins = mc.unknownPlugin(query=True, list=True) or []
                for plugin in unknown_plugins:
                    try:
                        mc.unknownPlugin(plugin, remove=True)
                        results["cleaned_plugins"].append(plugin)
                        self.logger.info(f"已移除未知插件: {plugin}")
                    except Exception as e:
                        self.logger.error(f"移除未知插件时出错: {plugin} - {str(e)}")
            except Exception as e:
                self.logger.error(f"处理未知插件时出错: {str(e)}")
            
            # 4. 清理未知节点类型
            self.logger.info("清理未知节点类型")
            try:
                unknown_types = ['unknown', 'unknownDag', 'unknownTransform']
                unknown_nodes = mc.ls(type=unknown_types) or []
                for node in unknown_nodes:
                    try:
                        mc.lockNode(node, lock=False)
                        mc.delete(node)
                        results["cleaned_unknown_nodes"].append(node)
                        self.logger.info(f"已删除未知节点: {node}")
                    except Exception as e:
                        self.logger.error(f"删除未知节点时出错: {node} - {str(e)}")
            except Exception as e:
                self.logger.error(f"处理未知节点时出错: {str(e)}")
            
            # 5. 重置编辑器回调
            self.logger.info("重置编辑器回调")
            try:
                # 重置modelEditor回调
                model_editors = mc.lsUI(editors=True) or []
                for editor in model_editors:
                    if mc.objectTypeUI(editor) == "modelEditor":
                        callback = mc.modelEditor(editor, query=True, editorChanged=True)
                        if callback:
                            mc.modelEditor(editor, edit=True, editorChanged="")
                            results["cleaned_editor_callbacks"].append(f"{editor}: {callback}")
                            self.logger.info(f"已重置编辑器回调: {editor}")
                
                # 重置outliner回调
                for panel in mc.lsUI(panels=True) or []:
                    if mc.objectTypeUI(panel) == "outlinerPanel":
                        editor = mc.outlinerPanel(panel, query=True, outlinerEditor=True)
                        if editor:
                            mm.eval(f'outlinerEditor -edit -selectCommand "" "{editor}";')
                            results["cleaned_editor_callbacks"].append(f"{editor}: resetSelectCommand")
                            self.logger.info(f"已重置大纲编辑器回调: {editor}")
            except Exception as e:
                self.logger.error(f"重置编辑器回调时出错: {str(e)}")
            
            # 6. 解锁初始节点
            self.logger.info("解锁初始节点")
            try:
                lock_nodes = ['initialParticleSE', 'renderPartition', 'initialShadingGroup', 'defaultTextureList1']
                for node in lock_nodes:
                    if mc.objExists(node):
                        mc.lockNode(node, lock=False, lockUnpublished=False)
                        self.logger.info(f"已解锁节点: {node}")
            except Exception as e:
                self.logger.error(f"解锁初始节点时出错: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"场景清理过程中出错: {str(e)}")
        
        # 更新总结
        results["summary"] = {
            "script_nodes_count": len(results["cleaned_script_nodes"]),
            "job_nodes_count": len(results["cleaned_job_nodes"]),
            "plugins_count": len(results["cleaned_plugins"]),
            "unknown_nodes_count": len(results["cleaned_unknown_nodes"]),
            "editor_callbacks_count": len(results["cleaned_editor_callbacks"])
        }
        
        self.logger.info(f"场景清理完成, 共清理 {sum(results['summary'].values())} 个项目")
        return results
        
    def clean_system(self):
        """清理系统垃圾文件（不依赖Maya UI）
        
        此方法用于在mayapy独立环境中运行，不需要Maya UI
        清理系统中的垃圾文件、插件注册表和启动脚本
        
        Returns:
            dict: 包含清理结果的字典
        """
        results = {
            "cleaned_startup_files": [],
            "deleted_virus_files": [],
            "cleaned_dirs": []
        }
        
        self.logger.info("开始系统清理(独立模式)...")
        
        try:
            # 导入必要的模块
            import os
            import glob
            import shutil
            import re
            
            # 1. 检查和清理Maya用户目录
            maya_app_dirs = get_maya_user_dirs()
            
            for maya_dir in maya_app_dirs:
                self.logger.info(f"清理Maya用户目录: {maya_dir}")
                
                # 清理scripts目录
                scripts_dir = os.path.join(maya_dir, "scripts")
                if os.path.exists(scripts_dir):
                    results["cleaned_dirs"].append(scripts_dir)
                    self._clean_standalone_scripts_dir(scripts_dir, results)
                
                # 清理各个Maya版本的scripts目录
                for maya_version in os.listdir(maya_dir):
                    version_scripts_dir = os.path.join(maya_dir, maya_version, "scripts")
                    if os.path.exists(version_scripts_dir):
                        results["cleaned_dirs"].append(version_scripts_dir)
                        self._clean_standalone_scripts_dir(version_scripts_dir, results)
            
            # 2. 清理Maya首选项文件中的病毒设置 (如果有)
            # 这部分需要根据具体病毒修改首选项文件
            
            self.logger.info("系统清理完成")
            
        except Exception as e:
            self.logger.error(f"系统清理出错: {str(e)}")
        
        # 更新结果摘要
        results["summary"] = {
            "cleaned_startup_files_count": len(results["cleaned_startup_files"]),
            "deleted_virus_files_count": len(results["deleted_virus_files"]),
            "cleaned_dirs_count": len(results["cleaned_dirs"])
        }
        
        return results
    
    def _clean_standalone_scripts_dir(self, scripts_dir, results):
        """清理脚本目录中的恶意文件(独立模式使用)"""
        try:
            # 已知的恶意文件名
            virus_files = [
                "vaccine.py", "vaccine.pyc", "vaccine.pyo",
                "userSetup.py", "userSetup.pyc", "userSetup.pyo",
                "fuckVirus.py", "fuckVirus.pyc", "fuckVirus.pyo",
                "antivirus.py", "antivirus.pyc", "antivirus.pyo",
                "av.py", "av.pyc", "av.pyo",
                "phage.py", "phage.pyc", "phage.pyo",
                "leukocyte.py", "leukocyte.pyc", "leukocyte.pyo"
            ]
            
            # 逐个检查文件
            for file_name in os.listdir(scripts_dir):
                file_path = os.path.join(scripts_dir, file_name)
                
                # 跳过目录
                if os.path.isdir(file_path):
                    continue
                
                # 跳过白名单文件
                if check_if_file_in_whitelist(file_name):
                    self.logger.info(f"保留白名单文件: {file_path}")
                    continue
                
                # 检查是否是恶意文件
                is_virus = False
                for virus_name in virus_files:
                    if file_name.lower() == virus_name.lower():
                        is_virus = True
                        break
                
                # 对于userSetup文件，检查内容而不是直接删除
                if file_name.lower() in ["usersetup.py", "usersetup.mel"]:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 检查是否包含恶意代码
                        has_malicious_code = False
                        for pattern in self.malicious_code_patterns:
                            if re.search(pattern, content):
                                has_malicious_code = True
                                break
                        
                        if has_malicious_code:
                            # 创建备份
                            backup_path = create_backup(file_path)
                            if backup_path:
                                self.logger.info(f"已备份: {backup_path}")
                                results["cleaned_startup_files"].append(file_path)
                            
                            # 清理文件内容
                            self._clean_startup_script(file_path, make_backup=False)
                            continue  # 已处理，跳过删除
                        
                    except Exception as e:
                        self.logger.error(f"检查启动脚本时出错: {str(e)}")
                
                # 删除恶意文件
                if is_virus:
                    try:
                        os.remove(file_path)
                        self.logger.info(f"已删除恶意文件: {file_path}")
                        results["deleted_virus_files"].append(file_path)
                    except Exception as e:
                        self.logger.error(f"删除恶意文件时出错: {file_path} - {str(e)}")
                
        except Exception as e:
            self.logger.error(f"清理脚本目录时出错: {scripts_dir} - {str(e)}") 

    def clean_system_startup_scripts(self):
        """清理系统中的Maya启动脚本 - 仅清理我的文档/maya/scripts，不包含子文件夹"""
        self.logger.info("开始清理系统启动脚本")
        
        # 获取Maya脚本路径（仅我的文档/maya/scripts）
        maya_script_paths = self._get_maya_script_paths()
        
        # 从patterns中导入已知恶意文件和恶意代码模式
        from core.patterns import KNOWN_MALICIOUS_FILES, MALICIOUS_CODE_PATTERNS
        
        # 跟踪处理的文件和可疑文件
        suspicious_files = []
        
        # 只扫描特定目录（不递归子文件夹）
        for script_path in maya_script_paths:
            if os.path.exists(script_path):
                self.logger.info(f"检查脚本路径: {script_path}")
                
                # 只检查当前目录中的文件，不遍历子目录
                for filename in os.listdir(script_path):
                    file_path = os.path.join(script_path, filename)
                    
                    # 跳过子目录
                    if os.path.isdir(file_path):
                        continue
                    
                    # 检查白名单
                    if check_if_file_in_whitelist(filename):
                        self.logger.info(f"保留白名单文件: {file_path}")
                        continue
                    
                    # 特别检查userSetup文件 (.mel和.py)
                    if filename.lower() in ["usersetup.mel", "usersetup.py"]:
                        self.logger.warning(f"发现可疑的启动脚本: {file_path}")
                        suspicious_files.append(file_path)
                        try:
                            # 创建备份以防万一
                            backup_path = create_backup(file_path)
                            if backup_path:
                                self.logger.info(f"已创建备份: {backup_path}")
                            
                            # 删除文件
                            os.remove(file_path)
                            self.logger.info(f"已删除可疑启动脚本: {file_path}")
                        except Exception as e:
                            self.logger.error(f"删除文件时出错: {str(e)}")
                    
                    # 检查其他已知恶意文件 - 直接删除不备份
                    elif filename.lower() in [name.lower() for name in KNOWN_MALICIOUS_FILES]:
                        self.logger.warning(f"发现已知恶意文件: {file_path}")
                        suspicious_files.append(file_path)
                        try:
                            # 直接删除文件，不创建备份
                            os.remove(file_path)
                            self.logger.info(f"已删除恶意文件: {file_path}")
                        except Exception as e:
                            self.logger.error(f"删除文件时出错: {str(e)}")
                    
                    # 检查其他.py和.mel文件是否包含恶意代码
                    elif filename.lower().endswith(('.py', '.mel')):
                        try:
                            # 统一使用UTF-8读取，处理可能的编码错误
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                            except UnicodeDecodeError:
                                self.logger.warning(f"UTF-8读取失败，尝试替代方案: {file_path}")
                                with open(file_path, 'rb') as f:
                                    content = f.read().decode('utf-8', errors='replace')
                            
                            # 检查是否包含恶意代码
                            has_malicious_code = False
                            for pattern in MALICIOUS_CODE_PATTERNS:
                                if re.search(pattern, content):  # 使用正则表达式搜索，不是简单的字符串匹配
                                    has_malicious_code = True
                                    self.logger.warning(f"发现匹配恶意代码模式的内容: {pattern}")
                                    break
                            
                            if has_malicious_code:
                                self.logger.warning(f"发现包含恶意代码的文件: {file_path}")
                                suspicious_files.append(file_path)
                                # 创建备份以防万一
                                backup_path = create_backup(file_path)
                                if backup_path:
                                    self.logger.info(f"已创建备份: {backup_path}")
                                
                                # 删除文件
                                os.remove(file_path)
                                self.logger.info(f"已删除包含恶意代码的文件: {file_path}")
                        except Exception as e:
                            self.logger.error(f"检查文件内容时出错: {file_path} - {str(e)}")
                            self.logger.error(traceback.format_exc())
        
        self.logger.info("系统启动脚本清理完成")
        
        # 更新结果字典
        self.results["deleted_files"].extend(suspicious_files)
        
        # 返回结果，包括找到的可疑文件列表
        return {
            "infected_files": [{"file": file_path} for file_path in suspicious_files]
        }

    def _get_maya_script_paths(self):
        """获取Maya脚本路径列表 - 仅返回我的文档/maya/scripts，不包含子文件夹"""
        # 获取用户文档目录
        user_docs = os.path.expanduser("~")
        
        # 只返回通用的Maya脚本路径（不包含版本号）
        maya_common_scripts = os.path.join(user_docs, "Documents", "maya", "scripts")
        
        # 检查目录是否存在
        if os.path.exists(maya_common_scripts):
            self.logger.info("找到的Maya脚本路径: {}".format(maya_common_scripts))
            return [maya_common_scripts]  # 只返回这一个路径
        else:
            self.logger.warning("未找到Maya脚本路径: {}".format(maya_common_scripts))
            return []  # 如果目录不存在，返回空列表 