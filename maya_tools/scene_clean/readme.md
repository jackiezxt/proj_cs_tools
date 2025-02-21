# Maya 场景清理工具

这是一个用于清理和优化 Maya 场景的综合工具集。

## 功能特点

### 变换工具
- 复制/关联复制物体到指定位置
- 支持冻结变换的物体

### 材质管理
- 重命名所有 shader（支持 VRay 和 RedShift）
- 检查按面赋予的材质
- 自定义 shader 前缀

### 场景清理
- 清除未知插件信息
- 清除未知节点类型
- 检查和修复重复命名的物体
- 清除病毒节点（vaccine 等）
- 清除 CgAbError
- 清除 onModelChange3dc
- 清除 lockNode error
- 清除 pasted_ 节点名字
- 清除 Intermediate shape 节点
- 清除多余的 shape 节点
- 清除空组

### 渲染器管理

#### VRay 设置
- 初始化 VRay 渲染设置
- 添加 AOV
- 批量添加/控制细分设置

#### RedShift 设置
- 修改 AOV 路径前缀

#### 其他渲染器清理
- 清除海龟渲染器残留
- 清除 RenderMan 相关节点
- 清除 renderGlobal 中的 yeti 信息
- 修复渲染层切换 Bug

## 使用方法

1. 将脚本添加到 Maya 的 Python 路径中
2. 在 Maya 中运行以下代码：

```python
import maya.cmds as mc
import sys
import importlib

# 添加工具路径
if r"d:\git\proj_cs_tools" not in sys.path:
    sys.path.append(r"d:\git\proj_cs_tools")

# 导入并重新加载模块
from maya_tools.scene_clean import zxtSCNclearUp
importlib.reload(zxtSCNclearUp)

# 显示界面
zxtSCNclearUp.build_ui()
```
