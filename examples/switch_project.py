"""
项目配置切换工具

此脚本提供简单的函数来切换不同项目的配置文件。
可以在Maya中运行或作为独立脚本运行。
"""

import os
import sys
import json

def switch_to_project(project_name):
    """
    切换到指定的项目配置
    
    Args:
        project_name: 项目名称，如 "ProjectA" 或 "ProjectB"
    
    Returns:
        成功返回True，失败返回False
    """
    # 检查examples目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建项目配置文件路径
    config_path = os.path.join(current_dir, f"project_{project_name.lower()}_config.json")
    
    if not os.path.exists(config_path):
        print(f"错误: 找不到项目配置文件: {config_path}")
        return False
    
    # 设置环境变量
    os.environ["MAYA_TOOLS_PROJECT_CONFIG"] = config_path
    print(f"已设置项目配置: {project_name}")
    print(f"配置文件路径: {config_path}")
    
    # 如果在Maya中运行，尝试重新加载配置
    try:
        from maya_tools.alembic_renderSetup.core.config import reload_config
        reload_config()
        print(f"已重新加载项目 '{project_name}' 的配置")
        return True
    except ImportError:
        print("提示: 在Maya中运行此脚本可自动重新加载配置")
        print("在启动Maya前设置环境变量:")
        print(f"  set MAYA_TOOLS_PROJECT_CONFIG={config_path}")
        return True

def list_available_projects():
    """
    列出可用的项目配置
    
    Returns:
        项目配置列表
    """
    projects = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for file in os.listdir(current_dir):
        if file.startswith("project_") and file.endswith("_config.json"):
            project_name = file[8:-12]  # 提取project_X_config.json中的X
            
            # 读取项目名称
            try:
                with open(os.path.join(current_dir, file), 'r') as f:
                    config = json.load(f)
                    display_name = config.get("project_name", project_name.upper())
                    projects.append((project_name, display_name))
            except:
                projects.append((project_name, project_name.upper()))
    
    return projects

def show_menu():
    """显示交互式菜单"""
    projects = list_available_projects()
    
    if not projects:
        print("未找到项目配置文件。请在examples目录中创建project_x_config.json文件。")
        return
    
    print("\n可用项目配置:")
    for i, (id_name, display_name) in enumerate(projects, 1):
        print(f"{i}. {display_name} ({id_name})")
    
    try:
        choice = int(input("\n请选择项目 [1-{}]: ".format(len(projects))))
        if 1 <= choice <= len(projects):
            switch_to_project(projects[choice-1][0])
        else:
            print("无效选择")
    except ValueError:
        print("请输入数字")

if __name__ == "__main__":
    # 如果没有参数，显示菜单
    if len(sys.argv) == 1:
        show_menu()
    # 否则使用第一个参数作为项目名称
    else:
        switch_to_project(sys.argv[1]) 