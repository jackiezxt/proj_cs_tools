import os
import maya.cmds as mc
import maya.mel as mel
from maya import OpenMaya

def check_asset_imported(asset_id):
    """
    检查资产是否已导入Maya场景
    
    参数:
        asset_id (str): 资产ID
        
    返回:
        bool: 如果资产已导入返回True，否则返回False
    """
    # 检查命名空间，通常为asset_id_lookdev
    asset_namespace = f"{asset_id.lower()}_lookdev"
    namespaces = mc.namespaceInfo(listOnlyNamespaces=True)
    
    # 检查包含资产ID的节点
    asset_nodes = mc.ls(f"*{asset_id}*:*", long=True)
    
    if asset_namespace not in namespaces and not asset_nodes:
        mc.warning(f"资产 {asset_id} 未导入场景，请先导入资产")
        return False
    
    OpenMaya.MGlobal.displayInfo(f"资产 {asset_id} 已在场景中")
    return True

def reference_cloth_cache(asset_id, cache_path):
    """
    使用reference方式导入布料缓存
    
    参数:
        asset_id (str): 资产ID
        cache_path (str): 布料缓存文件路径
        
    返回:
        tuple: (命名空间, 引用的节点列表)
    """
    # 构建命名空间
    namespace = f"{asset_id.lower()}_cloth"
    
    # 如果命名空间已存在，添加唯一后缀
    if namespace in mc.namespaceInfo(listOnlyNamespaces=True):
        i = 1
        while f"{namespace}{i}" in mc.namespaceInfo(listOnlyNamespaces=True):
            i += 1
        namespace = f"{namespace}{i}"
    
    # 创建引用
    reference_node = mc.file(
        cache_path, 
        reference=True, 
        namespace=namespace,
        returnNewNodes=True
    )
    
    # 获取引用的所有节点
    referenced_nodes = mc.ls(f"{namespace}:*", long=True)
    
    OpenMaya.MGlobal.displayInfo(f"成功引用布料缓存: {namespace}")
    return namespace, referenced_nodes

def transfer_material(source_mesh, target_mesh):
    """
    将源几何体的材质应用到目标几何体
    
    参数:
        source_mesh (str): 源几何体节点名称
        target_mesh (str): 目标几何体节点名称
        
    返回:
        bool: 如果成功应用材质返回True，否则返回False
    """
    # 获取源几何体的着色引擎
    shading_engines = mc.listConnections(source_mesh, type="shadingEngine")
    
    if not shading_engines:
        return False
    
    # 使用第一个着色引擎（通常几何体上只有一个）
    shading_engine = shading_engines[0]
    
    # 将目标几何体添加到着色引擎集合中
    try:
        mc.sets(target_mesh, edit=True, forceElement=shading_engine)
        return True
    except Exception as e:
        mc.warning(f"材质应用失败: {str(e)}")
        return False

def match_and_assign_materials(asset_id, cloth_namespace, referenced_nodes):
    """
    匹配几何体并分配材质
    
    参数:
        asset_id (str): 资产ID
        cloth_namespace (str): 布料缓存的命名空间
        referenced_nodes (list): 引用的节点列表
        
    返回:
        tuple: (匹配的几何体列表, 未匹配的几何体列表)
    """
    # 获取缓存引用中的几何体
    cloth_meshes = []
    for node in referenced_nodes:
        if mc.nodeType(node) == "mesh" or (mc.objectType(node, isAType="transform") and 
                                         mc.listRelatives(node, shapes=True, type="mesh")):
            shape_nodes = mc.listRelatives(node, shapes=True, type="mesh", fullPath=True) if mc.objectType(node, isAType="transform") else [node]
            for shape in shape_nodes:
                if shape not in cloth_meshes:
                    cloth_meshes.append(shape)
    
    # 获取所有包含资产ID的命名空间
    potential_namespaces = []
    all_namespaces = mc.namespaceInfo(listOnlyNamespaces=True, recurse=True)
    asset_id_lower = asset_id.lower()
    lookdev_namespace = f"{asset_id_lower}_lookdev"
    
    # 首先尝试确切的lookdev命名空间，这是最理想的情况
    if lookdev_namespace in all_namespaces:
        potential_namespaces.append(lookdev_namespace)
    
    # 然后尝试其他包含资产ID的命名空间
    for namespace in all_namespaces:
        if asset_id_lower in namespace.lower() and namespace not in potential_namespaces:
            potential_namespaces.append(namespace)
    
    # 获取原始资产中的所有几何体
    original_meshes = []
    for namespace in potential_namespaces:
        # 首先尝试直接在命名空间下查找几何体
        transforms = mc.ls(f"{namespace}:*", type="transform", long=True)
        for transform in transforms:
            shapes = mc.listRelatives(transform, shapes=True, type="mesh", fullPath=True)
            if shapes:
                for shape in shapes:
                    if shape not in original_meshes:
                        original_meshes.append(shape)
        
        # 然后尝试在子命名空间中查找几何体（处理多级命名空间的情况）
        transforms = mc.ls(f"{namespace}:*:*", type="transform", long=True)
        for transform in transforms:
            shapes = mc.listRelatives(transform, shapes=True, type="mesh", fullPath=True)
            if shapes:
                for shape in shapes:
                    if shape not in original_meshes:
                        original_meshes.append(shape)
    
    # 记录匹配和未匹配的几何体
    matched_meshes = []
    unmatched_meshes = []
    
    # 打印进度信息
    total_meshes = len(cloth_meshes)
    mc.progressWindow(
        title="布料缓存导入", 
        progress=0, 
        status="开始匹配材质...", 
        isInterruptable=True, 
        maxValue=total_meshes
    )
    
    # 逐个处理布料缓存中的几何体
    for i, cloth_mesh in enumerate(cloth_meshes):
        # 更新进度
        if mc.progressWindow(query=True, isCancelled=True):
            break
        mc.progressWindow(edit=True, progress=i, status=f"处理 {i+1}/{total_meshes}: {os.path.basename(cloth_mesh)}")
        
        # 获取几何体名称（只获取冒号后的最后一段）
        cloth_base_name = cloth_mesh.split(":")[-1].split("|")[-1]
        if "Shape" in cloth_base_name:
            cloth_base_name = cloth_base_name.split("Shape")[0]
        
        # 查找匹配的原始几何体
        match_found = False
        for orig_mesh in original_meshes:
            # 获取所有命名空间部分
            orig_parts = orig_mesh.split(":")
            
            # 尝试多种匹配策略
            # 1. 检查最后一段（基本几何体名称）
            orig_base_name = orig_parts[-1].split("|")[-1]
            if "Shape" in orig_base_name:
                orig_base_name = orig_base_name.split("Shape")[0]
            
            # 2. 也检查倒数第二段（可能是模型组名称）
            orig_second_part = ""
            if len(orig_parts) > 2:
                orig_second_part = orig_parts[-2]
            
            # 匹配条件：
            # 1. 最后一段完全匹配
            # 2. 或者倒数第二段 + 最后一段的某个组合匹配
            if cloth_base_name == orig_base_name:
                # 转移材质
                if transfer_material(orig_mesh, cloth_mesh):
                    matched_meshes.append((cloth_mesh, orig_mesh))
                    match_found = True
                    break
            # 检查是否匹配模型组+几何体名称的组合
            elif orig_second_part and f"{orig_second_part}_{orig_base_name}" == cloth_base_name:
                if transfer_material(orig_mesh, cloth_mesh):
                    matched_meshes.append((cloth_mesh, orig_mesh))
                    match_found = True
                    break
            # 检查是否有部分匹配（一些模型可能命名不完全一致）
            elif cloth_base_name in orig_base_name or orig_base_name in cloth_base_name:
                if transfer_material(orig_mesh, cloth_mesh):
                    matched_meshes.append((cloth_mesh, orig_mesh))
                    match_found = True
                    break
        
        if not match_found:
            unmatched_meshes.append(cloth_mesh)
    
    mc.progressWindow(endProgress=1)
    
    # 打印最终结果
    print(f"布料缓存材质匹配结果: {len(matched_meshes)}/{total_meshes} 几何体已匹配材质")
    
    return matched_meshes, unmatched_meshes

def import_cloth_cache(asset_id, cache_path):
    """
    导入布料缓存并处理材质
    
    参数:
        asset_id (str): 资产ID
        cache_path (str): 布料缓存文件路径
        
    返回:
        tuple: (是否成功导入, 匹配的几何体列表, 未匹配的几何体列表)
    """
    # 确保文件存在
    if not os.path.exists(cache_path):
        mc.error(f"缓存文件不存在: {cache_path}")
        return False, [], []
    
    # 开始导入过程
    mc.inViewMessage(asst=True, msg=f"开始导入布料缓存: {os.path.basename(cache_path)}", pos='topCenter', fade=True)
    
    # 步骤1：检查资产是否已导入
    if not check_asset_imported(asset_id):
        return False, [], []
    
    # 步骤2：引用方式导入缓存
    try:
        namespace, referenced_nodes = reference_cloth_cache(asset_id, cache_path)
        mc.inViewMessage(asst=True, msg=f"缓存引用创建成功: {namespace}", pos='topCenter', fade=True)
    except Exception as e:
        mc.error(f"缓存引用创建失败: {str(e)}")
        return False, [], []
    
    # 步骤3：材质匹配与应用
    matched_meshes, unmatched_meshes = match_and_assign_materials(asset_id, namespace, referenced_nodes)
    
    # 步骤4：结果报告
    mc.inViewMessage(
        asst=True, 
        msg=f"布料缓存导入完成\n"
            f"成功匹配材质: {len(matched_meshes)}/{len(matched_meshes) + len(unmatched_meshes)} 个几何体", 
        pos='midCenter', 
        fade=True
    )
    
    if unmatched_meshes:
        mc.warning(f"有 {len(unmatched_meshes)} 个几何体未找到匹配材质:")
        for mesh in unmatched_meshes[:5]:  # 只显示前5个
            mesh_name = mesh.split(":")[-1].split("|")[-1]
            mc.warning(f"  - {mesh_name}")
        if len(unmatched_meshes) > 5:
            mc.warning(f"  ...等{len(unmatched_meshes)-5}个未显示")
    
    return True, matched_meshes, unmatched_meshes 