from .alembic_mtl import AssignMtlCtl

def assign_materials():
    """在 Maya 中执行材质赋予"""
    try:
        mtl_tool = AssignMtlCtl()
        mtl_tool.selectAllCtl()
    except Exception as e:
        print(f"材质赋予失败: {str(e)}")

def show_mtl_ui():
    """显示材质赋予工具UI"""
    from .ui.mtl_ui import show_window
    return show_window()