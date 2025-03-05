import maya.cmds as mc
from PySide2 import QtWidgets
import logging
import os
from maya_tools.common.maya_utils import (
    handle_error, 
    show_progress, 
    update_progress, 
    end_progress
)

# 配置日志
logger = logging.getLogger('alembic_renderSetup')

# 重新导出这些函数以保持向后兼容性
__all__ = ['handle_error', 'show_progress', 'update_progress', 'end_progress', 'with_progress']

def update_status(status_label, message):
    """更新状态信息"""
    if status_label:
        status_label.setText(message)
        QtWidgets.QApplication.processEvents()

def set_frame_range(start_frame, end_frame):
    """设置帧范围"""
    mc.playbackOptions(min=start_frame, max=end_frame)
    mc.playbackOptions(animationStartTime=start_frame, animationEndTime=end_frame)

def with_progress(title, message, steps, func, *args, **kwargs):
    """使用进度条执行函数"""
    progress_bar = show_progress(title, message, steps)
    try:
        result = func(progress_bar, *args, **kwargs)
        return result
    finally:
        end_progress(progress_bar)