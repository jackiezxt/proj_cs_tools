#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件处理工具 - 提供安全的文件读写和处理功能
"""

import os
import shutil
import datetime
from utils.common import read_file_with_encoding, write_file_with_encoding
from utils.logger import Logger

class FileProcessor:
    """文件处理器类 - 提供安全的文件读写和处理功能"""
    
    def __init__(self, log_path=None):
        """初始化文件处理器"""
        self.logger = Logger(log_path) if log_path else Logger()
    
    def process_file(self, file_path, processor_func, make_backup=True):
        """处理文件内容，支持备份和安全写入
        
        Args:
            file_path: 要处理的文件路径
            processor_func: 处理函数，接收文件内容，返回处理后的内容
            make_backup: 是否创建备份
            
        Returns:
            bool: 处理是否成功
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.logger.error("文件不存在: {}".format(file_path))
            return False
        
        # 创建备份
        if make_backup:
            backup_path = "{}.{}".format(file_path, datetime.datetime.now().strftime("%Y%m%d_%H%M%S.bak"))
            try:
                shutil.copy2(file_path, backup_path)
                self.logger.info("已创建备份: {}".format(backup_path))
            except Exception as e:
                self.logger.error("创建备份时出错: {}".format(str(e)))
                return False
        
        # 读取文件内容
        content, encoding = read_file_with_encoding(file_path, self.logger)
        if content is None:
            return False
        
        # 处理文件内容
        try:
            processed_content = processor_func(content)
            
            # 检查内容是否被修改
            if processed_content == content:
                self.logger.info("文件未修改: {}".format(file_path))
                return True
            
            # 写入处理后的内容
            success = write_file_with_encoding(file_path, processed_content, encoding, self.logger)
            if success:
                self.logger.info("文件处理成功: {}".format(file_path))
                return True
            else:
                self.logger.error("写入文件失败: {}".format(file_path))
                return False
                
        except Exception as e:
            self.logger.error("处理文件内容时出错: {}".format(str(e)))
            return False
    
    def stream_process_large_file(self, file_path, line_processor_func, make_backup=True, chunk_size=1024*1024):
        """流式处理大文件，逐行处理，减少内存占用
        
        Args:
            file_path: 要处理的文件路径
            line_processor_func: 行处理函数，接收文件行，返回处理后的行
            make_backup: 是否创建备份
            chunk_size: 每次读取的块大小
            
        Returns:
            bool: 处理是否成功
        """
        # 未完成实现 - 当前暂不需要
        self.logger.warning("流式处理大文件功能尚未完全实现")
        return False 