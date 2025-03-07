# Maya 模型检查工具

这是一个用于检查和对比 Maya 模型结构的工具。主要用于比较不同版本模型文件之间的差异（如 rig 版本和 fur 版本）。

## 功能特点

- 检查 Geometry 组下所有模型的结构
- 统计每个模型的顶点数
- 保存检查结果到 JSON 文件
- 支持不同版本文件的模型对比
- 详细显示模型差异（新增、删除、顶点数变化）

## 使用方法

### 1. 启动工具
```python
import sys
import importlib

# 添加工具路径
if r"d:\git\proj_cs_tools" not in sys.path:
    sys.path.append(r"d:\git\proj_cs_tools")

from maya_tools.model_check import show_window
show_window()
```

### 2. 检查当前文件
1. 打开要检查的模型文件
2. 点击"检查当前文件"按钮
3. 工具会显示当前文件中所有模型的信息
4. 检查结果会自动保存到 `d:/temp/{文件名}.json`

### 3. 对比文件
1. 打开要对比的文件
2. 在输入框中输入之前检查过的文件名（不含扩展名）
   - 例如：要对比 `C013_rig.ma` 和 `C013_fur.ma`
   - 在 `C013_fur.ma` 中输入 `C013_rig`
3. 点击"与之前文件对比"按钮
4. 工具会显示两个文件之间的模型差异

## 检查内容

- Geometry 组的数量对比
- 模型层级结构对比
- 模型数量对比
- 每个模型的顶点数对比

## 注意事项

1. 使用前请确保文件已保存
2. 检查结果保存在 `d:/temp` 目录下
3. 对比时需要先检查第一个文件，再打开第二个文件进行对比
4. 文件名要求不含特殊字符
```