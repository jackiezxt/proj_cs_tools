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
    get_script_node_name
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
        
        # 从patterns模块导入配置
        from core.patterns import (
            ALWAYS_SUSPICIOUS_NODES,
            CONDITIONAL_SUSPICIOUS_NODES,
            MALICIOUS_NODE_PREFIXES,
            SUSPICIOUS_CODE_PATTERNS
        )
        
        # 使用导入的配置
        self.always_suspicious_nodes = ALWAYS_SUSPICIOUS_NODES
        self.conditional_suspicious_nodes = CONDITIONAL_SUSPICIOUS_NODES
        self.malicious_node_prefixes = MALICIOUS_NODE_PREFIXES
        self.suspicious_code_patterns = SUSPICIOUS_CODE_PATTERNS
        
        self.logger.info("病毒清理器初始化")
        self.results = {
            "cleaned_files": [],
            "backup_files": [],
            "failed_files": [],
            "deleted_files": [],
            "summary": {}
        }
        self.stop_requested = False
    
    def is_node_suspicious(self, node_name, node_content):
        """判断节点是否可疑"""
        # 已知恶意节点，直接清理
        if node_name in self.always_suspicious_nodes:
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
            self.logger.info("保留正常节点: {}".format(node_name))
            return False
        
        # 对于所有节点检查恶意代码特征
        for pattern in self.suspicious_code_patterns:
            if pattern in node_content:
                self.logger.warning("节点 {} 包含恶意代码特征: {}".format(node_name, pattern))
                return True
        
        # 其他节点暂不处理
        return False
    
    def clean_file(self, file_path, make_backup=True):
        """清理单个Maya文件中的病毒代码"""
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
        
        # 读取文件内容，正确处理编码
        file_content = self._read_file_with_encoding(file_path)
        if file_content is None:
            return False
        
        # 初始化日志记录器
        self.logger.info("初始化日志记录器，日志文件: {}".format(self.logger.log_path))
        
        # 分析并清理文件
        cleaned_content = file_content
        has_changes = False
        
        # 识别脚本节点
        script_nodes = []
        for match in re.finditer(r'createNode\s+script\s+-n\s+"([^"]+)"', file_content):
            node_name = match.group(1)
            # 找到节点的内容范围
            node_start = match.start()
            # 找到节点结束位置（下一个节点开始或文件结束）
            next_node = re.search(r'createNode\s+\w+\s+-n', file_content[node_start + len(match.group(0)):])
            if next_node:
                node_end = node_start + len(match.group(0)) + next_node.start()
            else:
                node_end = len(file_content)
            
            node_content = file_content[node_start:node_end]
            script_nodes.append((node_name, node_content, node_start, node_end))
        
        # 处理找到的脚本节点
        for node_name, node_content, node_start, node_end in script_nodes:
            try:
                if self.is_node_suspicious(node_name, node_content):
                    # 这是可疑节点，需要清理
                    self.logger.warning("清理可疑节点: {}".format(node_name))
                    # 创建替换内容（清理版本的节点）
                    cleaned_node = self.create_clean_node(node_name)
                    # 替换原始内容
                    cleaned_content = cleaned_content[:node_start] + cleaned_node + cleaned_content[node_end:]
                    has_changes = True
                else:
                    self.logger.info("节点不含恶意代码，保留: {}".format(node_name))
            except Exception as e:
                self.logger.error("解析节点名称时出错: {}".format(str(e)))
        
        # 如果有修改，保存文件
        if has_changes:
            try:
                # 写入处理后的内容，保持原编码
                return self._write_file_with_encoding(file_path, cleaned_content)
            except Exception as e:
                self.logger.error("保存文件时出错: {}".format(str(e)))
                return False
        else:
            self.logger.info("文件不含恶意节点，无需清理: {}".format(file_path))
        
        return True
    
    def _read_file_with_encoding(self, file_path):
        """以正确的编码读取文件内容"""
        # 尝试不同的编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    self.logger.info("成功以 {} 编码读取文件".format(encoding))
                    # 记住使用的编码，写入时使用同样的编码
                    self._current_file_encoding = encoding
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.error("读取文件时出错 ({}): {}".format(encoding, str(e)))
                continue
        
        self.logger.error("无法以任何已知编码读取文件")
        return None

    def _write_file_with_encoding(self, file_path, content):
        """以正确的编码写入文件内容"""
        try:
            # 使用与读取时相同的编码
            encoding = getattr(self, '_current_file_encoding', 'utf-8')
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            self.logger.info("成功以 {} 编码写入文件".format(encoding))
            return True
        except Exception as e:
            self.logger.error("写入文件时出错: {}".format(str(e)))
            return False
    
    def create_clean_node(self, node_name):
        """创建干净的节点替换内容"""
        # 为特定节点创建干净的替代内容
        if node_name == "breed_gene":
            return '\ncreateNode script -n "breed_gene_cleaned";\n'
        elif "ConfigurationScriptNode" in node_name:
            # 为配置脚本节点创建安全版本
            return '\ncreateNode script -n "{}";\n// 此节点已被清理工具处理\n'.format(node_name)
        else:
            # 通用替换
            return '\ncreateNode script -n "{}_cleaned";\n'.format(node_name)
    
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
                    delete_results = self._clean_suspicious_files(scripts_dir, make_backup)
                    results["deleted_files"].extend(delete_results.get("deleted_files", []))
                    results["backup_files"].extend(delete_results.get("backup_files", []))
                    results["failed_files"].extend(delete_results.get("failed_files", []))
            
            # 清理maya根目录下的scripts文件夹
            scripts_dir = os.path.join(dir_path, "scripts")
            if os.path.isdir(scripts_dir):
                delete_results = self._clean_suspicious_files(scripts_dir, make_backup)
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
            
            # 读取文件内容
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 定义要删除的可疑代码模式
            suspicious_patterns = [
                r"import\s+base64",
                r"base64\.[ub]64decode",
                r"class\s+phage",
                r"leukocyte\s*=\s*phage\(\)",
                r"leukocyte\.occupation\(\)",
                r"scriptJob.*SceneSaved",
                r"eval\s*\(\s*cmds\.getAttr\("
            ]
            
            # 标记要保留的行
            clean_lines = []
            suspicious_lines_found = False
            
            for line in lines:
                is_suspicious = False
                for pattern in suspicious_patterns:
                    if re.search(pattern, line):
                        is_suspicious = True
                        suspicious_lines_found = True
                        self.logger.info(f"发现可疑代码行: {line.strip()}")
                        break
                
                if not is_suspicious:
                    clean_lines.append(line)
            
            # 如果发现了可疑代码，写回清理后的文件
            if suspicious_lines_found:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.writelines(clean_lines)
                self.logger.info(f"成功清理启动脚本: {script_path}")
                return True
            else:
                self.logger.info(f"启动脚本不需要清理: {script_path}")
                return False
            
        except Exception as e:
            self.logger.error(f"清理启动脚本时出错: {str(e)}")
            self.results["failed_files"].append({
                "file": script_path,
                "reason": str(e)
            })
            return False
    
    def _clean_suspicious_files(self, scripts_dir, make_backup=True):
        """清理目录中的可疑文件"""
        results = {
            "deleted_files": [],
            "backup_files": [],
            "failed_files": []
        }
        
        self.logger.info(f"清理目录中的可疑文件: {scripts_dir}")
        
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
                    # 恶意文件不备份，直接删除
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
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 检查内容是否明显有害（通过简单的模式识别）
                is_harmful = False
                
                for pattern in MALICIOUS_CODE_PATTERNS:
                    if re.search(pattern, content):
                        is_harmful = True
                        break
                
                if is_harmful:
                    # 恶意代码文件不备份，直接删除
                    os.remove(file_path)
                    results["deleted_files"].append(file_path)
                    self.logger.info(f"已删除恶意代码文件: {file_path}")
            except Exception as e:
                self.logger.error(f"检查或删除可疑文件时出错: {file_path} - {str(e)}")
        
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
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # 检查是否包含恶意代码
                        has_malicious_code = False
                        for pattern in MALICIOUS_CODE_PATTERNS:
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
        """清理系统中的恶意启动脚本"""
        results = {
            "clean_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cleaned_files": []
        }
        
        # 获取Maya用户目录
        maya_app_dirs = get_maya_user_dirs()
        
        # 清理每个目录中的启动脚本
        for dir_path in maya_app_dirs:
            self.logger.info(f"检查Maya用户目录: {dir_path}")
            
            # 检查scripts目录
            scripts_dir = os.path.join(dir_path, "scripts")
            if os.path.isdir(scripts_dir):
                self.logger.info(f"清理scripts目录: {scripts_dir}")
                
                # 删除已知恶意文件
                for file_name in KNOWN_MALICIOUS_FILES:
                    file_path = os.path.join(scripts_dir, file_name)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            self.logger.info(f"已删除已知恶意文件: {file_path}")
                            results["cleaned_files"].append({
                                "file": file_path,
                                "status": "已删除",
                                "reason": "已知恶意文件"
                            })
                        except Exception as e:
                            self.logger.error(f"删除文件失败: {file_path} - {str(e)}")
                            results["cleaned_files"].append({
                                "file": file_path,
                                "status": "删除失败",
                                "error": str(e)
                            })
        
        return results 