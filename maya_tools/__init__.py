"""
Maya工具集合
包含以下功能:
- Alembic导出工具
- 材质赋予工具
- 渲染设置工具
- 模型检查工具
- 场景清理工具
- UV检查工具
"""

# 模块级别的窗口引用
_alembic_exporter_window = None
_render_setup_window = None
_model_check_window = None
_scene_clean_window = None
_uv_check_window = None
_mtl_ui_window = None

def show_alembic_exporter():
    """显示Alembic导出工具UI"""
    from maya_tools import alembic_exporter
    from maya_tools.alembic_exporter.ui.gui import show_window
    
    # 创建窗口并保存引用
    window = show_window()
    
    # 将窗口引用保存到模块级别的变量中
    global _alembic_exporter_window
    _alembic_exporter_window = window
    
    return window


def show_render_setup():
    """显示渲染设置工具UI"""
    from maya_tools.alembic_renderSetup import show_ui
    global _render_setup_window
    _render_setup_window = show_ui()
    return _render_setup_window


def assign_mtl():
    """执行材质赋予"""
    from maya_tools.alembic_mtl import assign_materials
    return assign_materials()


def show_model_check():
    """显示模型检查工具UI"""
    from maya_tools.model_check import show_window
    return show_window()


def show_scene_clean():
    """显示场景清理工具UI"""
    from maya_tools.scene_clean import zxtSCNclearUp
    import importlib
    importlib.reload(zxtSCNclearUp)
    return zxtSCNclearUp.build_ui()


def show_uv_check():
    """显示UV检查工具UI"""
    from maya_tools.uv_check import zxtUVsetModify
    import importlib
    importlib.reload(zxtUVsetModify)
    zxtUV = zxtUVsetModify.zxtUVSetTool()
    return zxtUV.windows_zxtUVSetModify()


def show_mtl_ui():
    """显示材质赋予UI工具"""
    from maya_tools.alembic_mtl import show_mtl_ui
    global _mtl_ui_window
    _mtl_ui_window = show_mtl_ui()
    return _mtl_ui_window


# 提供一个便捷方法来显示所有工具的菜单
def create_tools_menu():
    """在Maya中创建工具菜单"""
    import maya.cmds as mc
    import maya.mel as mel

    # 创建主菜单
    if mc.menu("mayaToolsMenu", exists=True):
        mc.deleteUI("mayaToolsMenu")

    gMainWindow = mel.eval('$temp = $gMainWindow')
    mc.menu("mayaToolsMenu", label="项目工具", parent=gMainWindow, tearOff=True)

    # 添加Alembic导出工具
    mc.menuItem(label="ABC导出工具", command="from maya_tools import show_alembic_exporter; show_alembic_exporter()")
    
    # 添加材质赋予工具（UI版本）
    mc.menuItem(label="ABC材质赋予工具(UI)", command="from maya_tools import show_mtl_ui; show_mtl_ui()")

    # 添加渲染设置工具
    mc.menuItem(label="ABC渲染组装工具", command="from maya_tools import show_render_setup; show_render_setup()")

    # 添加分割线
    mc.menuItem(divider=True)

    # 添加模型检查工具
    mc.menuItem(label="模型检查工具", command="from maya_tools import show_model_check; show_model_check()")

    # 添加场景清理工具
    mc.menuItem(label="场景清理工具", command="from maya_tools import show_scene_clean; show_scene_clean()")

    # 添加UV检查工具
    mc.menuItem(label="UV检查工具", command="from maya_tools import show_uv_check; show_uv_check()")

    print("项目工具菜单已创建")
