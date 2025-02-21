# Alembic Exporter

Maya 角色模型 Alembic 缓存导出工具。

## 功能特点

- 自动识别场景中的角色模型（以 c001、c002 等命名）
- 按角色分类导出 Alembic 缓存
- 自动创建缓存目录结构
- 文件名包含剧集、场次、镜头信息
- 支持同一角色多个实例的导出
- 提供图形界面操作
- 支持独立运行和批处理模式

## 独立运行（不启动 Maya）

1. 使用 mayapy 运行（单个文件）：
```bash
mayapy -c "import maya.standalone; maya.standalone.initialize(); import maya.cmds as cmds; cmds.file(r'X:/projects/CSprojectFiles/Shot/Animation/PV/Sq04/Sc0120/work/scene.ma', open=True, force=True); import alembic_exporter; alembic_exporter.export_alembic()"
```
2. 批处理模式（多个文件）：
```bash
mayapy batch_export.py
```
## 在 Maya 中使用

1. 使用图形界面（推荐）：

```python
import sys
import importlib

# 添加工具路径
if r"d:\git\proj_cs_tools" not in sys.path:
   sys.path.append(r"d:\git\proj_cs_tools")

# 导入并重新加载模块
from maya_tools import alembic_exporter
from maya_tools.alembic_exporter.ui.gui import show_window

importlib.reload(alembic_exporter)

# 显示界面
window = show_window()
```

## 使用注意事项
1. 角色绑定文件中，不可含有任何重复命名的 mesh 模型，否则会报错
   
   - 例如：场景中有两个名为 "EyeBall_L_01_Geo" 的模型
2. Maya 文件必须已保存，且位于正确的项目路径结构中
   
   - 例如： X:/projects/CSprojectFiles/Shot/Animation/PV/Sq04/Sc0120/work/scene.ma
2. 角色模型要求：
   
   - 角色根节点命名必须符合规范（c001、c002 等）
   - Geometry 组必须位于角色层级下
3. 导出目录结构：
   
   ```plaintext
   work/
   └── abc_cache/
       ├── c001/
       │   └── PV_Sq04_Sc0120_c001_01.abc
       └── c002/
           └── PV_Sq04_Sc0120_c002_01.abc
    ```
4. 如果场景中存在多个相同角色：
   
   - 会自动添加编号后缀（_01、_02 等）
   - 存放在相同角色的文件夹中