import os
import maya.cmds as mc
from maya_tools.common.asset_manager import AssetManager as CommonAssetManager
from .path_checker import PathChecker
from maya_tools.alembic_renderSetup.core.config import PATH_TEMPLATES
import glob
import re


class AssetManager(CommonAssetManager):
    """资产管理器核心功能类，继承自common模块的AssetManager"""

    def __init__(self):
        # 先创建checker实例
        self.checker = PathChecker()
        self.asset_status = {}
        
        # 修改初始化方法，不再使用父类的__init__，而是直接设置必要的属性
        self.path_manager = self.checker.path_manager
        self.shot_data = self._load_shot_data()
        self.current_episode = None
        self.current_sequence = None
        self.current_shot = None

    def _load_shot_data(self, data_file=None):
        """加载镜头数据"""
        # 忽略data_file参数，使用path_checker中的shot_data
        return self.checker.shot_data.get("Episode", {})

    def get_episodes(self):
        """获取所有剧集"""
        return list(self.shot_data.keys())

    def get_sequences(self, episode):
        """获取指定剧集的所有场次"""
        self.current_episode = episode
        return list(self.shot_data.get(episode, {}).get("Sequences", {}).keys())

    def get_shots(self, episode, sequence):
        """获取指定场次的所有镜头"""
        self.current_episode = episode
        self.current_sequence = sequence
        return list(self.shot_data.get(episode, {}).get("Sequences", {}).get(sequence, {}).get("Shots", {}).keys())

    def get_shot_assets(self, episode, sequence, shot_id):
        """获取指定镜头的所有资产"""
        self.current_episode = episode
        self.current_sequence = sequence
        self.current_shot = shot_id

        shot_data = self.shot_data.get(episode, {}).get("Sequences", {}).get(sequence, {}).get("Shots", {}).get(shot_id,
                                                                                                                {})

        return {
            "Chars": shot_data.get("Chars", []),
            "Props": shot_data.get("Props", []),
            "Environment": shot_data.get("Environment", "")
        }

    def check_asset(self, asset_id, asset_type):
        """检查资产状态"""
        if not all([self.current_episode, self.current_sequence, self.current_shot]):
            raise ValueError("请先选择一个镜头")

        # 构建完整路径
        shot_path = os.path.join(self.checker.anm_path, self.current_episode, self.current_sequence, self.current_shot,
                                 "work")

        # 检查路径是否存在
        if not os.path.exists(shot_path):
            raise ValueError(f"路径不存在: {shot_path}")

        # 检查abc_cache文件夹
        abc_cache_path = os.path.join(shot_path, "abc_cache")
        if not os.path.exists(abc_cache_path) or not os.path.isdir(abc_cache_path):
            raise ValueError(f"未找到abc_cache文件夹: {abc_cache_path}")

        # 获取abc_cache中的所有文件夹
        cache_folders = [f.lower() for f in os.listdir(abc_cache_path)
                         if os.path.isdir(os.path.join(abc_cache_path, f))]

        # 检查缓存文件夹
        cache_exists = asset_id.lower() in cache_folders

        # 检查LookDev文件
        lookdev_exists = False
        lookdev_path = None
        try:
            lookdev_path = self.checker._check_lookdev_file(asset_id, asset_type, import_file=False)
            lookdev_exists = lookdev_path is not None
        except:
            lookdev_exists = False

        # 返回状态
        return {
            "cache_exists": cache_exists,
            "lookdev_exists": lookdev_exists,
            "lookdev_path": lookdev_path,
            "type": asset_type
        }

    def check_all_assets(self):
        """检查当前镜头的所有资产"""
        if not all([self.current_episode, self.current_sequence, self.current_shot]):
            raise ValueError("请先选择一个镜头")

        assets = self.get_shot_assets(self.current_episode, self.current_sequence, self.current_shot)

        self.asset_status = {}

        # 检查角色
        for char_id in assets["Chars"]:
            self.asset_status[char_id] = self.check_asset(char_id, "Chars")

        # 检查道具
        for prop_id in assets["Props"]:
            self.asset_status[prop_id] = self.check_asset(prop_id, "Props")

        return self.asset_status

    def import_asset(self, asset_id):
        """导入单个资产"""
        if not self.asset_status:
            self.check_all_assets()

        status = self.asset_status.get(asset_id, {})

        if not status.get("lookdev_exists"):
            raise ValueError(f"资产 {asset_id} 没有可用的LookDev文件")

        lookdev_path = status.get("lookdev_path")
        if not lookdev_path or not os.path.exists(lookdev_path):
            raise ValueError(f"找不到LookDev文件: {lookdev_path}")

        # 使用import方式导入文件，但保留文件中的引用关系
        namespace = f"{asset_id}_lookdev"
        mc.file(lookdev_path, i=True, namespace=namespace, preserveReferences=True)

        return True

    def update_abc_reference(self, asset_id):
        """更新资产的ABC引用路径
        
        将资产引用的ABC文件路径替换为当前镜头abc_cache中对应的文件
        
        Args:
            asset_id: 资产ID，如 "C001"
            
        Returns:
            bool: 是否成功更新
        """
        if not all([self.current_episode, self.current_sequence, self.current_shot]):
            raise ValueError("请先选择一个镜头")

        # 构建abc_cache路径
        shot_path = os.path.join(self.checker.anm_path, self.current_episode, self.current_sequence, self.current_shot,
                                 "work")
        abc_cache_path = os.path.join(shot_path, "abc_cache", asset_id.lower())
        
        # 检查路径是否存在
        if not os.path.exists(abc_cache_path):
            mc.warning(f"未找到资产 {asset_id} 的ABC缓存路径: {abc_cache_path}")
            return False
        
        # 获取该资产的所有ABC文件
        abc_files = [f for f in os.listdir(abc_cache_path) if f.endswith(".abc")]
        if not abc_files:
            mc.warning(f"未找到资产 {asset_id} 的ABC文件")
            return False
        
        # 构建完整文件路径
        abc_file_paths = [os.path.join(abc_cache_path, f).replace('\\', '/') for f in abc_files]
        
        # 获取资产命名空间
        namespace = f"{asset_id}_lookdev"
        
        # 查找引用节点
        all_references = mc.ls(type="reference") or []
        abc_references = []
        
        # 记录查找过程，帮助调试
        print(f"查找资产 {asset_id} 的引用:")
        print(f"命名空间: {namespace}")
        print(f"所有引用节点: {all_references}")
        
        # 直接使用字符串匹配查找所有相关引用节点
        for ref_node in all_references:
            # 跳过共享引用节点
            if "sharedReferenceNode" in ref_node:
                continue
                
            # 检查节点名称是否包含资产命名空间和geoRN
            if namespace in ref_node and "geoRN" in ref_node:
                # 获取当前引用路径进行检查
                try:
                    current_path = mc.referenceQuery(ref_node, filename=True)
                    print(f"找到匹配的引用节点: {ref_node}, 当前路径: {current_path}")
                    abc_references.append(ref_node)
                except Exception as e:
                    print(f"获取引用节点 {ref_node} 的路径时出错: {str(e)}")
        
        # 检查ABC文件数量和引用节点数量是否匹配
        if len(abc_files) != len(abc_references):
            mc.warning(f"ABC文件数量 ({len(abc_files)}) 与引用节点数量 ({len(abc_references)}) 不匹配")
            print(f"ABC文件: {abc_files}")
            print(f"引用节点: {abc_references}")
        
        # 更新引用
        updated_count = 0
        for i, ref_node in enumerate(abc_references):
            try:
                # 确保不超出文件列表范围
                if i < len(abc_file_paths):
                    # 替换为对应的ABC路径
                    mc.file(abc_file_paths[i], loadReference=ref_node)
                    print(f"已将 {ref_node} 的引用路径更新为: {abc_file_paths[i]}")
                    updated_count += 1
                else:
                    print(f"没有可用的ABC文件来更新引用 {ref_node}")
            except Exception as e:
                print(f"更新引用节点 {ref_node} 时出错: {str(e)}")
        
        return updated_count > 0

    def find_cloth_caches(self, episode, sequence, shot, asset_id):
        """
        查找指定资产的布料缓存文件
        
        Args:
            episode (str): 集号
            sequence (str): 场次
            shot (str): 镜头号
            asset_id (str): 资产ID，例如"c001"
            
        Returns:
            list: 布料缓存文件列表，每项包含文件名和路径信息
        """
        # 从配置获取布料缓存根路径
        cloth_path_template = PATH_TEMPLATES.get("cloth_sim_path", "")
        if not cloth_path_template:
            mc.warning("布料缓存路径模板未在配置中定义")
            return []
        
        # 处理场次命名格式 - 确保Sq03变为Sq03，sc0090变为Sc0090
        formatted_sequence = sequence
        formatted_shot = shot.capitalize() if shot.startswith("sc") or shot.startswith("Sc") else shot
        
        # 构建布料缓存发布目录
        publish_dir = os.path.join(
            cloth_path_template.format(
                episode=episode,
                sequence=formatted_sequence,
                shot=formatted_shot
            ),
            "publish"
        )
        
        if not os.path.exists(publish_dir):
            mc.warning(f"布料缓存目录不存在: {publish_dir}")
            return []
        
        # 查找匹配条件的布料缓存
        search_pattern = os.path.join(publish_dir, f"*cloth*{asset_id}*.abc")
        cache_files = glob.glob(search_pattern)
        
        # 提取文件信息
        result = []
        for file_path in cache_files:
            cache_info = self.get_cache_info(file_path)
            if cache_info:
                result.append(cache_info)
        
        return result

    def get_cache_info(self, file_path):
        filename = os.path.basename(file_path)
        
        # 尝试提取版本信息
        version_match = re.search(r'_(\d+)\.abc$', filename)
        version = int(version_match.group(1)) if version_match else 1
        
        # 确定缓存类型
        cache_type = "未知"
        if "cloth" in filename.lower():
            cache_type = "布料"
        elif "DES_" in filename:
            cache_type = "XGen"
        
        # 返回缓存信息
        return {
            "filename": filename,
            "path": file_path,
            "version": version,
            "type": cache_type,
            "size": os.path.getsize(file_path) / (1024 * 1024),  # 大小(MB)
            "date_modified": os.path.getmtime(file_path)  # 修改日期
        }

    def find_xgen_caches(self, episode, sequence, shot, asset_id):
        """
        查找指定资产的XGen缓存文件
        
        Args:
            episode (str): 集号
            sequence (str): 场次
            shot (str): 镜头号
            asset_id (str): 资产ID，例如"c001"
            
        Returns:
            list: XGen缓存文件列表，每项包含描述名称和路径信息
        """
        # 从配置获取XGen缓存根路径
        xgen_path_template = PATH_TEMPLATES.get("xgen_sim_path", "")
        if not xgen_path_template:
            mc.warning("XGen缓存路径模板未在配置中定义")
            return []
        
        # 处理场次命名格式 - 确保Sq03变为Sq03，sc0090变为Sc0090
        formatted_sequence = sequence
        formatted_shot = shot.capitalize() if shot.startswith("sc") or shot.startswith("Sc") else shot
        
        # 构建XGen缓存发布目录
        publish_dir = os.path.join(
            xgen_path_template.format(
                episode=episode,
                sequence=formatted_sequence,
                shot=formatted_shot
            ),
            "publish"
        )
        
        if not os.path.exists(publish_dir):
            mc.warning(f"XGen缓存目录不存在: {publish_dir}")
            return []
        
        # 查找匹配条件的XGen缓存
        search_pattern = os.path.join(publish_dir, f"*{asset_id}*.abc")
        cache_files = glob.glob(search_pattern)
        
        # 过滤并提取描述名称
        result = []
        desc_pattern = re.compile(r'(DES_[^_]+)_.*?')
        
        for file_path in cache_files:
            filename = os.path.basename(file_path)
            
            # 跳过布料缓存(含有cloth关键词)
            if "cloth" in filename.lower():
                continue
            
            # 提取描述名称
            match = desc_pattern.search(filename)
            if match:
                desc_name = match.group(1)
                cache_info = self.get_cache_info(file_path)
                if cache_info:
                    cache_info["description"] = desc_name
                    result.append(cache_info)
        
        return result
