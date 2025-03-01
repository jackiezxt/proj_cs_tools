import importlib
import maya.cmds as mc

# 全局变量，用于跟踪UI实例
_shot_asset_manager_ui = None

def show_ui():
    """显示镜头资产管理器界面"""
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
    
    try:
        # 导入UI模块
        from .ui import shot_asset_manager
        
        # 创建并显示UI
        _shot_asset_manager_ui = shot_asset_manager.ShotAssetManagerUI()
        _shot_asset_manager_ui.show()
        
        print("成功显示镜头资产管理器窗口")
        return _shot_asset_manager_ui
    except Exception as e:
        mc.warning(f"创建UI时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# 为了向后兼容，添加别名
show_shot_asset_manager = show_ui