import maya.cmds as mc
from PySide2 import QtWidgets
import os
import logging

# 配置日志
logger = logging.getLogger('maya_tools')

def handle_error(error, status_label=None, show_warning=True):
    """统一错误处理"""
    error_msg = str(error)
    
    # 记录日志
    logger.error(error_msg)
    
    if show_warning:
        mc.warning(error_msg)
    if status_label:
        try:
            status_label.setText(error_msg)
            status_label.setStyleSheet("color: red")
        except:
            pass
    return error_msg

def show_progress(title, message, max_value, parent=None):
    """显示进度条"""
    if parent:
        progress_bar = QtWidgets.QProgressBar(parent)
        progress_bar.setMaximum(max_value)
        progress_bar.setFormat("%v/%m - %p% - %s")
        progress_bar.setTextVisible(True)
        
        # 如果提供了父窗口，则返回QProgressBar对象
        return progress_bar
    else:
        # 否则使用Maya的进度窗口
        if mc.window("assetProgressWindow", exists=True):
            mc.deleteUI("assetProgressWindow")
            
        progress_bar = mc.progressWindow(
            title=title,
            progress=0,
            status=message,
            isInterruptable=True,
            max=max_value
        )
        return progress_bar

def update_progress(progress_bar, value=None, message=None):
    """更新进度条"""
    if isinstance(progress_bar, QtWidgets.QProgressBar):
        # 处理PySide2进度条
        if value is not None:
            progress_bar.setValue(value)
        if message:
            progress_bar.setFormat(f"%v/%m - %p% - {message}")
        return True
    else:
        # 处理Maya进度条
        if mc.progressWindow(progress_bar, query=True, isCancelled=True):
            return False
            
        if value is not None:
            mc.progressWindow(progress_bar, edit=True, progress=value)
        
        if message:
            mc.progressWindow(progress_bar, edit=True, status=message)
        
        return True

def end_progress(progress_bar):
    """结束进度条显示"""
    if isinstance(progress_bar, QtWidgets.QProgressBar):
        # 处理PySide2进度条
        progress_bar.setValue(progress_bar.maximum())
    else:
        # 处理Maya进度条
        try:
            if mc.window("assetProgressWindow", exists=True):
                mc.deleteUI("assetProgressWindow")
        except:
            pass

def import_reference(file_path, namespace=None, preserve_references=True):
    """导入引用文件"""
    try:
        if not os.path.exists(file_path):
            raise ValueError(f"文件不存在: {file_path}")
            
        # 检查文件是否已经被引用
        ref_nodes = mc.ls(type='reference') or []
        for ref in ref_nodes:
            try:
                if mc.referenceQuery(ref, filename=True).replace('\\', '/') == file_path.replace('\\', '/'):
                    print(f"文件已经导入: {file_path}")
                    return True
            except:
                continue
                
        # 导入文件
        if namespace:
            mc.file(file_path, i=True, namespace=namespace, preserveReferences=preserve_references)
        else:
            mc.file(file_path, i=True, preserveReferences=preserve_references)
            
        return True
    except Exception as e:
        error_msg = f"导入文件时出错: {str(e)}"
        mc.warning(error_msg)
        return False 