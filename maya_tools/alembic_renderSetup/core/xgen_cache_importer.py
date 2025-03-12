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
    # 大小写变体 - 检查多种可能的大小写形式
    asset_id_variants = [
        asset_id,  # 原始形式
        asset_id.lower(),  # 全小写
        asset_id.upper(),  # 全大写
        asset_id.capitalize()  # 首字母大写
    ]
    
    # 1. 检查命名空间
    namespaces = mc.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []
    
    # 检查多种可能的命名空间格式
    namespace_patterns = []
    for variant in asset_id_variants:
        namespace_patterns.extend([
            f"{variant}_lookdev",  # 标准格式
            f"{variant}",  # 仅ID
            f"{variant}_*"  # ID后跟其他标识
        ])
    
    for pattern in namespace_patterns:
        for ns in namespaces:
            if pattern.lower() in ns.lower() or ns.lower() in pattern.lower():
                OpenMaya.MGlobal.displayInfo(f"资产 {asset_id} 已在场景中(命名空间匹配)")
                return True
    
    # 2. 检查节点名称
    for variant in asset_id_variants:
        # 创建要搜索的模式
        search_patterns = [
            f"*{variant}*:*",  # 命名空间中包含ID
            f"*{variant}*",     # 名称中包含ID
            f"*{variant.replace('0', '')}*:*",  # 移除数字0后的ID (例如C001变为C1)
            f"*{variant.replace('0', '')}*"      # 移除数字0后的ID
        ]
        
        for pattern in search_patterns:
            asset_nodes = mc.ls(pattern, long=True) or []
            if asset_nodes:
                OpenMaya.MGlobal.displayInfo(f"资产 {asset_id} 已在场景中(节点名称匹配)")
                return True
    
    # 3. 尝试更宽松的搜索
    # 移除前缀字母，只保留数字部分 (例如C001变为001)
    numeric_part = ''.join(c for c in asset_id if c.isdigit())
    if numeric_part:
        search_patterns = [
            f"*{numeric_part}*:*",  # 命名空间中包含数字部分
            f"*{numeric_part}*"      # 名称中包含数字部分
        ]
        
        for pattern in search_patterns:
            asset_nodes = mc.ls(pattern, long=True) or []
            if asset_nodes:
                OpenMaya.MGlobal.displayInfo(f"资产 {asset_id} 已在场景中(数字部分匹配)")
                return True
    
    # 最后检查场景中的参考节点
    references = mc.ls(type="reference") or []
    for ref in references:
        try:
            ref_path = mc.referenceQuery(ref, filename=True) or ""
            if any(variant.lower() in ref_path.lower() for variant in asset_id_variants):
                OpenMaya.MGlobal.displayInfo(f"资产 {asset_id} 已在场景中(参考路径匹配)")
                return True
        except:
            # 参考可能已损坏
            pass
    
    # 未找到匹配
    mc.warning(f"资产 {asset_id} 未导入场景，请先导入资产")
    return False

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
    从缓存文件路径提取Collection和Description名称
    
    参数:
        cache_path (str): 缓存文件路径
        
    返回:
        tuple: (collection_name, description_name)
    """
    # 获取文件名（不包含扩展名）
    filename = os.path.basename(cache_path)
    base_name = os.path.splitext(filename)[0]
    
    # 初始化返回值
    collection_name = ""
    description_name = ""
    
    # 使用正则表达式匹配新格式，更可靠
    import re
    
    # 新格式: COL_Hair_DES_Bangs_c001_01
    # 其中COL_Hair是collection的全称，DES_Bangs是description的全称
    new_format = re.search(r'(COL_[^_]+)_(DES_[^_]+)_([^_]+)_(\d+)', base_name)
    if new_format:
        collection_name = new_format.group(1)  # COL_Hair
        description_name = new_format.group(2)  # DES_Bangs
        asset_id = new_format.group(3)  # c001
        version = new_format.group(4)  # 01
        return collection_name, description_name
        
    # 回退到使用split方法解析
    parts = base_name.split('_')
    
    # 新格式: COL_[CollectionName]_DES_[DescriptionName]_[AssetID]_[Version]
    # 例如: COL_Hair_DES_Bangs_c001_01
    if len(parts) >= 5 and parts[0] == 'COL' and 'DES' in parts:
        # 查找DES的位置
        des_index = parts.index('DES')
        
        # 提取Collection名称 (包含COL_前缀)
        collection_name = '_'.join(parts[0:des_index])
        if collection_name == 'COL':
            collection_name = 'COL_' + parts[1]
        
        # 提取Description名称 (包含DES_前缀和后面的名称部分)
        if des_index + 1 < len(parts):
            description_name = 'DES_' + parts[des_index + 1]
        
        return collection_name, description_name
    
    # 旧格式: DES_[DescriptionName]_[AssetID]_[Version]
    # 例如: DES_Bangs_c001_01
    elif len(parts) >= 3 and parts[0] == 'DES':
        # 完整的Description名称 (包含DES_前缀)
        description_name = parts[0] + '_' + parts[1]
        return collection_name, description_name
    
    # 使用备用正则表达式匹配
    # 尝试匹配部分格式
    partial_col = re.search(r'(COL_[^_]+)', base_name)
    if partial_col:
        collection_name = partial_col.group(1)
        
    partial_des = re.search(r'(DES_[^_]+)', base_name)
    if partial_des:
        description_name = partial_des.group(1)
    
    if collection_name or description_name:
        return collection_name, description_name
    
    # 如果无法解析，返回空值和文件名
    return "", base_name

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
        # 如果description_name为空，则无法匹配
        if not description_name:
            return ""
        
        # 准备用于比较的描述名称变体 - 多种形式用于匹配
        matching_variations = [description_name.lower()]  # 原始名称（小写）
        
        # 如果提供的描述包含DES_前缀，添加不带前缀的版本
        desc_no_prefix = description_name
        if description_name.startswith("DES_"):
            desc_no_prefix = description_name[4:]  # 移除"DES_"前缀
            matching_variations.append(desc_no_prefix.lower())
        # 反向情况：如果不包含DES_前缀，添加带前缀的版本
        else:
            with_prefix = f"DES_{description_name}"
            matching_variations.append(with_prefix.lower())
        
        # 尝试多种方法获取Descriptions
        # 方法1: 使用XGen API
        try:
            import xgenm
            descriptions = xgenm.descriptions(collection) or []
            if not descriptions:
                return ""
            
            # 首先尝试完全匹配（忽略大小写）
            for desc in descriptions:
                desc_lower = desc.lower()
                for variation in matching_variations:
                    if desc_lower == variation:
                        return desc
            
            # 然后尝试部分匹配（任一包含另一个）
            for desc in descriptions:
                desc_lower = desc.lower()
                for variation in matching_variations:
                    if variation in desc_lower or desc_lower in variation:
                        return desc
            
            # 如果Collection名称中包含可能的Description名称提示，也尝试匹配
            if collection.startswith("COL_"):
                collection_base = collection[4:].lower()  # 移除"COL_"前缀
                for desc in descriptions:
                    # 检查Description是否与Collection的基础部分相关
                    if collection_base in desc.lower() or desc.lower() in collection_base:
                        return desc
            
            # 最后的尝试：如果只有一个Description，考虑使用它
            if len(descriptions) == 1:
                only_desc = descriptions[0]
                return only_desc
                
            # 没有找到匹配
            return ""
            
        except Exception as e:
            mc.warning(f"使用XGen API获取Descriptions失败: {str(e)}")
        
        # 方法2: 使用Maya节点查询
        try:
            # 在Maya 2024中可能的节点类型
            xgen_desc_types = ["xgmDescription", "xgmSplineDescription"]
            
            for desc_type in xgen_desc_types:
                # 检查类型是否存在
                type_exists = False
                try:
                    if mc.objExists(desc_type) or len(mc.ls(type=desc_type)) > 0:
                        type_exists = True
                except:
                    pass
                
                if type_exists:
                    desc_nodes = mc.ls(type=desc_type) or []
                    
                    # 筛选与collection相关的描述
                    related_descs = []
                    for node in desc_nodes:
                        if collection.lower() in node.lower():
                            related_descs.append(node)
                    
                    # 在相关描述中查找匹配
                    for desc in related_descs:
                        desc_lower = desc.lower()
                        for variation in matching_variations:
                            if variation in desc_lower or desc_lower in variation:
                                short_name = desc.split(":")[-1] if ":" in desc else desc
                                return short_name
                                
            # 没有找到匹配
            return ""
            
        except Exception as e:
            mc.warning(f"使用Maya节点查询获取Descriptions失败: {str(e)}")
            
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
        # 确保必要的模块已导入
        import maya.cmds as mc  # 显式导入，防止UnboundLocalError
        import os
        
        # 格式化路径，确保使用"/"作为路径分隔符
        cache_path = cache_path.replace("\\", "/")
        
        # 处理路径中的重复分隔符
        if "//" in cache_path:
            cache_path = cache_path.replace("//", "/")
        
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
                OpenMaya.MGlobal.displayInfo(f"成功设置缓存: {collection} - {description}")
                return True
                
        except Exception as e:
            mc.warning(f"使用XGen API设置缓存失败: {str(e)}")
        
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
            OpenMaya.MGlobal.displayInfo(f"通过MEL命令设置缓存成功: {collection} - {description}")
            return True
            
        except Exception as e:
            mc.warning(f"使用MEL命令设置缓存失败: {str(e)}")
        
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
                    
                    if "use" in attr.lower() or "enable" in attr.lower():
                        mc.setAttr(f"{node}.{attr}", True)
            
            if xgen_nodes:
                OpenMaya.MGlobal.displayInfo(f"通过直接设置节点属性成功设置缓存: {collection} - {description}")
                return True
                
        except Exception as e:
            mc.warning(f"直接设置属性失败: {str(e)}")
        
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
    # 确保必要的模块已导入
    import maya.cmds as mc  # 显式导入，防止UnboundLocalError
    import os
    import traceback
    
    # 格式化路径，确保使用"/"作为路径分隔符
    cache_path = cache_path.replace("\\", "/")
    
    # 处理路径中的重复分隔符
    if "//" in cache_path:
        cache_path = cache_path.replace("//", "/")
    
    # 确保文件存在
    if not os.path.exists(cache_path):
        # 尝试解析环境变量
        if "$(DESG)" in cache_path:
            desg_var = mc.getenv("DESG")
            if desg_var:
                resolved_path = cache_path.replace("$(DESG)", desg_var)
                if os.path.exists(resolved_path):
                    cache_path = resolved_path
        
        # 如果仍然找不到文件
        if not os.path.exists(cache_path):
            mc.error(f"缓存文件不存在: {cache_path}")
            return False, "", ""
    
    # 开始导入过程
    try:
        mc.inViewMessage(asst=True, msg=f"开始导入XGen缓存: {os.path.basename(cache_path)}", pos='topCenter', fade=True)
    except Exception as e:
        # 在某些Maya版本中inViewMessage可能不可用，使用备用消息方式
        mc.warning(f"开始导入XGen缓存: {os.path.basename(cache_path)}")
    
    # 步骤1：检查资产是否已导入
    asset_imported = check_asset_imported(asset_id)
    
    if not asset_imported:
        return False, "", ""
    
    # 步骤2：强制初始化XGen环境
    xgen_env_ready = ensure_xgen_environment()
    
    # 步骤3：查找XGen Collections
    all_collections = find_xgen_collections(asset_id)
    
    if not all_collections:
        mc.warning(f"未找到与资产 {asset_id} 相关的XGen Collections")
        return False, "", ""
    
    # 步骤4：从缓存路径提取Collection和Description名称
    extracted_collection, extracted_description = extract_description_name_from_cache(cache_path)
    
    # 步骤5：尝试匹配Collection
    target_collections = []
    if extracted_collection:
        # 查找匹配的Collection
        for collection in all_collections:
            # 为了更灵活的匹配，创建不带前缀的版本
            extracted_col_no_prefix = extracted_collection
            if extracted_collection.startswith("COL_"):
                extracted_col_no_prefix = extracted_collection[4:]  # 移除"COL_"前缀
                
            collection_no_prefix = collection
            if collection.startswith("COL_"):
                collection_no_prefix = collection[4:]  # 移除"COL_"前缀
                
            # 多种匹配条件
            if (extracted_collection.lower() == collection.lower() or  # 完全匹配
                extracted_collection.lower() in collection.lower() or  # 部分匹配
                collection.lower() in extracted_collection.lower() or  # 反向部分匹配
                extracted_col_no_prefix.lower() in collection_no_prefix.lower() or  # 不带前缀部分匹配
                collection_no_prefix.lower() in extracted_col_no_prefix.lower()):  # 反向不带前缀部分匹配
                
                target_collections.append(collection)
        
        # 如果没有找到匹配的Collection，使用所有Collection
        if not target_collections:
            target_collections = all_collections
    else:
        # 如果没有提取出Collection名称，使用所有Collection
        target_collections = all_collections
    
    # 步骤6：尝试为目标Collections查找匹配的Description
    for collection in target_collections:
        # 查找匹配的Description - 使用增强匹配逻辑
        description = find_matching_description(collection, extracted_description)
        if description:
            # 步骤7：设置缓存
            try:
                success = setup_cache_for_description(collection, description, cache_path)
                if success:
                    success_msg = f"XGen缓存设置成功: {collection} - {description}"
                    
                    try:
                        mc.inViewMessage(
                            asst=True, 
                            msg=success_msg, 
                            pos='midCenter', 
                            fade=True
                        )
                    except Exception as e:
                        mc.warning(success_msg)
                    
                    return True, collection, description
            except Exception as e:
                mc.warning(f"设置缓存时出错: {str(e)}")
    
    # 尝试特殊匹配逻辑 - 基于Collection名称
    for collection in target_collections:
        # 获取不带前缀的Collection名称部分
        collection_name_part = collection
        if collection.startswith("COL_"):
            collection_name_part = collection[4:]  # 移除"COL_"前缀
            
        # 尝试在此Collection中查找所有Descriptions
        try:
            import xgenm
            descriptions = xgenm.descriptions(collection) or []
            
            # 如果只有一个Description，可以考虑直接使用它
            if len(descriptions) == 1:
                description = descriptions[0]
                
                # 设置缓存
                try:
                    success = setup_cache_for_description(collection, description, cache_path)
                    if success:
                        success_msg = f"XGen缓存设置成功(唯一描述): {collection} - {description}"
                        
                        try:
                            mc.inViewMessage(
                                asst=True, 
                                msg=success_msg, 
                                pos='midCenter', 
                                fade=True
                            )
                        except Exception as e:
                            mc.warning(success_msg)
                        
                        return True, collection, description
                except Exception:
                    pass
        except Exception:
            pass
    
    # 尝试创建新Description
    if target_collections:
        try:
            import xgenm
            # 创建新的Description
            collection = target_collections[0]
            
            # 确定要创建的Description名称
            new_desc_name = extracted_description
            if not new_desc_name:
                if extracted_collection:
                    # 使用Collection名称作为基础
                    col_base = extracted_collection
                    if col_base.startswith("COL_"):
                        col_base = col_base[4:]  # 移除"COL_"前缀
                    new_desc_name = f"DES_{col_base}"
                else:
                    # 使用默认名称
                    new_desc_name = f"Description_{asset_id}"
            
            # 确保新Description名称没有DES_前缀的重复
            if new_desc_name.startswith("DES_") and "_DES_" in new_desc_name:
                new_desc_name = new_desc_name.replace("_DES_", "_")
            
            # 创建新Description前，先检查是否已存在同名Description
            existing_descs = xgenm.descriptions(collection) or []
            
            if new_desc_name in existing_descs:
                # 直接使用已存在的Description
                try:
                    success = setup_cache_for_description(collection, new_desc_name, cache_path)
                    if success:
                        success_msg = f"使用已存在的Description设置缓存成功: {collection} - {new_desc_name}"
                        
                        try:
                            mc.inViewMessage(
                                asst=True, 
                                msg=success_msg, 
                                pos='midCenter', 
                                fade=True
                            )
                        except Exception as e:
                            mc.warning(success_msg)
                        
                        return True, collection, new_desc_name
                except Exception:
                    pass
            else:
                # 创建新Description
                try:
                    xgenm.createDescription(collection, new_desc_name)
                    
                    # 设置缓存
                    success = setup_cache_for_description(collection, new_desc_name, cache_path)
                    if success:
                        success_msg = f"创建新Description并设置缓存成功: {collection} - {new_desc_name}"
                        
                        try:
                            mc.inViewMessage(
                                asst=True, 
                                msg=success_msg, 
                                pos='midCenter', 
                                fade=True
                            )
                        except Exception as e:
                            mc.warning(success_msg)
                        
                        return True, collection, new_desc_name
                except Exception:
                    pass
        except Exception:
            pass
    
    # 最终失败消息
    error_msg = "无法为XGen缓存找到或创建匹配的Description，请尝试手动连接"
    mc.warning(error_msg)
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