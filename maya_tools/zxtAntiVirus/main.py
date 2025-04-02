#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Maya病毒扫描清理工具 - 主程序
"""
import os
import sys
import traceback
import logging
import datetime
import argparse

# 添加当前目录到系统路径，确保能够导入所需模块
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# 确保正确处理编码
if hasattr(sys, 'setdefaultencoding'):
    sys.setdefaultencoding('utf-8')

# 设置全局异常处理
def global_exception_handler(exc_type, exc_value, exc_tb):
    """全局异常处理函数"""
    print("\n======= 错误 =======")
    print(f"错误类型: {exc_type.__name__}")
    print(f"错误信息: {exc_value}")
    print("")
    print("堆栈跟踪:")
    for line in traceback.format_tb(exc_tb):
        print(f"  {line.strip()}")
    print("")
    print("请报告此错误。")
    print("=====================\n")
    
    # 也记录到日志文件
    try:
        from utils.logger import Logger
        logger = Logger()
        logger.error(f"未捕获的异常: {exc_type.__name__} - {exc_value}")
        logger.error("异常堆栈:")
        for line in traceback.format_tb(exc_tb):
            logger.error(line.strip())
    except:
        pass
    
sys.excepthook = global_exception_handler

# 主程序执行
def main():
    """主程序入口"""
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description="Maya病毒扫描与清理工具")
        parser.add_argument("--scan", action="store_true", help="扫描Maya文件或目录")
        parser.add_argument("--clean", action="store_true", help="清理Maya文件中的病毒")
        parser.add_argument("--path", type=str, help="要扫描或清理的Maya文件或目录路径")
        parser.add_argument("--gui", action="store_true", help="启动图形用户界面")
        parser.add_argument("--all", action="store_true", help="扫描和清理所有相关目录")
        parser.add_argument("--log", type=str, help="指定日志文件路径")
        
        args = parser.parse_args()
        
        # 设置日志文件路径
        log_path = args.log
        if not log_path:
            # 默认存放在用户文档目录
            log_dir = os.path.expanduser("~/Documents/zxtAntiVirus/logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            log_path = os.path.join(log_dir, "zxtAntiVirus_{}.log".format(
                datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
        
        # 初始化日志
        from utils.logger import Logger
        logger = Logger(log_path)
        logger.info("初始化日志记录器，日志文件: {}".format(log_path))
        
        # 根据参数决定执行模式
        if args.gui:
            run_gui(log_path)
        else:
            run_cli(args, log_path)
            
    except Exception as e:
        print(f"程序启动时出错: {str(e)}")
        traceback.print_exc()
        print("请尝试使用--gui参数启动图形界面")
        return 1
        
    return 0

def run_cli(args, log_path):
    """运行命令行模式"""
    from utils.logger import Logger
    logger = Logger(log_path)
    
    if args.scan or args.all:
        from core.scanner import VirusScanner
        scanner = VirusScanner(log_path)
        
        if args.path:
            # 扫描指定路径
            path = os.path.abspath(args.path)
            logger.info(f"开始扫描: {path}")
            
            if os.path.isfile(path):
                results = scanner.scan_file(path)
            elif os.path.isdir(path):
                results = scanner.scan_directory(path)
            else:
                logger.error(f"指定的路径不存在: {path}")
                return
                
            logger.info(f"扫描完成。检测到 {len(results.get('infected_files', []))} 个感染文件")
            
        elif args.all:
            # 扫描所有相关目录
            logger.info("开始全面扫描...")
            results = scanner.scan_all()
            logger.info(f"全面扫描完成。检测到 {len(results.get('infected_files', []))} 个感染文件")
        
    if args.clean or args.all:
        from core.cleaner import VirusCleaner
        cleaner = VirusCleaner(log_path)
        
        if args.path:
            # 清理指定路径
            path = os.path.abspath(args.path)
            logger.info(f"开始清理: {path}")
            
            if os.path.isfile(path):
                if os.path.splitext(path)[1].lower() in ['.ma', '.mb']:
                    cleaner.clean_file(path)
                else:
                    logger.error(f"指定的文件不是Maya文件: {path}")
            elif os.path.isdir(path):
                # 清理目录中的脚本文件
                results = {}  # 创建一个空的结果字典传递给方法
                cleaner._clean_standalone_scripts_dir(path, results)
            else:
                logger.error(f"指定的路径不存在: {path}")
            
        elif args.all:
            # 执行全面清理
            logger.info("开始全面清理...")
            results = cleaner.clean_system()
            logger.info("全面清理完成")
            
            # 打印清理摘要
            cleaned_count = len(cleaner.results.get("cleaned_files", []))
            deleted_count = len(cleaner.results.get("deleted_files", []))
            backup_count = len(cleaner.results.get("backup_files", []))
            failed_count = len(cleaner.results.get("failed_files", []))
            
            logger.info(f"清理摘要: 清理文件 {cleaned_count}, 删除文件 {deleted_count}, 备份文件 {backup_count}, 失败 {failed_count}")

def run_gui(log_path):
    """运行图形界面模式"""
    from utils.logger import Logger
    logger = Logger(log_path)
    logger.info("启动图形用户界面")
    
    try:
        # 直接使用独立UI
        logger.info("启动独立UI界面")
        from ui.standalone_ui import show_ui
        show_ui(log_path)
        return
            
    except Exception as e:
        logger.error(f"启动UI时出错: {str(e)}")
        logger.error(traceback.format_exc())
        print("启动图形界面失败，将自动切换到命令行模式执行扫描和清理")
        
        # 如果UI启动失败，回退到命令行模式
        from core.scanner import VirusScanner
        from core.cleaner import VirusCleaner
        
        # 初始化扫描器
        scanner = VirusScanner(log_path)
        logger.info("开始全面扫描...")
        scan_results = scanner.scan_all()
        logger.info(f"全面扫描完成。检测到 {len(scan_results.get('infected_files', []))} 个感染文件")
        
        # 初始化清理器
        cleaner = VirusCleaner(log_path)
        logger.info("开始全面清理...")
        cleaner.clean_system()
        logger.info("全面清理完成")
        
        # 打印清理摘要
        cleaned_count = len(cleaner.results.get("cleaned_files", []))
        deleted_count = len(cleaner.results.get("deleted_files", []))
        backup_count = len(cleaner.results.get("backup_files", []))
        failed_count = len(cleaner.results.get("failed_files", []))
        
        logger.info(f"清理摘要: 清理文件 {cleaned_count}, 删除文件 {deleted_count}, 备份文件 {backup_count}, 失败 {failed_count}")
        
        print(f"\n扫描和清理完成！\n清理文件: {cleaned_count}, 删除文件: {deleted_count}, 备份文件: {backup_count}, 失败: {failed_count}")

if __name__ == "__main__":
    print("Starting Maya Virus Scanner...")
    
    # 检查是否运行在mayapy环境
    maya_py = False
    for path in sys.path:
        if "maya" in path.lower() and os.path.exists(os.path.join(path, "maya", "mel.py")):
            maya_py = True
            print("\nUsing Maya Python: {}\n".format(sys.executable))
            break
    
    if not maya_py:
        print("\nRunning with system Python: {}\n".format(sys.executable))
    
    print("Note: If problems persist, try running as administrator.\n")
    
    sys.exit(main()) 