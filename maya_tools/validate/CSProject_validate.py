import maya.cmds as cmds


def validate_mesh_transform_nodes():
    mesh_transforms = cmds.ls(type='transform')

    for transform in mesh_transforms:
        shapes = cmds.listRelatives(transform, shapes=True, type='mesh')
        if shapes and 'polySurface' in transform:
            return ["模型名称含polySurface, 不允许通过提交"]

    return []


def validate_material_assignments():
    mesh_shapes = cmds.ls(type='mesh')
    invalid_materials = []
    non_compliant_types = ['lambert', 'standardSurface']

    for mesh in mesh_shapes:
        # Get the transform node
        transform = cmds.listRelatives(mesh, parent=True)[0]

        # Get assigned materials
        shading_groups = cmds.listConnections(mesh, type='shadingEngine')
        if not shading_groups:
            continue

        for sg in shading_groups:
            materials = cmds.listConnections(sg + '.surfaceShader')
            if not materials:
                continue

            material_type = cmds.nodeType(materials[0])
            material_name = materials[0]
            
            if material_type in non_compliant_types:
                if material_type == 'standardSurface' and 'aiStandardSurface' in material_type:
                    continue
                if material_name == 'lambert1':  # 只检查 lambert1
                    invalid_materials.append("材质中包含默认材质(lambert1)，不允许通过提交")
                    return invalid_materials

    return invalid_materials


def validate_duplicate_mesh_names():
    mesh_transforms = cmds.ls(type='transform')
    mesh_names = []

    for transform in mesh_transforms:
        shapes = cmds.listRelatives(transform, shapes=True, type='mesh')
        if shapes:
            mesh_names.append(transform)

    # Check for duplicates using set comparison
    if len(mesh_names) != len(set(mesh_names)):
        return ["模型中有重名，不允许通过提交"]

    return []


def validate_scene():
    invalid_mesh_nodes = validate_mesh_transform_nodes()
    invalid_materials = validate_material_assignments()
    duplicate_names = validate_duplicate_mesh_names()

    return invalid_mesh_nodes, invalid_materials, duplicate_names
