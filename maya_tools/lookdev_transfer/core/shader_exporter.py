import maya.cmds as mc
import json
import os
from .path_parser import AssetPathParser

class ShaderExporter:
    def __init__(self):
        self.current_file = mc.file(q=True, sn=True)
        if not self.current_file:
            raise RuntimeError("请先保存场景文件")
            
        self.path_parser = AssetPathParser(self.current_file)
        self.export_path = self.path_parser.get_lookdev_path()
        
    def set_export_path(self, path):
        """设置自定义导出路径"""
        self.export_path = path
        
    def collect_shader_info(self):
        """收集模型和材质的对应关系"""
        shader_info = {}
        
        # 查找场景中的 Geometry 组
        geometry_groups = mc.ls("*:Geometry", "*|Geometry", long=True) or []
        if not geometry_groups:
            raise RuntimeError("场景中未找到 Geometry 组")
            
        # 获取 Geometry 组下的所有 mesh
        all_meshes = []
        for geo_group in geometry_groups:
            meshes = mc.listRelatives(geo_group, allDescendents=True, type='mesh', fullPath=True) or []
            all_meshes.extend(meshes)
            
        # 确保找到了模型
        if not all_meshes:
            raise RuntimeError("Geometry 组中未找到任何模型")
            
        for mesh in all_meshes:
            # 跳过中间物体
            if mc.getAttr(f"{mesh}.intermediateObject"):
                continue
                
            transform = mc.listRelatives(mesh, parent=True, fullPath=True)[0]
            mesh_data = {
                "full_name": transform,
                "name": transform.split('|')[-1],
                "shape": {
                    "full_name": mesh,
                    "name": mesh.split('|')[-1]
                },
                "poly_count": mc.polyEvaluate(mesh, f=True),
                "materials": []
            }
            
            # 获取材质信息
            shading_engines = mc.listConnections(mesh, type='shadingEngine') or []
            
            for se in shading_engines:
                # 获取所有可能的材质连接
                material_attrs = [
                    'surfaceShader',
                    'volumeShader',
                    'displacementShader',
                    'aiSurfaceShader',
                    'aiVolumeShader'
                ]
                
                for attr in material_attrs:
                    if mc.attributeQuery(attr, node=se, exists=True):
                        shaders = mc.listConnections(f"{se}.{attr}") or []
                        for shader in shaders:
                            if shader not in ['lambert1', 'standardSurface1']:
                                # 获取材质的所有属性
                                shader_attrs = mc.listAttr(shader, k=True, s=True) or []
                                attr_values = {}
                                for shader_attr in shader_attrs:
                                    try:
                                        value = mc.getAttr(f"{shader}.{shader_attr}")
                                        if isinstance(value, list):
                                            value = value[0]
                                        attr_values[shader_attr] = value
                                    except:
                                        continue
                                
                                # 获取材质的连接信息
                                connections = {}
                                for conn in (mc.listConnections(shader, connections=True, plugs=True) or []):
                                    if isinstance(conn, tuple):
                                        src, dst = conn
                                        connections[src.split('.')[-1]] = {
                                            'node': dst.split('.')[0],
                                            'attr': dst.split('.')[-1]
                                        }
                                
                                material_info = {
                                    'name': shader,
                                    'type': mc.nodeType(shader),
                                    'connection_type': attr,
                                    'shading_engine': se,
                                    'attributes': attr_values,
                                    'connections': connections
                                }
                                
                                # 检查是否已经添加过这个材质
                                if not any(m['name'] == shader for m in mesh_data['materials']):
                                    mesh_data['materials'].append(material_info)
            
            if mesh_data['materials']:
                shader_info[mesh_data['name']] = mesh_data
                
        return shader_info
        
    def export_shaders(self):
        """导出材质和信息文件"""
        # 确保导出目录存在
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)
            
        # 收集材质信息
        shader_info = self.collect_shader_info()
        
        # 导出 JSON 文件
        json_path = os.path.join(self.export_path, f"{self.path_parser.asset_name}_lookdev_info.json")  # 修改文件名
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(shader_info, f, indent=4, ensure_ascii=False)
            
        # 导出材质文件
        # 获取所有非默认材质
        all_materials = []
        for mesh_data in shader_info.values():
            for mat in mesh_data['materials']:
                if mat['name'] not in all_materials:
                    all_materials.append(mat['name'])
                
        if all_materials:
            # 清除当前选择
            mc.select(clear=True)
            
            # 收集所有需要导出的节点
            export_nodes = set()
            
            for shader in all_materials:
                # 获取材质相关的所有节点
                mc.select(shader)
                mc.hyperShade(shaderNetworksSelectMaterialNodes=True)
                nodes = mc.ls(sl=True) or []
                export_nodes.update(nodes)
                
                # 获取 shading engine
                se_nodes = mc.listConnections(shader, type='shadingEngine') or []
                export_nodes.update(se_nodes)
            
            # 过滤掉所有的 mesh 和 transform 节点
            filtered_nodes = []
            for node in export_nodes:
                node_type = mc.nodeType(node)
                if node_type not in ['mesh', 'transform', 'shadingEngine']:
                    filtered_nodes.append(node)
                elif node_type == 'shadingEngine':
                    # 只保留包含我们材质的 shadingEngine
                    connections = mc.listConnections(f"{node}.surfaceShader") or []
                    if any(mat in connections for mat in all_materials):
                        filtered_nodes.append(node)
            
            if not filtered_nodes:
                raise RuntimeError("未能找到任何材质节点")
                
            # 选择过滤后的节点进行导出
            mc.select(filtered_nodes, r=True, ne=True)
            
            # 导出选中的节点
            ma_path = os.path.join(self.export_path, f"{self.path_parser.asset_name}_lookdev_shader.ma")
            mc.file(ma_path, 
                   force=True,
                   options="v=0;",
                   type="mayaAscii",
                   preserveReferences=True,
                   exportSelected=True)
            
        return json_path, ma_path if all_materials else None