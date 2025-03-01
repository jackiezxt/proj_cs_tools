import maya.cmds as mc
from PySide2 import QtWidgets
import logging
import os

# 配置日志
logger = logging.getLogger('alembic_renderSetup')

def handle_error(error, status_label=None, show_warning=True):
    """统一错误处理"""
    error_msg = str(error)
    
    # 记录日志
    logger.error(error_msg)
    
    if show_warning:
        mc.warning(error_msg)
    if status_label:
        update_status(status_label, error_msg)
    return False

def update_status(status_label, message):
    """更新状态信息"""
    if status_label:
        status_label.setText(message)
        QtWidgets.QApplication.processEvents()

def set_frame_range(start_frame, end_frame):
    """设置帧范围"""
    mc.playbackOptions(min=start_frame, max=end_frame)
    mc.playbackOptions(animationStartTime=start_frame, animationEndTime=end_frame)


def show_progress(title, status, max_value):
    """显示进度条"""
    try:
        # 创建一个进度窗口而不是使用主进度条
        if mc.window("assetProgressWindow", exists=True):
            mc.deleteUI("assetProgressWindow")

        window = mc.window("assetProgressWindow", title=title, widthHeight=(300, 50))
        layout = mc.columnLayout(adjustableColumn=True)
        progress_bar = mc.progressBar(
            width=300,
            minValue=0,
            maxValue=max_value,
            progress=0,
            status=status,
            isInterruptable=True
        )
        mc.showWindow(window)
        return progress_bar
    except Exception as e:
        mc.warning(f"创建进度条时出错: {str(e)}")
        return None

def update_progress(progress_bar, step, message=None):
    """更新进度条"""
    if mc.progressBar(progress_bar, query=True, isCancelled=True):
        return False
    
    if message:
        mc.progressBar(progress_bar, edit=True, status=message)
    
    mc.progressBar(progress_bar, edit=True, step=1)
    return True

def end_progress(progress_bar):
    """结束进度条显示"""
    if progress_bar:
        try:
            # 如果是在独立窗口中，关闭窗口
            if mc.window("assetProgressWindow", exists=True):
                mc.deleteUI("assetProgressWindow")
        except:
            pass

def with_progress(title, message, steps, func, *args, **kwargs):
    """使用进度条执行函数"""
    progress_bar = show_progress(title, message, steps)
    try:
        result = func(progress_bar, *args, **kwargs)
        return result
    finally:
        end_progress(progress_bar)