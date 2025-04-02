# -*- coding: utf-8 -*-
"""
日志记录工具
提供日志记录功能
"""
import os
import datetime
import logging

class Logger:
    """日志记录器"""
    
    def __init__(self, log_path=None):
        """初始化日志记录器
        
        Args:
            log_path: 日志文件路径，如果为None则使用默认路径
        """
        # 如果未指定日志路径，使用默认路径
        if log_path is None:
            log_dir = os.path.expanduser("~/Documents/zxtAntiVirus/logs")
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = os.path.join(log_dir, f"zxtAntiVirus_{timestamp}.log")
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_path)
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志记录器
        self.logger = logging.getLogger("zxtAntiVirus")
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复处理程序
        if not self.logger.handlers:
            # 文件处理程序
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # 控制台处理程序
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 格式化程序
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                          datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加处理程序
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.log_path = log_path
        self.info(f"初始化日志记录器，日志文件: {log_path}")
    
    def debug(self, message):
        """记录调试信息"""
        self.logger.debug(message)
    
    def info(self, message):
        """记录一般信息"""
        self.logger.info(message)
    
    def warning(self, message):
        """记录警告信息"""
        self.logger.warning(message)
    
    def error(self, message):
        """记录错误信息"""
        self.logger.error(message)
    
    def critical(self, message):
        """记录严重错误信息"""
        self.logger.critical(message)
    
    def get_log_path(self):
        """获取日志文件路径"""
        return self.log_path 