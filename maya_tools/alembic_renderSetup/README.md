# Alembic RenderSetup 工具包

## 简介

Alembic RenderSetup 是一个 Maya 工具包，用于简化动画镜头的渲染设置和资产管理流程。该工具包可以帮助艺术家快速导入相机、设置渲染参数、管理角色和道具资产，以及更新 Alembic 缓存引用。

## 主要功能

- **镜头管理**：浏览和选择项目中的镜头
- **相机导入**：自动导入镜头相机并设置渲染参数
- **资产检查**：检查镜头所需的角色和道具资产状态
- **资产导入**：一键导入所需的角色和道具 LookDev 文件
- **Alembic 更新**：自动更新资产的 Alembic 缓存引用路径
- **渲染设置**：自动配置 Arnold 渲染器参数
- **场景保存**：按照项目规范保存场景文件

## 使用方法

### 启动工具

在 Maya 中执行以下 Python 代码启动工具：

```python
import sys

# 添加工具路径
if r"d:\git\proj_cs_tools" not in sys.path:
    sys.path.append(r"d:\git\proj_cs_tools")
# 加载工具   
import maya_tools.alembic_renderSetup.ui as ars
ars.show_shot_asset_manager()


```

### 基本工作流程
1. 选择项目、集数、场次和镜头
2. 导入相机（自动设置帧范围和渲染参数）
3. 检查资产状态（绿色表示资产存在，红色表示缺失）
4. 导入所需资产（可选择单个资产或全部导入）
5. 保存场景文件

## 注意事项
- 工具需要制片进行统计，将场号，镜头号，镜头中的角色和道具信息形成一个表格，工具会根据表格中的信息进行导入和检查
- 工具依赖 Maya 2020 或更高版本
- 需要 Arnold 渲染器插件支持
- 项目路径结构需要符合配置文件中定义的格式
- 相机文件命名应遵循 cam_[开始帧]_[结束帧].fbx 格式以便自动解析帧范围

## 开发者信息
如需修改或扩展功能，可使用重载模块功能进行开发：

```python
import maya_tools.alembic_renderSetup.ui.reload_module as rm
rm.reload_shot_asset_manager()
```