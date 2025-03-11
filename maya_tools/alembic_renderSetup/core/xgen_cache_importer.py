#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XGen缓存导入模块

用于将Alembic缓存文件连接到Legacy XGen系统
"""

import os
import re
import maya.cmds as mc
import maya.mel as mel
from maya import OpenMaya

# 导入XGen模块，处理Legacy XGen
try:
    import xgenm as xg
    import xgenm.xgGlobal as xgg
except ImportError:
    OpenMaya.MGlobal.displayWarning("无法导入XGen Python模块，请确保XGen已加载")

def check_asset_imported(asset_id):
    """
    检查资产是否已导入Maya场景
    
    参数:
        asset_id (str): 资产ID
        
    返回:
        bool: 如果资产已导入返回True，否则返回False
    """
    # 检查命名空间，通常为asset_id_lookdev
    asset_namespace = f"{asset_id.lower()}_lookdev"
    namespaces = mc.namespaceInfo(listOnlyNamespaces=True, recurse=True)
    
    # 检查包含资产ID的节点
    asset_nodes = mc.ls(f"*{asset_id.lower()}*:*", long=True)
    
    if asset_namespace not in namespaces and not asset_nodes:
        mc.warning(f"资产 {asset_id} 未导入场景，请先导入资产")
        return False
    
    OpenMaya.MGlobal.displayInfo(f"资产 {asset_id} 已在场景中")
    return True

def ensure_xgen_environment():
    """
    确保XGen环境正确设置 - 专为Maya 2024优化
    
    返回:
        bool: XGen环境是否正确设置
    """
    # 步骤1：确保XGen插件已加载
    if not mc.pluginInfo("xgenToolkit", query=True, loaded=True):
        try:
            print("尝试加载XGen插件...")
            mc.loadPlugin("xgenToolkit")
            print("XGen插件加载成功")
        except Exception as e:
            mc.warning(f"加载XGen插件失败: {str(e)}")
            return False
    
    # 步骤2：确保XGen Python模块可用
    try:
        import xgenm
        print("XGen Python模块导入成功")
    except ImportError as e:
        mc.warning(f"无法导入XGen Python模块: {str(e)}")
        return False
    
    # 步骤3：对于Maya 2024，确保特定MEL命令可用
    try:
        # 检查关键MEL命令
        # 在Maya 2024中，一些命令可能已移至不同的位置，尝试多种检查方法
        
        # 方法1: 直接检查命令是否存在
        command_exists = mel.eval("exists(\"xgmPaletteUtilities\")")
        
        # 方法2: 从XGen Python API获取MEL命令
        if not command_exists:
            import xgenm
            # 尝试通过执行一个简单的XGen命令来初始化MEL环境
            try:
                # 尝试列出所有collections
                xgenm.palettes()
                command_exists = True
                print("通过XGen API初始化MEL命令成功")
            except Exception as e:
                print(f"尝试初始化XGen MEL环境时出错: {str(e)}")
                pass
        
        # 方法3: 对于Maya 2024，尝试使用替代命令
        if not command_exists:
            try:
                # 尝试其他可能的命令名称
                alternative_commands = ["xgmUtilUtilities", "xgmSplineUtilities", "xgmModifierUtilities"]
                for cmd in alternative_commands:
                    if mel.eval(f"exists(\"{cmd}\")"):
                        command_exists = True
                        print(f"找到替代XGen命令: {cmd}")
                        break
            except Exception:
                pass
        
        if not command_exists:
            # 尝试执行一个简单的MEL命令来初始化XGen环境
            try:
                mel.eval("source \"xgen.mel\";")
                mel.eval("xgmPaletteUtilities;")  # 尝试强制加载
                command_exists = mel.eval("exists(\"xgmPaletteUtilities\")")
                if command_exists:
                    print("通过source xgen.mel初始化成功")
            except Exception as e:
                print(f"尝试source xgen.mel时出错: {str(e)}")
                pass
        
        if not command_exists:
            mc.warning("XGen MEL命令不可用，可能影响XGen功能")
            return False
            
        print("XGen MEL命令检查成功")
        return True
    except Exception as e:
        mc.warning(f"检查XGen MEL命令时出错: {str(e)}")
        return False

def find_xgen_collections(asset_id):
    """
    查找与指定资产相关的XGen Collections
    
    参数:
        asset_id (str): 资产ID
        
    返回:
        list: 找到的Collections名称列表
    """
    # 确保XGen环境正确设置
    if not ensure_xgen_environment():
        mc.warning("XGen环境未正确设置，无法查找Collections")
        return []
    
    # 尝试多种方法获取Collections
    try:
        # 方法1: 使用标准XGen API
        try:
            import xgenm
            all_collections = xgenm.palettes()
            print(f"找到 {len(all_collections)} 个XGen Collections")
            
            # 筛选与asset_id相关的Collections
            related_collections = []
            asset_id_lower = asset_id.lower()
            for collection in all_collections:
                if asset_id_lower in collection.lower():
                    related_collections.append(collection)
                    
            print(f"与资产 {asset_id} 相关的Collections: {len(related_collections)}")
            return related_collections
        except Exception as e:
            print(f"使用XGen API获取Collections失败: {str(e)}")
            
        # 方法2: 使用Maya节点查询
        try:
            # 查找XGen描述节点
            xgen_nodes = mc.ls(type="xgmPalette") or []
            related_collections = []
            
            asset_id_lower = asset_id.lower()
            for node in xgen_nodes:
                if asset_id_lower in node.lower():
                    related_collections.append(node)
                    
            print(f"通过Maya节点查询找到与资产 {asset_id} 相关的Collections: {len(related_collections)}")
            return related_collections
        except Exception as e:
            print(f"使用Maya节点查询获取Collections失败: {str(e)}")
        
        # 最后返回空列表
        return []
    except Exception as e:
        mc.warning(f"查找XGen Collections时出错: {str(e)}")
        return []

def extract_description_name_from_cache(cache_path):
    """
    从缓存文件路径提取Description名称
    
    参数:
        cache_path (str): 缓存文件路径
        
    返回:
        str: Description名称
    """
    # 获取文件名（不包含扩展名）
    filename = os.path.basename(cache_path)
    base_name = os.path.splitext(filename)[0]
    
    # 按照命名规则解析: DES_[DescriptionName]_[AssetID]_[Version]
    # 例如: DES_Bangs_c001_01
    parts = base_name.split('_')
    
    if len(parts) >= 3 and parts[0] == 'DES':
        # 返回Description名称部分
        return parts[1]
    
    # 如果文件名不符合预期格式，尝试其他解析方法
    # 这里可以添加更复杂的正则表达式匹配
    
    # 如果无法解析，返回整个文件名作为参考
    return base_name

def find_matching_description(collection, description_name):
    """
    在指定Collection中查找匹配的Description - 针对Maya 2024优化
    
    参数:
        collection (str): Collection名称
        description_name (str): 要查找的Description名称或其一部分
        
    返回:
        str: 找到的Description名称，如果未找到则返回空字符串
    """
    try:
        # 尝试多种方法获取Descriptions
        
        # 方法1: 使用XGen API
        try:
            import xgenm
            descriptions = xgenm.descriptions(collection)
            print(f"Collection {collection} 中的Descriptions: {descriptions}")
            
            # 精确匹配优先
            for desc in descriptions:
                if desc.lower() == description_name.lower():
                    return desc
                    
            # 然后尝试部分匹配
            for desc in descriptions:
                if description_name.lower() in desc.lower() or desc.lower() in description_name.lower():
                    return desc
                    
            # 没有找到匹配
            return ""
            
        except Exception as e:
            print(f"使用XGen API获取Descriptions失败: {str(e)}")
        
        # 方法2: 使用Maya节点查询
        try:
            # 在Maya 2024中可能的节点类型
            xgen_desc_types = ["xgmDescription", "xgmSplineDescription"]
            
            for desc_type in xgen_desc_types:
                if mc.objExists(desc_type):
                    desc_nodes = mc.ls(type=desc_type) or []
                    
                    # 筛选与collection相关的描述
                    related_descs = []
                    for node in desc_nodes:
                        if collection.lower() in node.lower():
                            related_descs.append(node)
                    
                    # 精确匹配优先
                    for desc in related_descs:
                        if description_name.lower() in desc.lower():
                            short_name = desc.split(":")[-1] if ":" in desc else desc
                            return short_name
                            
            return ""
            
        except Exception as e:
            print(f"使用Maya节点查询获取Descriptions失败: {str(e)}")
            
        # 最后返回空字符串
        return ""
        
    except Exception as e:
        mc.warning(f"查找匹配Description时出错: {str(e)}")
        return ""

def setup_cache_for_description(collection, description, cache_path):
    """
    为指定的Description设置Alembic缓存 - 针对Maya 2024优化
    
    参数:
        collection (str): Collection名称
        description (str): Description名称
        cache_path (str): Alembic缓存文件路径
        
    返回:
        bool: 是否成功设置缓存
    """
    try:
        # 格式化路径，确保使用"/"作为路径分隔符
        cache_path = cache_path.replace("\\", "/")
        print(f"设置缓存 - 格式化后的路径: {cache_path}")
        
        # 处理路径中的重复分隔符
        if "//" in cache_path:
            cache_path = cache_path.replace("//", "/")
            print(f"设置缓存 - 修正重复分隔符后的路径: {cache_path}")
        
        # 尝试多种方法设置缓存
        
        # 方法1: 使用XGen API
        try:
            import xgenm
            # 注意：Maya 2024可能使用不同的API调用
            
            # 尝试设置缓存
            result = xgenm.setAttr("cacheFileName", cache_path, collection, description, 'SplinePrimitive')
            if result:
                # 启用缓存
                xgenm.setAttr("useCache", "true", collection, description, 'SplinePrimitive')
                print(f"成功设置缓存: {collection} - {description} -> {cache_path}")
                return True
                
        except Exception as e:
            print(f"使用XGen API设置缓存失败: {str(e)}")
        
        # 方法2: 使用MEL命令
        try:
            # 准备MEL命令
            mel_cmd = f"""
            if (catch(`xgmSelectPalette "{collection}"`)) {{
                error "无法选择Collection: {collection}";
            }}
            
            if (catch(`xgmSelectDescription "{description}"`)) {{
                error "无法选择Description: {description}";
            }}
            
            if (catch(`xgmSetArchiveAttribute "useCache" true`)) {{
                error "无法启用缓存";
            }}
            
            if (catch(`xgmSetArchiveAttribute "cacheFileName" "{cache_path}"`)) {{
                error "无法设置缓存文件路径";
            }}
            """
            
            # 执行MEL命令
            result = mel.eval(mel_cmd)
            print(f"通过MEL命令设置缓存结果: {result}")
            return True
            
        except Exception as e:
            print(f"使用MEL命令设置缓存失败: {str(e)}")
        
        # 方法3: 直接设置属性
        try:
            # 查找与Collection和Description相关的节点
            xgen_nodes = mc.ls(f"*{collection}*{description}*", long=True) or []
            
            for node in xgen_nodes:
                # 检查节点是否有相关属性
                attrs = mc.listAttr(node) or []
                cache_attrs = [attr for attr in attrs if "cache" in attr.lower()]
                
                for attr in cache_attrs:
                    if "filename" in attr.lower() or "file" in attr.lower():
                        mc.setAttr(f"{node}.{attr}", cache_path, type="string")
                        print(f"直接设置节点属性: {node}.{attr} = {cache_path}")
                    
                    if "use" in attr.lower() or "enable" in attr.lower():
                        mc.setAttr(f"{node}.{attr}", True)
                        print(f"启用缓存: {node}.{attr} = True")
            
            return True
                
        except Exception as e:
            print(f"直接设置属性失败: {str(e)}")
        
        # 返回失败
        return False
        
    except Exception as e:
        mc.warning(f"设置缓存时出错: {str(e)}")
        return False

def import_xgen_cache(asset_id, cache_path):
    """
    导入XGen缓存并连接到Legacy XGen系统 - 针对Maya 2024优化
    
    参数:
        asset_id (str): 资产ID
        cache_path (str): Alembic缓存文件路径
        
    返回:
        tuple: (是否成功导入, 连接的Collection, 连接的Description)
    """
    # 格式化路径，确保使用"/"作为路径分隔符
    cache_path = cache_path.replace("\\", "/")
    print(f"XGen缓存导入 - 格式化后的路径: {cache_path}")
    
    # 处理路径中的重复分隔符
    if "//" in cache_path:
        cache_path = cache_path.replace("//", "/")
        print(f"XGen缓存导入 - 修正重复分隔符后的路径: {cache_path}")
    
    # 确保文件存在
    if not os.path.exists(cache_path):
        # 尝试解析环境变量
        if "$(DESG)" in cache_path:
            desg_var = mc.getenv("DESG")
            if desg_var:
                resolved_path = cache_path.replace("$(DESG)", desg_var)
                print(f"XGen缓存导入 - 尝试解析环境变量后的路径: {resolved_path}")
                if os.path.exists(resolved_path):
                    cache_path = resolved_path
                    print(f"XGen缓存导入 - 已成功解析环境变量路径: {cache_path}")
        
        # 如果仍然找不到文件
        if not os.path.exists(cache_path):
            mc.error(f"缓存文件不存在: {cache_path}")
            return False, "", ""
    
    print(f"XGen缓存导入 - 最终使用的缓存路径: {cache_path}")
    
    # 开始导入过程
    mc.inViewMessage(asst=True, msg=f"开始导入XGen缓存: {os.path.basename(cache_path)}", pos='topCenter', fade=True)
    
    # 步骤1：检查资产是否已导入
    if not check_asset_imported(asset_id):
        return False, "", ""
    
    # 步骤2：强制初始化XGen环境
    if not ensure_xgen_environment():
        mc.warning("无法初始化XGen环境，缓存导入可能失败")
        # 继续尝试，因为用户指定需要Legacy XGen方法
    
    # 步骤3：查找XGen Collections
    collections = find_xgen_collections(asset_id)
    if not collections:
        mc.warning(f"未找到与资产 {asset_id} 相关的XGen Collections")
        return False, "", ""
    
    print(f"找到相关Collections: {collections}")
    
    # 步骤4：从缓存路径提取Description名称
    description_name = extract_description_name_from_cache(cache_path)
    if not description_name:
        mc.warning("无法从缓存路径提取Description名称")
        # 使用备用方法：从文件名提取
        base_name = os.path.basename(cache_path)
        description_name = os.path.splitext(base_name)[0]
        print(f"使用文件名作为Description名称: {description_name}")
    
    # 步骤5：尝试为每个Collection查找匹配的Description
    for collection in collections:
        # 查找匹配的Description
        description = find_matching_description(collection, description_name)
        if description:
            print(f"找到匹配的Description: {collection} - {description}")
            
            # 步骤6：设置缓存
            success = setup_cache_for_description(collection, description, cache_path)
            if success:
                mc.inViewMessage(
                    asst=True, 
                    msg=f"XGen缓存设置成功:\n{collection} - {description}", 
                    pos='midCenter', 
                    fade=True
                )
                return True, collection, description
    
    # 如果没有找到匹配的Description
    mc.warning(f"未找到匹配的Description，尝试在每个Collection中创建新的Description")
    
    # 尝试在第一个Collection中创建新的Description
    if collections:
        try:
            import xgenm
            # 创建新的Description
            collection = collections[0]
            xgenm.createDescription(collection, description_name)
            print(f"在Collection {collection}中创建了新的Description: {description_name}")
            
            # 设置缓存
            success = setup_cache_for_description(collection, description_name, cache_path)
            if success:
                mc.inViewMessage(
                    asst=True, 
                    msg=f"创建新Description并设置缓存成功:\n{collection} - {description_name}", 
                    pos='midCenter', 
                    fade=True
                )
                return True, collection, description_name
        except Exception as e:
            mc.warning(f"创建新Description时出错: {str(e)}")
    
    # 如果仍然失败
    mc.warning("无法为XGen缓存找到或创建匹配的Description")
    return False, "", ""

def list_available_descriptions(asset_id):
    """
    列出资产的所有可用XGen Descriptions
    
    参数:
        asset_id (str): 资产ID
        
    返回:
        dict: 以Collection为键，Description列表为值的字典
    """
    result = {}
    
    # 查找Collections
    collections = find_xgen_collections(asset_id)
    
    for collection in collections:
        descriptions = xg.descriptions(collection)
        if descriptions:
            result[collection] = descriptions
    
    return result 