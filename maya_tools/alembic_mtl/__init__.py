from .alembic_mtl import AssignMtlCtl

def assign_materials():
    """在 Maya 中执行材质赋予"""
    try:
        mtl_tool = AssignMtlCtl()
        mtl_tool.selectAllCtl()
    except Exception as e:
        print(f"材质赋予失败: {str(e)}")