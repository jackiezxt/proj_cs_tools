import os
import maya.cmds as mc
from .path_checker import PathChecker


class AssetManager:
    """资产管理器核心功能类"""

    def __init__(self):
        self.checker = PathChecker()
        self.shot_data = {}
        self.current_episode = None
        self.current_sequence = None
        self.current_shot = None
        self.asset_status = {}

        self._load_shot_data()

    def _load_shot_data(self):
        """加载镜头数据"""
        self.shot_data = self.checker.shot_data.get("Episode", {})

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
        abc_cache_path = os.path.join(shot_path, "abc_cache")

        if not os.path.exists(abc_cache_path):
            raise ValueError(f"abc_cache路径不存在: {abc_cache_path}")

        # 查找资产对应的abc_cache文件夹
        asset_cache_dir = None
        for folder in os.listdir(abc_cache_path):
            if folder.lower() == asset_id.lower():
                asset_cache_dir = folder
                break

        if not asset_cache_dir:
            raise ValueError(f"在abc_cache中未找到资产 {asset_id} 的文件夹")

        # 查找资产文件夹中的ABC文件
        asset_cache_path = os.path.join(abc_cache_path, asset_cache_dir)
        abc_files = []
        for file in os.listdir(asset_cache_path):
            if file.lower().endswith(".abc"):
                abc_files.append(file)

        if not abc_files:
            raise ValueError(f"在 {asset_cache_path} 中未找到ABC文件")

        # 使用最新的ABC文件
        abc_files.sort(key=lambda x: os.path.getmtime(os.path.join(asset_cache_path, x)), reverse=True)
        latest_abc = os.path.join(asset_cache_path, abc_files[0])

        # 查找资产的引用节点
        namespace = f"{asset_id}_lookdev"

        # 获取所有引用节点
        all_references = mc.ls(type="reference") or []
        updated = False

        # 遍历所有引用节点，查找包含ABC文件的引用
        for ref_node in all_references:
            try:
                # 获取引用文件路径
                ref_path = mc.referenceQuery(ref_node, filename=True)

                # 检查是否为ABC文件
                if ref_path.lower().endswith(".abc"):
                    # 检查引用节点是否属于当前资产的命名空间
                    ref_namespace = mc.referenceQuery(ref_node, namespace=True)
                    if ref_namespace and ref_namespace.strip(':') == namespace:
                        # 替换为新的ABC路径
                        mc.file(latest_abc, loadReference=ref_node)
                        print(f"已将 {ref_node} 的引用路径更新为: {latest_abc}")
                        updated = True
            except Exception as e:
                print(f"处理引用节点 {ref_node} 时出错: {str(e)}")

        # 如果没有找到引用节点，尝试查找所有带命名空间的节点
        if not updated:
            # 获取所有带命名空间的节点
            namespace_nodes = mc.ls(f"{namespace}:*") or []

            # 遍历这些节点，查找可能的引用
            for node in namespace_nodes:
                try:
                    # 检查节点是否有引用属性
                    if mc.objectType(node) == "reference" or "reference" in mc.nodeType(node, inherited=True):
                        # 获取引用文件路径
                        ref_path = mc.referenceQuery(node, filename=True)

                        # 检查是否为ABC文件
                        if ref_path.lower().endswith(".abc"):
                            # 替换为新的ABC路径
                            mc.file(latest_abc, loadReference=node)
                            print(f"已将 {node} 的引用路径更新为: {latest_abc}")
                            updated = True
                except Exception as e:
                    # 忽略错误，继续检查下一个节点
                    pass

        return updated
