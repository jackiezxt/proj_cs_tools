# CSProject_validate.py 使用说明

## 功能概述
这个Python脚本用于Maya场景的验证检查，主要针对模型和材质进行合规性验证。脚本包含三个主要的验证功能，用于确保场景符合提交标准。

## 主要功能

### 1. 模型命名验证 (validate_mesh_transform_nodes)
- 检查所有网格体的变换节点名称
- 验证是否包含'polySurface'关键词
- 如果发现包含该关键词的模型，将不允许通过提交

### 2. 材质分配验证 (validate_material_assignments)
- 检查网格体上的材质分配
- 验证以下不合规材质类型：
  - lambert材质
  - standardSurface材质（不包括aiStandardSurface）
- 如果发现使用了以上默认材质，将不允许通过提交

### 3. 重复命名验证 (validate_duplicate_mesh_names)
- 检查所有网格体的变换节点名称
- 验证是否存在重复的模型名称
- 如果发现重名模型，将不允许通过提交

## 使用方法

### 在Maya中使用
```python

import sys
import importlib

# 添加工具路径
if r"d:\git\proj_cs_tools" not in sys.path:
   sys.path.append(r"d:\git\proj_cs_tools")
   
from maya_tools.validate import CSProject_validate

# 执行完整的场景验证
result = CSProject_validate.validate_scene()

# 结果包含三个部分：
invalid_mesh_nodes, invalid_materials, duplicate_names = result

# 检查验证结果
if any([invalid_mesh_nodes, invalid_materials, duplicate_names]):
    print("场景验证失败，存在以下问题：")
    if invalid_mesh_nodes:
        print("- 模型命名问题：", invalid_mesh_nodes)
    if invalid_materials:
        print("- 材质问题：", invalid_materials)
    if duplicate_names:
        print("- 重复命名问题：", duplicate_names)
else:
    print("场景验证通过！")
```

### 单独使用各项验证功能
```python
# 仅验证模型命名
name_check = CSProject_validate.validate_mesh_transform_nodes()

# 仅验证材质
material_check = CSProject_validate.validate_material_assignments()

# 仅验证重复名称
duplicate_check = CSProject_validate.validate_duplicate_mesh_names()
```

## 错误信息说明

- 模型命名验证失败：`["模型名称含polySurface, 不允许通过提交"]`
- 材质验证失败：`["材质中包含默认材质，不允许通过提交"]`
- 重复命名验证失败：`["模型中有重名，不允许通过提交"]`

## 注意事项

1. 确保在执行验证前，场景中的所有模型都已经正确命名
2. 建议在提交场景前进行完整的验证检查
3. 如果验证失败，请根据返回的错误信息进行相应修正
4. 材质验证不会影响aiStandardSurface材质的使用