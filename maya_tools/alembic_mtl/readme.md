# Maya 材质赋予工具

一个用于自动赋予材质的 Maya 工具，可以将一个模型的材质快速赋予到其他相同拓扑的模型上。

## 使用方法

1. 在 Maya 中运行以下代码：

```python
import sys
import importlib

# 添加工具路径
if r"d:\git\proj_cs_tools" not in sys.path:
    sys.path.append(r"d:\git\proj_cs_tools")

# 导入并重新加载模块
from maya_tools.alembic_mtl import assign_materials
importlib.reload(sys.modules["maya_tools.alembic_mtl.alembic_mtl"])

# 执行材质赋予
assign_materials()
```

2. 使用步骤
    - 先选择源模型（带有材质的模型）
    - 按住 Shift 选择目标模型（需要赋予材质的模型）
    - 执行上述代码
    - 工具会自动匹配相同面数的模型并赋予对应材质

## 注意事项

1. 源模型和目标模型必须具有相同的面数，否则无法赋予材质
2. 工具会自动识别以下情况的模型：
   - 使用默认材质(lambert1, standardSurface1)的模型
   - 带有自定义材质的模型
3. 支持以下材质赋予模式：
   - 面级别赋予(Face Mode)
   - 物体级别赋予(Group Mode)
4. 命名空间支持：
   - 工具可以处理带有命名空间的模型
   - 会自动匹配去除命名空间后相同名称的模型
5. 材质赋予后会自动选中处理过的模型，方便查看结果
6. 如果模型没有任何材质，会被视为使用默认材质