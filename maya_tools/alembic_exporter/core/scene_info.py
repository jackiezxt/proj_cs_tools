import maya.cmds as mc
import re

class SceneInfoManager:
    """场景信息管理器，用于获取场景中的资产ID和XGen Collection信息"""
    
    @staticmethod
    def get_asset_ids():
        """获取场景中的资产ID列表，从引用文件路径中提取
        
        Returns:
            list: 资产ID列表，如 ['c001', 'c002']
        """
        asset_ids = set()  # 使用集合去重
        
        # 获取所有有效的引用文件
        try:
            # 获取所有引用文件
            ref_nodes = mc.ls(type='reference') or []
            
            # 资产ID的正则表达式模式（不区分大小写）
            pattern = re.compile(r'[cC]\d{3}')
            
            for ref in ref_nodes:
                try:
                    # 跳过特殊的引用节点
                    if ref.endswith('sharedReferenceNode'):
                        continue
                        
                    # 检查引用节点是否有关联的文件
                    try:
                        if not mc.referenceQuery(ref, isLoaded=True):
                            continue
                    except Exception:
                        continue
                        
                    # 获取引用文件路径
                    try:
                        ref_path = mc.referenceQuery(ref, filename=True)
                    except Exception:
                        continue
                    
                    # 如果是abc文件则跳过
                    if ref_path.lower().endswith('.abc'):
                        continue
                        
                    # 从文件路径中提取资产ID
                    match = pattern.search(ref_path)
                    if match:
                        # 统一转换为小写格式
                        asset_id = match.group().lower()
                        asset_ids.add(asset_id)
                        
                except Exception as e:
                    if not str(e).startswith("Reference node") and not "is not associated with a reference file" in str(e):
                        print(f"处理引用节点 {ref} 时出错: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"获取引用列表时出错: {str(e)}")
        
        # 转换为列表并排序
        return sorted(list(asset_ids))
    
    @staticmethod
    def get_xgen_collections(asset_id=None):
        """获取场景中的XGen Collection列表
        
        Args:
            asset_id (str, optional): 资产ID，如'c001'。如果提供，只返回该资产相关的Collection
        
        Returns:
            list: XGen Collection名称列表，如 ['COL_Hair', 'COL_Beard']
        """
        collections = set()  # 使用集合去重
        
        # 获取场景中所有的transform节点
        all_transforms = mc.ls(type='transform') or []
        
        # Collection名称的正则表式模式（不区分大小写）
        pattern = re.compile(r'col_[a-zA-Z][a-zA-Z0-9_]*', re.IGNORECASE)
        
        # 如果指定了资产ID，构建资产的命名空间模式
        asset_pattern = None
        if asset_id:
            # 转换资产ID为大写格式（因为Maya中通常使用大写）
            asset_id = asset_id.upper()
            # 构建资产命名空间的正则表达式
            asset_pattern = re.compile(f"{asset_id}_[^:]+")
        
        for node in all_transforms:
            # 如果指定了资产ID，检查节点是否属于该资产
            if asset_pattern:
                # 获取节点的第一级命名空间
                namespace = node.split(':')[0] if ':' in node else ''
                if not asset_pattern.match(namespace):
                    continue
            
            # 检查节点名称中是否包含Collection名称
            match = pattern.search(node)
            if match:
                # 保持原始大小写
                collection_name = match.group()
                collections.add(collection_name)
        
        # 转换为列表并排序
        return sorted(list(collections))
    
    @classmethod
    def refresh_scene_info(cls):
        """刷新场景信息，获取最新的资产ID和Collection列表
        
        Returns:
            tuple: (asset_ids, collections) 包含资产ID列表和Collection列表的元组
        """
        asset_ids = cls.get_asset_ids()
        # 不传入asset_id参数，获取所有Collection
        collections = cls.get_xgen_collections()
        return asset_ids, collections 