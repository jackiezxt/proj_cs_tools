# coding: utf-8
"""
材质赋予工具的核心逻辑模块
"""
import maya.cmds as mc
from ..alembic_mtl import AssignShapeMtl, shapeData

class MaterialAssignLogic:
    """材质赋予工具的逻辑类"""
    
    def __init__(self):
        self.mtl_tool = AssignShapeMtl()
        self.shaded_meshes = []  # 有材质的模型
        self.default_meshes = []  # 无材质的模型
        
    def refresh_scene_data(self):
        """刷新场景数据，获取所有mesh及其材质状态"""
        # 重置数据
        self.mtl_tool = AssignShapeMtl()
        self.shaded_meshes = []
        self.default_meshes = []
        
        # 获取场景中所有mesh
        all_meshes = mc.ls(type='mesh', long=True)
        if not all_meshes:
            return
        
        # 获取mesh的transform节点
        transforms = []
        for mesh in all_meshes:
            parent = mc.listRelatives(mesh, parent=True, fullPath=True)
            if parent:
                transforms.append(parent[0])
        
        # 使用现有工具分析材质
        self.mtl_tool.selectShapes(transforms)
        
        # 获取有材质和无材质的模型列表
        self.shaded_meshes = self.mtl_tool.getShadedList()
        self.default_meshes = self.mtl_tool.getDefaultList()
        
        return {
            'shaded': self.shaded_meshes,
            'default': self.default_meshes
        }
    
    def get_mesh_names_without_namespace(self):
        """获取去除命名空间后的模型名称列表"""
        shaded_names = []
        for mesh in self.shaded_meshes:
            # 去除命名空间
            name = mesh.name.split(':')[-1]
            shaded_names.append({
                'display_name': name,
                'full_name': mesh.full_name,
                'data': mesh
            })
        
        default_names = []
        for mesh in self.default_meshes:
            # 去除命名空间
            name = mesh.name.split(':')[-1]
            default_names.append({
                'display_name': name,
                'full_name': mesh.full_name,
                'data': mesh
            })
        
        # 按字母排序
        shaded_names.sort(key=lambda x: x['display_name'].lower())
        default_names.sort(key=lambda x: x['display_name'].lower())
        
        return {
            'shaded': shaded_names,
            'default': default_names
        }
    
    def assign_one_to_one(self, shaded_mesh, default_mesh):
        """将一个有材质的模型的材质赋予给一个无材质的模型"""
        if not shaded_mesh or not default_mesh:
            mc.warning("请选择源模型和目标模型")
            return False
        
        try:
            # 检查面数是否相同
            if shaded_mesh.polyCount != default_mesh.polyCount:
                mc.warning(f"面数不匹配: {shaded_mesh.name}({shaded_mesh.polyCount}面) 和 {default_mesh.name}({default_mesh.polyCount}面)")
                return False
            
            # 执行材质赋予
            self.mtl_tool.assignShadeToDefault(shaded_mesh, default_mesh)
            return True
        except Exception as e:
            mc.warning(f"材质赋予失败: {str(e)}")
            return False
    
    def assign_all_matching(self):
        """为所有匹配的模型赋予材质"""
        try:
            # 创建一个新的 AssignMtlCtl 实例执行原有的自动匹配逻辑
            from ..alembic_mtl import AssignMtlCtl
            mtl_ctl = AssignMtlCtl()
            
            # 选择所有模型（有材质和无材质的）
            all_transforms = []
            for mesh in self.shaded_meshes + self.default_meshes:
                all_transforms.append(mesh.full_name)
            
            if not all_transforms:
                mc.warning("场景中没有检测到合适的模型")
                return False
            
            mc.select(all_transforms)
            mtl_ctl.selectAllCtl()
            return True
        except Exception as e:
            mc.warning(f"批量材质赋予失败: {str(e)}")
            return False 