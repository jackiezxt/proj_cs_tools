# -*- coding: utf-8 -*-
"""
文件处理模块
提供高效的文件读写和处理功能
"""
import os
import re
import shutil
from utils.common import create_backup

def read_file_safe(file_path, encoding='utf-8'):
    """安全地读取文件内容
    
    Args:
        file_path (str): 文件路径
        encoding (str): 文件编码
        
    Returns:
        str: 文件内容
    """
    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"读取文件失败: {str(e)}")

def write_file_safe(file_path, content, encoding='utf-8'):
    """安全地写入文件内容
    
    Args:
        file_path (str): 文件路径
        content (str): 要写入的内容
        encoding (str): 文件编码
        
    Returns:
        bool: 是否成功写入
    """
    try:
        # 先写入临时文件
        temp_file = file_path + ".tmp"
        with open(temp_file, 'w', encoding=encoding) as f:
            f.write(content)
        
        # 确认临时文件写入成功后替换原文件
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_file, file_path)
            return True
        else:
            # 临时文件创建失败
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
    except Exception as e:
        # 确保清理临时文件
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        raise IOError(f"写入文件失败: {str(e)}")

def process_file_with_backup(file_path, processor_func, make_backup=True, logger=None):
    """使用备份保护处理文件
    
    Args:
        file_path (str): 文件路径
        processor_func (callable): 处理函数，接收文件内容作为参数，返回处理后的内容
        make_backup (bool): 是否创建备份
        logger: 可选的日志记录器
        
    Returns:
        dict: 处理结果
    """
    result = {
        "file": file_path,
        "status": "处理失败",
        "error": None,
        "backup": None
    }
    
    try:
        # 创建备份
        if make_backup:
            backup_path = create_backup(file_path)
            if backup_path:
                result["backup"] = backup_path
                if logger:
                    logger.info(f"已创建备份: {backup_path}")
            else:
                result["error"] = "创建备份失败"
                if logger:
                    logger.error("创建备份失败，取消处理")
                return result
        
        # 读取文件内容
        content = read_file_safe(file_path)
        
        # 处理内容
        try:
            processed_content = processor_func(content)
            
            # 如果处理后内容有变化
            if processed_content != content:
                # 写回文件
                if write_file_safe(file_path, processed_content):
                    result["status"] = "已处理"
                    if logger:
                        logger.info(f"成功处理文件: {file_path}")
                else:
                    result["status"] = "写入失败"
                    result["error"] = "写入文件失败"
                    if logger:
                        logger.error(f"写入文件失败: {file_path}")
            else:
                result["status"] = "无需修改"
                if logger:
                    logger.info(f"文件无需修改: {file_path}")
        except Exception as e:
            result["error"] = f"处理内容时出错: {str(e)}"
            if logger:
                logger.error(f"处理文件内容时出错: {str(e)}")
        
        return result
    
    except Exception as e:
        result["error"] = str(e)
        if logger:
            logger.error(f"处理文件时出错: {str(e)}")
        return result

def stream_process_large_file(file_path, line_processor, make_backup=True, logger=None):
    """流式处理大文件
    
    Args:
        file_path (str): 文件路径
        line_processor (callable): 行处理函数，接收一行文本作为参数，返回处理后的行或None（删除该行）
        make_backup (bool): 是否创建备份
        logger: 可选的日志记录器
        
    Returns:
        dict: 处理结果
    """
    result = {
        "file": file_path,
        "status": "处理失败",
        "error": None,
        "backup": None,
        "lines_processed": 0,
        "lines_modified": 0
    }
    
    try:
        # 创建备份
        if make_backup:
            backup_path = create_backup(file_path)
            if backup_path:
                result["backup"] = backup_path
                if logger:
                    logger.info(f"已创建备份: {backup_path}")
            else:
                result["error"] = "创建备份失败"
                if logger:
                    logger.error("创建备份失败，取消处理")
                return result
        
        # 临时文件
        temp_file = file_path + ".tmp"
        
        # 流式处理
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as in_file, \
                 open(temp_file, 'w', encoding='utf-8') as out_file:
                
                line_count = 0
                modified_count = 0
                
                for line in in_file:
                    line_count += 1
                    
                    # 处理行
                    processed_line = line_processor(line)
                    
                    # 如果返回None，表示删除该行
                    if processed_line is not None:
                        out_file.write(processed_line)
                        # 检查是否修改了行
                        if processed_line != line:
                            modified_count += 1
            
            result["lines_processed"] = line_count
            result["lines_modified"] = modified_count
            
            # 替换原文件
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                if os.path.exists(file_path):
                    os.remove(file_path)
                os.rename(temp_file, file_path)
                result["status"] = "已处理"
                if logger:
                    logger.info(f"成功处理文件: {file_path} (处理 {line_count} 行，修改 {modified_count} 行)")
            else:
                # 临时文件创建失败
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                result["error"] = "生成的临时文件为空或不存在"
                if logger:
                    logger.error(f"生成的临时文件为空或不存在: {temp_file}")
        except Exception as e:
            # 确保清理临时文件
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            result["error"] = f"流式处理文件时出错: {str(e)}"
            if logger:
                logger.error(f"流式处理文件时出错: {str(e)}")
        
        return result
    
    except Exception as e:
        result["error"] = str(e)
        if logger:
            logger.error(f"处理文件时出错: {str(e)}")
        return result 

def process_maya_file_safely(file_path, processor_func, make_backup=True, logger=None):
    """安全处理Maya文件
    
    Args:
        file_path (str): Maya文件路径
        processor_func (callable): 处理函数，接收文件内容作为参数，返回处理后的内容
        make_backup (bool): 是否创建备份
        logger: 可选的日志记录器
        
    Returns:
        dict: 处理结果
    """
    result = {
        "file": file_path,
        "status": "处理失败",
        "error": None,
        "backup": None,
        "processed_nodes": []
    }
    
    # 确保是Maya文件
    if not file_path.lower().endswith('.ma'):
        result["error"] = "只能处理ASCII格式(.ma)的Maya文件"
        if logger:
            logger.error(f"只能处理ASCII格式(.ma)的Maya文件: {file_path}")
        return result
    
    try:
        # 创建备份
        if make_backup:
            backup_path = create_backup(file_path)
            if backup_path:
                result["backup"] = backup_path
                if logger:
                    logger.info(f"已创建备份: {backup_path}")
            else:
                result["error"] = "创建备份失败"
                if logger:
                    logger.error("创建备份失败，取消处理")
                return result
        
        # 读取文件内容
        content = read_file_safe(file_path)
        
        # 处理内容
        try:
            processed_content, processed_nodes = processor_func(content)
            result["processed_nodes"] = processed_nodes
            
            # 如果处理后内容有变化
            if processed_content != content:
                # 写回文件
                if write_file_safe(file_path, processed_content):
                    result["status"] = "已处理"
                    if logger:
                        logger.info(f"成功处理文件: {file_path}")
                else:
                    result["status"] = "写入失败"
                    result["error"] = "写入文件失败"
                    if logger:
                        logger.error(f"写入文件失败: {file_path}")
            else:
                result["status"] = "无需修改"
                if logger:
                    logger.info(f"文件无需修改: {file_path}")
        except Exception as e:
            result["error"] = f"处理内容时出错: {str(e)}"
            if logger:
                logger.error(f"处理文件内容时出错: {str(e)}")
            import traceback
            if logger:
                logger.error(f"详细错误: {traceback.format_exc()}")
        
        return result
    
    except Exception as e:
        result["error"] = str(e)
        if logger:
            logger.error(f"处理文件时出错: {str(e)}")
        import traceback
        if logger:
            logger.error(f"详细错误: {traceback.format_exc()}")
        return result 