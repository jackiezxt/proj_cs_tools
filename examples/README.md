# 配置系统指南

## 配置系统概述

我们的配置系统由多个配置文件组成，每个文件负责不同的配置方面：

1. **项目全局配置(project_config.json)**
   - 包含项目根路径、帧率、分辨率、色彩空间等全局设置

2. **资产配置(asset_config.json)**
   - 包含资产类型、资产步骤和资产路径模板

3. **镜头配置(shot_config.json)**
   - 包含镜头步骤和镜头路径模板

4. **渲染设置(render_settings.json)**
   - 包含渲染器设置、输出格式和其他渲染参数

## 配置文件位置

配置系统按以下顺序查找配置文件：

1. 通过函数参数提供的路径（如果有）
2. 环境变量指定的路径（例如 `CS_PROJECT_CONFIG_PATH`）
3. 当前Maya项目路径下的配置文件
4. 默认位置（`maya_tools/config/`目录）

## 配置示例

本目录包含以下示例配置文件：

- `project_a_config.json` - 项目A的全局设置
- `project_a_asset_config.json` - 项目A的资产配置
- `project_a_shot_config.json` - 项目A的镜头配置
- `project_b_config.json` - 项目B的全局设置
- `project_b_asset_config.json` - 项目B的资产配置
- `project_b_shot_config.json` - 项目B的镜头配置
- `render_settings.json` - 渲染设置示例
- `switch_project.py` - 项目切换脚本示例

## 使用方法

### 1. 创建项目配置文件

参考示例文件，为你的项目创建配置文件：

```json
{
  "project_name": "项目A",
  "project_root": "X:/projects/ProjectA",
  "frame_rate": 25,
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "color_space": "ACES - ACEScg"
}
```

### 2. 设置环境变量

使用环境变量指向您的配置文件：

```bash
# Windows
set CS_PROJECT_CONFIG_PATH=D:/configs/my_project_config.json
set CS_ASSET_CONFIG_PATH=D:/configs/my_asset_config.json
set CS_SHOT_CONFIG_PATH=D:/configs/my_shot_config.json
set CS_RENDER_SETTINGS_PATH=D:/configs/my_render_settings.json

# Linux/Mac
export CS_PROJECT_CONFIG_PATH=/path/to/my_project_config.json
export CS_ASSET_CONFIG_PATH=/path/to/my_asset_config.json
export CS_SHOT_CONFIG_PATH=/path/to/my_shot_config.json
export CS_RENDER_SETTINGS_PATH=/path/to/my_render_settings.json
```

### 3. 使用Python脚本切换项目

```python
import os
import json

def switch_to_project(project_name):
    """切换到指定项目的配置"""
    project_configs = {
        "ProjectA": {
            "project": "D:/configs/projectA/project_config.json",
            "asset": "D:/configs/projectA/asset_config.json",
            "shot": "D:/configs/projectA/shot_config.json",
            "render": "D:/configs/projectA/render_settings.json"
        },
        "ProjectB": {
            "project": "D:/configs/projectB/project_config.json",
            "asset": "D:/configs/projectB/asset_config.json",
            "shot": "D:/configs/projectB/shot_config.json", 
            "render": "D:/configs/projectB/render_settings.json"
        }
    }
    
    if project_name not in project_configs:
        print(f"未知项目: {project_name}")
        return False
    
    config = project_configs[project_name]
    os.environ["CS_PROJECT_CONFIG_PATH"] = config["project"]
    os.environ["CS_ASSET_CONFIG_PATH"] = config["asset"]
    os.environ["CS_SHOT_CONFIG_PATH"] = config["shot"]
    os.environ["CS_RENDER_SETTINGS_PATH"] = config["render"]
    
    print(f"已切换到项目: {project_name}")
    print(f"项目配置: {config['project']}")
    print(f"资产配置: {config['asset']}")
    print(f"镜头配置: {config['shot']}")
    print(f"渲染设置: {config['render']}")
    return True
```

## 路径模板变量

配置文件中的路径模板使用以下变量：

### 项目变量
- `{project_root}` - 项目根目录（来自project_config.json）

### 镜头变量
- `{episode}` - 集号
- `{sequence}` - 场次
- `{shot}` - 镜头号
- `{step}` - 制作步骤代码
- `{version}` - 版本号

### 资产变量
- `{asset_type}` - 资产类型（如char、prop、env）
- `{asset_id}` - 资产ID
- `{step}` - 制作步骤代码
- `{version}` - 版本号

## 资产类型配置

asset_config.json中定义了资产类型和制作步骤：

```json
{
  "types": {
    "char": "角色",
    "prop": "道具",
    "env": "场景",
    "veh": "载具"
  },
  "steps": {
    "mod": "模型",
    "rig": "绑定",
    "shd": "材质",
    "tex": "贴图"
  }
}
```

## 重新加载配置

修改配置文件后，可以使用以下方式重新加载配置：

### 1. 重启Maya
最简单可靠的方法

### 2. 使用reload_config()函数
```python
# 重新加载Alembic导出器配置
from maya_tools.alembic_exporter.core import config
config.reload_config()

# 重新加载渲染设置配置
from maya_tools.alembic_renderSetup.core import config
config.reload_config()
```

## 核心模块

配置系统由以下核心模块实现：

1. **ConfigManager**
   - 位于`maya_tools/common/config_manager.py`
   - 负责加载、合并和缓存配置文件

2. **alembic_exporter配置模块**
   - 位于`maya_tools/alembic_exporter/core/config.py`
   - 提供Alembic导出相关的配置访问接口

3. **alembic_renderSetup配置模块**
   - 位于`maya_tools/alembic_renderSetup/core/config.py`
   - 提供渲染设置相关的配置访问接口

## 最佳实践

1. **项目特定配置**: 为每个项目创建单独的配置文件集，以适应不同项目的需求
2. **环境变量配置**: 使用环境变量来切换项目配置，使工具适应不同项目
3. **脚本化配置切换**: 使用Python脚本自动设置环境变量，简化项目切换
4. **保持默认配置更新**: 确保默认配置文件包含所有必要的设置，作为备份 