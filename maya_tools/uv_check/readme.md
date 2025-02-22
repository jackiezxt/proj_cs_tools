# UV检查工具
## 使用方法
```python
import sys
import importlib

# 添加工具路径
if r"d:\git\proj_cs_tools" not in sys.path:
    sys.path.append(r"d:\git\proj_cs_tools")
import maya_tools.uv_check.zxtUVsetModify
import importlib
importlib.reload(maya_tools.uv_check.zxtUVsetModify)

zxtUV = maya_tools.uv_check.zxtUVsetModify.zxtUVSetTool()
zxtUV.windows_zxtUVSetModify()
```
