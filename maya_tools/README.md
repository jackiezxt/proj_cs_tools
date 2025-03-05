# Maya 工具集 (maya_tools)
## 简介
maya_tools 是一个专为 Maya 开发的工具集合，旨在简化和自动化动画制作流程中的常见任务。该工具集主要包含三个核心模块：Alembic导出器、材质赋予工具和渲染设置管理器，帮助艺术家提高工作效率并保持项目一致性。
## 核心模块
### 1. Alembic 导出器 (alembic_exporter)
自动识别场景中的角色和道具模型，按类型批量导出 Alembic 缓存文件。
主要特点：
自动识别场景中的角色模型（以 c001、c002 等命名）和道具模型
按资产分类导出 Alembic 缓存
自动创建缓存目录结构
文件名包含剧集、场次、镜头信息
支持同一角色多个实例的导出
提供图形界面操作
支持独立运行和批处理模式
### 2. Alembic 材质赋予工具 (alembic_mtl)
将有材质的模型材质快速赋予到其他相同拓扑的模型上，特别适用于 Alembic 缓存导入后的材质恢复。
主要特点：
自动识别有材质和无材质的模型
支持面级别和物体级别材质赋予
基于面数匹配相同拓扑模型
支持命名空间的模型处理
简洁直观的用户界面
支持批量赋予和单对单赋予
### 3. Alembic 渲染组装管理器 (alembic_renderSetup)
简化动画镜头的渲染设置和资产管理流程，便于快速搭建渲染场景。
主要特点：
镜头管理：浏览和选择项目中的镜头
相机导入：自动导入镜头相机并设置渲染参数
资产检查：检查镜头所需的角色和道具资产状态
资产导入：一键导入所需的角色和道具 LookDev 文件
Alembic 更新：自动更新资产的 Alembic 缓存引用路径
渲染设置：自动配置 Arnold 渲染器参数
场景保存：按照项目规范保存场景文件

## 安装说明
### 1. 将整个 maya_tools 文件夹复制到 Maya 的 Python 路径中，例如：
* Windows: `C:/Users/<用户名>/Documents/maya/scripts`
* Mac: `/Users/<用户名>/Library/Preferences/Autodesk/maya/scripts`
* Linux: `/home/<用户名>/maya/scripts`
* 或者在 maya 窗口运行
    ```python
    import sys
    if r"D:/GIT/proj_cs_tools" not in sys.path:
        sys.path.append(r"D:/GIT/proj_cs_tools")
    import maya_tools
    maya_tools.create_tools_menu()
    ```

## 系统要求
* Maya 2020 或更高版本
* Python 2.7 或 Python 3.7+（取决于 Maya 版本）
* 对于渲染设置管理器：需要 Arnold 渲染器插件

## 注意事项
1. 资产命名必须符合规范（角色以 c001、c002 等命名，道具以 p001、p002 等命名）
2. 项目路径结构需要符合配置文件中定义的格式
3. 材质赋予工具要求源模型和目标模型具有相同的面数
4. 渲染设置管理器需要制片提供的场号、镜头号、资产信息表格