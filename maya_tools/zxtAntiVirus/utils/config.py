#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置模块 - 用于存储工具的全局配置
"""

import os
import json
import tempfile
import datetime

# 基本配置
CONFIG = {
    # 工具信息
    'tool_name': 'Maya病毒扫描与清理工具',
    'version': '1.0.0',
    'author': 'zxt',
    'date': '2023-12-01',
    
    # 文件扩展名
    'maya_extensions': ['.ma', '.mb'],
    'script_extensions': ['.py', '.mel'],
    
    # 备份设置
    'create_backup': True,
    'backup_suffix': '_clean_backup',
    'backup_directory': os.path.join(tempfile.gettempdir(), 'maya_virus_backups'),
    
    # 日志设置
    'log_directory': os.path.join(tempfile.gettempdir(), 'maya_virus_logs'),
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # 界面设置
    'ui_width': 800,
    'ui_height': 600,
    'ui_title': 'Maya病毒扫描与清理工具',
    
    # 扫描设置
    'max_scan_depth': 5,  # 递归扫描的最大深度
    'max_file_size': 100 * 1024 * 1024,  # 最大扫描文件大小 (100 MB)
    'scan_timeout': 60,  # 单个文件扫描超时时间(秒)
    
    # 清理设置
    'clean_mode': 'safe',  # 'safe', 'thorough', 'aggressive'
    'auto_clean': False,  # 是否自动清理
}

def load_config(config_file=None):
    """加载配置文件，如果配置文件不存在则使用默认配置"""
    global CONFIG
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                CONFIG.update(user_config)
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
    
    # 确保目录存在
    for dir_key in ['backup_directory', 'log_directory']:
        if not os.path.exists(CONFIG[dir_key]):
            try:
                os.makedirs(CONFIG[dir_key])
            except Exception as e:
                print(f"创建目录 {CONFIG[dir_key]} 时出错: {e}")
    
    return CONFIG

def save_config(config_file, config=None):
    """保存配置到文件"""
    if config is None:
        config = CONFIG
    
    try:
        # 确保目录存在
        config_dir = os.path.dirname(config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"保存配置文件时出错: {e}")
        return False

def get_backup_path(file_path):
    """获取备份文件路径"""
    file_name = os.path.basename(file_path)
    base_name, ext = os.path.splitext(file_name)
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{base_name}{CONFIG['backup_suffix']}_{date_str}{ext}"
    return os.path.join(CONFIG['backup_directory'], backup_name)

def get_log_path():
    """获取日志文件路径"""
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(CONFIG['log_directory'], f"virus_scan_{date_str}.log")

def get_report_path():
    """获取报告文件路径"""
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(CONFIG['log_directory'], f"virus_scan_report_{date_str}.html")

# 确保配置已加载
load_config() 