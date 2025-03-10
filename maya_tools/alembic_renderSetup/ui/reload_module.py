import sys
import importlib
import maya.cmds as mc
import os
import shutil

# 全局变量，用于跟踪UI实例
_shot_asset_manager_ui = None

def reload_shot_asset_manager():
    """重新加载镜头资产管理器模块"""
    global _shot_asset_manager_ui
    
    # 关闭已存在的窗口
    if _shot_asset_manager_ui is not None:
        try:
            _shot_asset_manager_ui.close()
            _shot_asset_manager_ui.deleteLater()
        except Exception as e:
            print(f"关闭窗口时出错: {str(e)}")
    
    # 设置为None，确保垃圾回收
    _shot_asset_manager_ui = None
    
    # 获取需要重新加载的模块（按照依赖顺序排列）
    module_names = [
        "maya_tools.alembic_renderSetup.core.config",
        "maya_tools.alembic_renderSetup.core.utils",
        "maya_tools.alembic_renderSetup.core.path_checker",
        "maya_tools.alembic_renderSetup.core.camera_manager",
        "maya_tools.alembic_renderSetup.core.render_manager",
        "maya_tools.alembic_renderSetup.core.asset_manager",
        "maya_tools.alembic_renderSetup.core",
        "maya_tools.alembic_renderSetup.ui.cache_browser",
        "maya_tools.alembic_renderSetup.ui.shot_asset_manager",
        "maya_tools.alembic_renderSetup.ui.__init__",
        "maya_tools.alembic_renderSetup.ui",
        "maya_tools.alembic_renderSetup"
    ]
    
    # 删除__pycache__目录
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, dirs, files in os.walk(base_path):
            if "__pycache__" in dirs:
                pycache_path = os.path.join(root, "__pycache__")
                print(f"删除缓存目录: {pycache_path}")
                shutil.rmtree(pycache_path)
    except Exception as e:
        print(f"删除__pycache__目录时出错: {str(e)}")
    
    # 先卸载模块，然后重新导入
    for module_name in module_names:
        if module_name in sys.modules:
            try:
                # 从sys.modules中删除模块
                del sys.modules[module_name]
                print(f"成功卸载模块: {module_name}")
            except Exception as e:
                mc.warning(f"卸载模块 {module_name} 时出错: {str(e)}")
    
    # 清理可能的循环引用
    import gc
    gc.collect()
    
    # 重新导入模块
    try:
        # 使用importlib重新导入核心模块
        importlib.import_module("maya_tools.alembic_renderSetup.core.config")
        importlib.import_module("maya_tools.alembic_renderSetup.core.utils")
        importlib.import_module("maya_tools.alembic_renderSetup.core.path_checker")
        importlib.import_module("maya_tools.alembic_renderSetup.core.camera_manager")
        importlib.import_module("maya_tools.alembic_renderSetup.core.render_manager")
        importlib.import_module("maya_tools.alembic_renderSetup.core.asset_manager")
        
        # 先导入缓存浏览器模块
        importlib.import_module("maya_tools.alembic_renderSetup.ui.cache_browser")
        
        # 重新导入UI模块
        importlib.import_module("maya_tools.alembic_renderSetup.ui.shot_asset_manager")
        ui_module = importlib.import_module("maya_tools.alembic_renderSetup.ui")
        
        # 最后导入主模块
        importlib.import_module("maya_tools.alembic_renderSetup")
        
        # 使用导入的模块创建UI
        _shot_asset_manager_ui = ui_module.show_shot_asset_manager()
        print("成功创建并显示新的镜头资产管理器窗口")
        
        return _shot_asset_manager_ui
    except Exception as e:
        mc.warning(f"创建UI时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# 为方便使用，可以创建一个快捷命令
def create_reload_command():
    """创建一个Maya命令用于重新加载模块"""
    from maya import cmds
    
    command_name = "reloadShotAssetManager"
    if cmds.runTimeCommand(command_name, q=True, exists=True):
        cmds.runTimeCommand(command_name, e=True, delete=True)
    
    cmds.runTimeCommand(
        command_name,
        annotation="重新加载镜头资产管理器",
        category="Custom",
        commandLanguage="python",
        command="import maya_tools.alembic_renderSetup.ui.reload_module as rm; importlib.reload(rm); rm.reload_shot_asset_manager()"
    )
    
    print(f"已创建命令: {command_name}")
    print("您可以在脚本编辑器中运行此命令，或为其分配快捷键")
