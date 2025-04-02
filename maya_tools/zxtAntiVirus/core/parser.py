import argparse
import sys

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Maya病毒扫描与清理工具')
    
    # 扫描模式选项
    parser.add_argument('--path', help='要扫描的文件或文件夹路径')
    parser.add_argument('--recursive', action='store_true', help='递归扫描文件夹')
    parser.add_argument('--scan-startup', action='store_true', help='扫描启动脚本')
    
    # 清理选项
    parser.add_argument('--clean', action='store_true', help='清理感染的文件')
    parser.add_argument('--backup', action='store_true', help='在清理前备份文件')
    
    # 场景清理选项
    parser.add_argument('--scene-cleanup', action='store_true', help='清理当前Maya场景中的病毒')
    
    # 系统清理选项
    parser.add_argument('--system-cleanup', action='store_true', help='清理系统中的Maya垃圾文件和插件(独立模式)')
    
    # GUI 模式
    parser.add_argument('--gui', action='store_true', help='启动图形界面模式')
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果没有指定参数，默认启动GUI
    if len(sys.argv) == 1:
        args.gui = True
    
    return args 