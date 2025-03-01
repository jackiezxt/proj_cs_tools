from .shot_asset_manager import ShotAssetManagerUI

# 确保全局变量在导入时就定义
_shot_asset_manager_instance = None

def show_shot_asset_manager():
    """显示镜头资产管理器窗口"""
    global _shot_asset_manager_instance
    # 如果已有实例，直接返回
    if _shot_asset_manager_instance is not None:
        try:
            _shot_asset_manager_instance.show()
            _shot_asset_manager_instance.raise_()
            _shot_asset_manager_instance.activateWindow()
            return _shot_asset_manager_instance
        except Exception:
            # 如果实例已经无效，则创建新实例
            pass
    
    # 创建新实例
    ui = ShotAssetManagerUI()
    ui.show()
    _shot_asset_manager_instance = ui
    return ui

__all__ = ['ShotAssetManagerUI', 'show_shot_asset_manager']