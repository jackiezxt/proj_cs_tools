#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重载模块工具

提供了自动重载alembic_renderSetup工具包中所有模块的功能
"""

import sys
import importlib
import maya.cmds as mc
import os
import shutil
import inspect
import pkgutil
import traceback
from maya import OpenMaya

# 全局变量，用于跟踪UI实例
_shot_asset_manager_ui = None

def get_package_modules(package_name):
    """
    获取包中的所有模块
    
    参数:
        package_name (str): 包名称
        
    返回:
        list: 包中所有模块的完整名称列表
    """
    package = importlib.import_module(package_name)
    modules = []
    
    # 获取包目录
    if hasattr(package, '__path__'):
        package_path = package.__path__
    else:
        return modules
    
    # 遍历包中的所有模块
    for _, name, ispkg in pkgutil.iter_modules(package_path):
        module_name = f"{package_name}.{name}"
        
        # 添加模块
        if not ispkg:
            modules.append(module_name)
        # 递归处理子包
        else:
            try:
                subpackage_modules = get_package_modules(module_name)
                modules.extend(subpackage_modules)
                # 添加包本身
                modules.append(module_name)
            except ImportError:
                pass
    
    return modules

def get_module_dependencies(modules):
    """
    获取模块依赖关系并排序
    
    参数:
        modules (list): 模块名称列表
        
    返回:
        list: 按依赖顺序排列的模块名称列表
    """
    # 构建依赖图
    dependency_graph = {}
    imported_modules = {}
    
    # 获取当前已加载的模块
    for name in modules:
        if name in sys.modules:
            imported_modules[name] = sys.modules[name]
    
    # 分析依赖关系
    for name, module in imported_modules.items():
        dependencies = set()
        
        # 获取模块的所有导入
        if hasattr(module, '__file__'):
            try:
                with open(module.__file__, 'r', encoding='utf-8') as f:
                    code = f.read()
                    
                # 简单解析导入语句
                for line in code.split('\n'):
                    line = line.strip()
                    if line.startswith('from') and 'import' in line:
                        parts = line.split('from')[1].split('import')[0].strip()
                        if parts.startswith(modules[0].split('.')[0]):  # 只考虑项目内部依赖
                            dependencies.add(parts)
                    elif line.startswith('import'):
                        parts = line.split('import')[1].strip().split(',')
                        for part in parts:
                            part = part.strip().split(' ')[0]
                            if part.startswith(modules[0].split('.')[0]):  # 只考虑项目内部依赖
                                dependencies.add(part)
            except Exception:
                pass
        
        dependency_graph[name] = list(dependencies)
    
    # 拓扑排序
    def topological_sort(graph):
        visited = set()
        result = []
        
        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for dependency in graph.get(node, []):
                if dependency in graph:
                    dfs(dependency)
            result.append(node)
        
        for node in graph:
            dfs(node)
        
        return result
    
    # 执行拓扑排序
    sorted_modules = topological_sort(dependency_graph)
    
    # 添加未分析到的模块
    for module in modules:
        if module not in sorted_modules:
            sorted_modules.append(module)
    
    return sorted_modules

def reload_all_modules(base_package="maya_tools.alembic_renderSetup", clear_cache=True):
    """
    重新加载所有模块
    
    参数:
        base_package (str): 基础包名称
        clear_cache (bool): 是否清除缓存文件
    
    返回:
        list: 重新加载的模块列表
    """
    # 记录开始时间
    import time
    start_time = time.time()
    
    print(f"开始重载 {base_package} 模块...")
    
    # 检查Maya环境
    try:
        import maya.cmds as cmds
        print(f"Maya版本: {cmds.about(version=True)}")
        
        # 检查是否加载了XGen插件
        xgen_loaded = cmds.pluginInfo("xgenToolkit", query=True, loaded=True)
        print(f"XGen插件加载状态: {'已加载' if xgen_loaded else '未加载'}")
        
        if not xgen_loaded:
            print("注意: XGen插件未加载，这可能会影响XGen相关功能。可以使用以下命令加载:")
            print("import maya.cmds as cmds; cmds.loadPlugin('xgenToolkit')")
    except:
        print("无法获取Maya环境信息")
    
    # 获取所有模块
    try:
        all_modules = get_package_modules(base_package)
        print(f"找到 {len(all_modules)} 个模块")
        
        # 按依赖关系排序
        sorted_modules = get_module_dependencies(all_modules)
        
        # 打印依赖排序
        print("\n按依赖顺序排序的模块:")
        for i, module in enumerate(sorted_modules, 1):
            print(f"{i}. {module}")
        print()
        
        # 清除缓存目录
        if clear_cache:
            try:
                # 获取基础包的目录
                base_module = importlib.import_module(base_package)
                if hasattr(base_module, '__path__'):
                    base_path = base_module.__path__[0]
                    
                print(f"查找缓存目录: {base_path}")
                cache_dirs_removed = 0
                
                # 遍历查找__pycache__目录
                for root, dirs, files in os.walk(base_path):
                    if "__pycache__" in dirs:
                        pycache_path = os.path.join(root, "__pycache__")
                        try:
                            shutil.rmtree(pycache_path)
                            cache_dirs_removed += 1
                        except Exception as e:
                            print(f"无法删除缓存目录 {pycache_path}: {str(e)}")
                
                print(f"已删除 {cache_dirs_removed} 个缓存目录")
            except Exception as e:
                print(f"清除缓存时出错: {str(e)}")
        
        # 删除模块
        removed_modules = []
        for module_name in reversed(sorted_modules):
            if module_name in sys.modules:
                try:
                    del sys.modules[module_name]
                    removed_modules.append(module_name)
                except Exception as e:
                    print(f"删除模块 {module_name} 时出错: {str(e)}")
        
        print(f"已删除 {len(removed_modules)} 个模块")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 重新导入模块
        reloaded_modules = []
        for module_name in sorted_modules:
            try:
                importlib.import_module(module_name)
                reloaded_modules.append(module_name)
            except Exception as e:
                print(f"重新导入模块 {module_name} 时出错: {str(e)}")
                traceback.print_exc()
        
        end_time = time.time()
        print(f"重载完成! 耗时: {end_time - start_time:.2f} 秒")
        print(f"成功重载 {len(reloaded_modules)}/{len(sorted_modules)} 个模块")
        
        # 如果有模块未能重载，打印未重载的模块
        if len(reloaded_modules) < len(sorted_modules):
            not_reloaded = set(sorted_modules) - set(reloaded_modules)
            print("\n以下模块未能重载:")
            for module in not_reloaded:
                print(f"- {module}")
        
        return reloaded_modules
        
    except Exception as e:
        print(f"获取模块列表时出错: {str(e)}")
        traceback.print_exc()
        return []

def reload_shot_asset_manager():
    """
    重新加载镜头资产管理器模块并重新创建UI
    
    返回:
        object: 新创建的UI实例
    """
    global _shot_asset_manager_ui
    
    # 关闭已存在的窗口
    if _shot_asset_manager_ui is not None:
        try:
            _shot_asset_manager_ui.close()
            _shot_asset_manager_ui.deleteLater()
            print("已关闭现有窗口")
        except Exception as e:
            print(f"关闭窗口时出错: {str(e)}")
    
    # 设置为None，确保垃圾回收
    _shot_asset_manager_ui = None
    
    # 重载所有模块
    reload_all_modules("maya_tools.alembic_renderSetup")
    
    try:
        # 重新导入UI模块
        ui_module = importlib.import_module("maya_tools.alembic_renderSetup.ui")
        
        # 创建并显示UI
        _shot_asset_manager_ui = ui_module.show_shot_asset_manager()
        OpenMaya.MGlobal.displayInfo("成功创建并显示新的镜头资产管理器窗口")
        
        return _shot_asset_manager_ui
    except Exception as e:
        mc.warning(f"创建UI时出错: {str(e)}")
        traceback.print_exc()
        return None

def reload_specific_module(module_name):
    """
    重新加载指定模块
    
    参数:
        module_name (str): 要重载的模块名称
        
    返回:
        module: 重新加载的模块
    """
    try:
        # 检查模块是否已加载
        if module_name in sys.modules:
            # 删除模块
            del sys.modules[module_name]
            print(f"已删除模块: {module_name}")
        
        # 重新导入模块
        module = importlib.import_module(module_name)
        print(f"已重新加载模块: {module_name}")
        
        return module
    except Exception as e:
        print(f"重载模块 {module_name} 时出错: {str(e)}")
        traceback.print_exc()
        return None

def create_reload_command():
    """创建Maya命令用于重新加载模块"""
    from maya import cmds
    
    command_name = "reloadShotAssetManager"
    if cmds.runTimeCommand(command_name, q=True, exists=True):
        cmds.runTimeCommand(command_name, e=True, delete=True)
    
    cmds.runTimeCommand(
        command_name,
        annotation="重新加载镜头资产管理器",
        category="Custom",
        commandLanguage="python",
        command="import importlib; import maya_tools.alembic_renderSetup.ui.reload_module as rm; importlib.reload(rm); rm.reload_shot_asset_manager()"
    )
    
    print(f"已创建命令: {command_name}")
    print("您可以在脚本编辑器中运行此命令，或为其分配快捷键")

if __name__ == "__main__":
    # 如果直接运行此脚本，执行重载
    reload_shot_asset_manager()
