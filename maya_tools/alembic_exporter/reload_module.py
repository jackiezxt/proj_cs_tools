"""
重载工具模块 - 为alembic_exporter专门设计

提供系统化的方法来重载alembic_exporter包及其所有子模块，
确保按照正确的依赖顺序重载，并处理缓存问题。
"""

import sys
import os
import importlib
import pkgutil
import inspect
import time
import shutil
import types
import re
from collections import defaultdict


def get_package_modules(package_name):
    """
    获取指定包名下的所有模块

    参数:
        package_name (str): 包名，如'maya_tools.alembic_exporter'

    返回:
        list: 模块名称列表
    """
    modules = []

    # 导入主包
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        print(f"无法导入包 {package_name}")
        return modules

    # 获取包路径
    if hasattr(package, '__path__'):
        pkg_path = package.__path__
    else:
        print(f"{package_name} 不是一个包")
        return modules

    # 遍历包中的所有模块
    for _, name, is_pkg in pkgutil.walk_packages(pkg_path, package_name + '.'):
        # 将模块加入列表
        if not is_pkg:  # 只处理模块，不处理子包
            modules.append(name)
        else:  # 对于子包，递归获取其中的模块
            sub_modules = get_package_modules(name)
            modules.extend(sub_modules)

    # 添加主包
    if package_name not in modules:
        modules.append(package_name)

    return modules


def get_module_dependencies(modules):
    """
    分析模块之间的依赖关系并按拓扑排序返回重载顺序

    参数:
        modules (list): 模块名称列表

    返回:
        list: 按依赖顺序排序的模块列表
    """
    # 构建依赖图
    graph = defaultdict(list)
    all_modules = set(modules)

    # 为每个模块找出其依赖
    for module_name in modules:
        try:
            # 导入模块
            module = importlib.import_module(module_name)

            # 检查模块中的所有对象
            for name, obj in inspect.getmembers(module):
                # 如果是从其他模块导入的对象
                if inspect.ismodule(obj):
                    dependency = obj.__name__
                    # 如果依赖也在我们的模块列表中
                    if dependency in all_modules and dependency != module_name:
                        graph[module_name].append(dependency)
        except (ImportError, AttributeError):
            print(f"无法分析模块 {module_name} 的依赖")

    # 进行拓扑排序
    def topological_sort(graph):
        """对有向无环图进行拓扑排序"""
        visited = set()
        temp_mark = set()  # 用于检测循环
        result = []

        def dfs(node):
            """深度优先搜索"""
            if node in temp_mark:
                # 检测到循环依赖
                print(f"警告: 检测到循环依赖于 {node}")
                return
            if node not in visited:
                temp_mark.add(node)

                # 访问所有依赖
                for dependency in graph[node]:
                    dfs(dependency)

                temp_mark.remove(node)
                visited.add(node)
                result.append(node)

        # 对图中每个节点进行DFS
        for node in list(graph.keys()):
            if node not in visited:
                dfs(node)

        # 因为我们需要从基础模块开始重载，所以反转结果
        result.reverse()
        return result

    # 进行拓扑排序
    sorted_modules = topological_sort(graph)

    # 添加未包含在依赖图中的模块
    for module in modules:
        if module not in sorted_modules:
            sorted_modules.append(module)

    return sorted_modules


def reload_all_modules(base_package="maya_tools.alembic_exporter", clear_cache=True):
    """
    重新加载指定包的所有模块，按照依赖顺序进行重载

    参数:
        base_package (str): 基础包名称
        clear_cache (bool): 是否清除缓存文件

    返回:
        list: 重新加载的模块列表
    """
    # 记录开始时间
    start_time = time.time()

    print(f"\n======== 开始重载 {base_package} 模块 ========")

    # 检查Maya环境
    try:
        import maya.cmds as mc
        print(f"Maya版本: {mc.about(version=True)}")
    except:
        print("无法获取Maya环境信息")

    # 清除__pycache__
    if clear_cache:
        try:
            # 获取包的路径
            package = importlib.import_module(base_package)
            if hasattr(package, '__path__'):
                pkg_path = package.__path__[0]
                # 遍历包路径查找并删除__pycache__
                for root, dirs, files in os.walk(pkg_path):
                    for dir_name in dirs:
                        if dir_name == "__pycache__":
                            cache_path = os.path.join(root, dir_name)
                            print(f"删除缓存目录: {cache_path}")
                            shutil.rmtree(cache_path, ignore_errors=True)
                print("已清除所有__pycache__目录")
        except Exception as e:
            print(f"清除缓存时出错: {e}")

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

        # 从sys.modules中移除所有相关模块
        removed = 0
        for key in list(sys.modules.keys()):
            if key.startswith(base_package):
                del sys.modules[key]
                removed += 1
        print(f"\n从sys.modules中移除了 {removed} 个模块")

        # 重新导入和重载模块
        reloaded_modules = []
        for module_name in sorted_modules:
            try:
                module = importlib.import_module(module_name)
                reloaded_modules.append(module)
                print(f"已重载: {module_name}")
            except ImportError as e:
                print(f"无法重载 {module_name}: {e}")

        # 计算耗时
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"\n重载完成, 共耗时 {elapsed:.2f} 秒")

        print(f"成功重载 {len(reloaded_modules)}/{len(sorted_modules)} 个模块")
        print("========== 重载完成 ==========\n")

        # 返回重载的模块
        return reloaded_modules
    except Exception as e:
        print(f"重载过程中出错: {e}")
        print("========== 重载失败 ==========\n")
        return []


def show_ui_after_reload():
    """重载模块后显示UI"""
    try:
        from maya_tools.alembic_exporter import show_window
        window = show_window()
        print("已显示Alembic导出工具窗口")
        return window
    except Exception as e:
        print(f"显示UI窗口时出错: {e}")
        return None


def run_test_after_reload():
    """重载模块后运行测试"""
    try:
        from maya_tools.alembic_exporter.fur_export_test import run_tests
        run_tests()
        print("已运行毛发导出测试")
    except Exception as e:
        print(f"运行测试时出错: {e}")


def reload_and_show():
    """重载所有模块并显示UI"""
    modules = reload_all_modules()
    if modules:
        return show_ui_after_reload()
    return None


def reload_alembic_exporter():
    """
    重载alembic_exporter包及所有子模块
    
    返回:
        窗口实例或None
    """
    base_package = "maya_tools.alembic_exporter"
    print("\n========== 开始重载 Alembic导出工具 ==========")
    
    # 1. 清除Python缓存
    try:
        # 获取包路径
        import maya_tools.alembic_exporter
        pkg_path = os.path.dirname(maya_tools.alembic_exporter.__file__)
        print(f"包路径: {pkg_path}")
        
        # 删除所有__pycache__目录
        for root, dirs, files in os.walk(pkg_path):
            if "__pycache__" in dirs:
                cache_path = os.path.join(root, "__pycache__")
                print(f"删除缓存: {cache_path}")
                try:
                    shutil.rmtree(cache_path)
                except Exception as e:
                    print(f"清除缓存出错: {e}")
        
        print("✓ 已清除Python缓存")
    except Exception as e:
        print(f"查找或清除缓存时出错: {e}")
    
    # 2. 从sys.modules中移除所有相关模块
    modules_to_remove = []
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(base_package):
            modules_to_remove.append(module_name)
    
    for module_name in modules_to_remove:
        try:
            del sys.modules[module_name]
        except KeyError:
            pass
    
    print(f"✓ 已从sys.modules中移除 {len(modules_to_remove)} 个模块")
    
    # 3. 按顺序重新导入模块
    try:
        # 核心模块
        import maya_tools.alembic_exporter.core.helpers
        import maya_tools.alembic_exporter.core.settings
        import maya_tools.alembic_exporter.core.scene_info
        import maya_tools.alembic_exporter.core.xgen_guides
        print("✓ 已重新导入核心模块")
        
        # 导出模块
        import maya_tools.alembic_exporter.export
        print("✓ 已重新导入export模块")
        
        # UI模块
        import maya_tools.alembic_exporter.ui.gui
        print("✓ 已重新导入UI模块")
        
        # 主模块
        import maya_tools.alembic_exporter
        print("✓ 已重新导入主模块")
        
        # 单独导入测试模块
        sys.path.append(os.path.dirname(pkg_path))
        try:
            from maya_tools.alembic_exporter import fur_export_test
            print("✓ 已重新导入测试模块")
        except ImportError as e:
            print(f"导入测试模块时出错 (不影响主功能): {e}")
    except Exception as e:
        print(f"重新导入模块时出错: {e}")
        print("========== 重载失败 ==========\n")
        return None
    
    # 4. 显示UI
    try:
        from maya_tools.alembic_exporter import show_window
        window = show_window()
        print("✓ 已显示Alembic导出工具窗口")
        print("========== 重载完成 ==========\n")
        return window
    except Exception as e:
        print(f"显示窗口时出错: {e}")
        print("========== 重载失败 ==========\n")
        return None


def run_test():
    """运行毛发导出测试"""
    try:
        from maya_tools.alembic_exporter.fur_export_test import run_tests
        run_tests()
    except Exception as e:
        print(f"运行测试时出错: {e}")


if __name__ == "__main__":
    # 如果直接运行此脚本，则重载所有模块并显示UI
    reload_alembic_exporter()