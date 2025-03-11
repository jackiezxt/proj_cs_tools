# Alembic缓存导出工具

这个工具用于在Maya中导出角色、道具和毛发生长面的Alembic缓存文件。

## 功能特点

- 自动识别并导出场景中的角色几何体
- 自动识别并导出场景中的道具几何体
- 支持导出角色毛发生长面（Fur_Grp），用于XGen毛发模拟

## 使用方法

### 基本导出命令

在Maya脚本编辑器中运行以下命令打开导出工具界面：

```python
from maya_tools.alembic_exporter import show_window
show_window()
```

### 按类型导出

也可以直接调用特定类型的导出函数：

```python
# 导出角色
from maya_tools.alembic_exporter import export_char_alembic
export_char_alembic()

# 导出道具
from maya_tools.alembic_exporter import export_prop_alembic
export_prop_alembic()

# 导出毛发生长面
from maya_tools.alembic_exporter import export_fur_alembic
export_fur_alembic()
```

## 毛发生长面（Fur_Grp）导出说明

毛发生长面导出功能专为XGen毛发工作流程设计，它会：

1. 自动检测场景中所有名称包含"Fur_Grp"的组
2. 识别这些组所属的角色ID（例如从"c001_Fur_Grp"中识别出"c001"）
3. 为每个角色创建单独的Alembic缓存文件
4. 导出文件将保存在Maya文件所在目录的"abc_cache/[角色ID]"子目录中

## 开发者信息

### 添加新的资产类型

如果需要支持新的资产类型导出，请按照以下步骤操作：

1. 在`core/helpers.py`中添加查找新资产类型的函数
2. 在`export.py`中的`_find_asset_geometry`函数中添加对新资产类型的支持
3. 在`export.py`中添加导出新资产类型的函数
4. 在`__init__.py`中导出新函数
5. 在GUI中添加相应的按钮和处理逻辑

### 导出设置自定义

导出设置可在`core/settings.py`中的`AlembicExportSettings`类中修改。