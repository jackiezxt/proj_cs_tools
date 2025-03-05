import os
import json
import maya.cmds as mc
from maya_tools.common.path_manager import PathManager


class PathChecker:
    """路径检查器，使用PathManager处理路径逻辑"""

    def __init__(self, data_file=None):
        """初始化路径检查器
        
        Args:
            data_file: 镜头数据JSON文件路径，如果为None则使用默认路径
        """
        self.path_manager = PathManager(project_config_path=None)
        
        # 如果未指定数据文件，使用默认路径
        if data_file is None:
            module_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_file = os.path.join(module_dir, "data", "shot_data.json")

        # 加载镜头数据
        self.shot_data = self._load_shot_data(data_file)
        self.anm_path = self.shot_data.get("anm_path", "")
        self.project_root = self.anm_path.split("Shot")[0] if "Shot" in self.anm_path else ""

    def _load_shot_data(self, data_file):
        """加载镜头数据
        
        Args:
            data_file: 数据文件路径
            
        Returns:
            加载的镜头数据字典
        """
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"找不到数据文件: {data_file}")

        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_shot_info(self, shot_id):
        """获取镜头信息
        
        Args:
            shot_id: 镜头ID，如 "sc0040"
            
        Returns:
            tuple: (episode, sequence, shot_data) 或 (None, None, None)
        """
        shot_id = shot_id.lower()
        for episode_name, episode_data in self.shot_data.get("Episode", {}).items():
            for seq_name, seq_data in episode_data.get("Sequences", {}).items():
                if shot_id in seq_data.get("Shots", {}):
                    return episode_name, seq_name, seq_data["Shots"][shot_id]
        return None, None, None

    def check_shot_path(self, episode, sequence, shot, import_lookdev=False):
        """检查指定镜头的工作目录是否存在
        
        Args:
            episode: 剧集名称，如 "PV"
            sequence: 场次名称，如 "Sq01"
            shot: 镜头名称，如 "Sc0040"
            import_lookdev: 是否导入找到的LookDev文件
            
        Returns:
            如果目录存在且包含文件，返回True；否则返回False
        """
        # 构建完整路径
        shot_path = os.path.join(self.anm_path, episode, sequence, shot, "work")

        # 检查路径是否存在
        if not os.path.exists(shot_path):
            print(f"路径不存在: {shot_path}")
            return False

        # 检查目录中是否有文件
        files = os.listdir(shot_path)
        if files:
            print(f"在路径 {shot_path} 中找到 {len(files)} 个文件")

            # 检查abc_cache文件夹
            abc_cache_path = os.path.join(shot_path, "abc_cache")
            if os.path.exists(abc_cache_path) and os.path.isdir(abc_cache_path):
                print(f"找到abc_cache文件夹: {abc_cache_path}")

                # 获取镜头数据
                shot_id = shot.lower()
                _, _, shot_data = self._get_shot_info(shot_id)

                if shot_data:
                    chars = shot_data.get("Chars", [])
                    props = shot_data.get("Props", [])

                    # 检查角色文件夹
                    missing_chars = self._check_asset_folders(abc_cache_path, chars, "角色")

                    # 检查道具文件夹
                    missing_props = self._check_asset_folders(abc_cache_path, props, "道具")

                    # 检查LookDev文件
                    if self.project_root:
                        # 检查角色LookDev文件
                        for char in chars:
                            self._check_lookdev_file(char, "Chars", import_lookdev)

                        # 检查道具LookDev文件
                        for prop in props:
                            self._check_lookdev_file(prop, "Props", import_lookdev)
                    else:
                        print("无法确定项目根目录，跳过LookDev文件检查")

                else:
                    print(f"在shot_data.json中找不到镜头 {shot_id} 的数据")
            else:
                print(f"未找到abc_cache文件夹: {abc_cache_path}")

            return True
        else:
            print(f"路径 {shot_path} 存在但没有文件")
            return False

    def _check_lookdev_file(self, asset_id, asset_type, import_file=False):
        """检查资产的LookDev文件是否存在
        
        Args:
            asset_id: 资产ID，如 "C001"
            asset_type: 资产类型，如 "Chars" 或 "Props"
            import_file: 是否导入找到的文件
            
        Returns:
            找到的LookDev文件路径，如果未找到则返回None
        """
        # 构建资产名称（假设格式为C001_Name）
        asset_name = None

        # 查找资产目录
        asset_base_path = os.path.join(self.project_root, "Asset", asset_type)
        if os.path.exists(asset_base_path):
            # 查找匹配的资产文件夹
            for folder in os.listdir(asset_base_path):
                if folder.lower().startswith(asset_id.lower() + "_"):
                    asset_name = folder
                    break

        if not asset_name:
            print(f"未找到{asset_type}资产: {asset_id}")
            return None

        # 构建LookDev路径
        lookdev_path = os.path.join(asset_base_path, asset_name, "LookDev", "work")
        if not os.path.exists(lookdev_path):
            print(f"未找到{asset_id}的LookDev路径: {lookdev_path}")
            return None

        # 查找_lookdev.ma文件
        lookdev_files = []
        for file in os.listdir(lookdev_path):
            if file.endswith("_lookdev.ma") and file.startswith(asset_name):
                lookdev_files.append(file)

        if not lookdev_files:
            print(f"未找到{asset_id}的LookDev文件")
            return None

        # 使用最新的文件
        lookdev_file = lookdev_files[0]  # 默认使用第一个
        if len(lookdev_files) > 1:
            # 如果有多个文件，可以根据修改时间选择最新的
            lookdev_files.sort(key=lambda x: os.path.getmtime(os.path.join(lookdev_path, x)), reverse=True)
            lookdev_file = lookdev_files[0]

        lookdev_file_path = os.path.join(lookdev_path, lookdev_file)
        print(f"找到{asset_id}的LookDev文件: {lookdev_file_path}")

        # 如果需要导入文件
        if import_file:
            try:
                # 检查文件是否已经导入
                ref_nodes = mc.ls(type='reference') or []
                for ref in ref_nodes:
                    if mc.referenceQuery(ref, filename=True).replace('\\', '/') == lookdev_file_path.replace('\\', '/'):
                        print(f"{asset_id}的LookDev文件已经导入")
                        return lookdev_file_path
                # 导入文件
                namespace = f"{asset_id}_lookdev"
                mc.file(lookdev_file_path, i=True, namespace=namespace, preserveReferences=True)
                print(f"已导入{asset_id}的LookDev文件")
            except Exception as e:
                print(f"导入{asset_id}的LookDev文件时出错: {str(e)}")

        return lookdev_file_path

    def check_shot_by_id(self, shot_id, import_lookdev=False):
        """根据镜头ID检查工作目录是否存在
        
        Args:
            shot_id: 镜头ID，如 "sc0040"
            import_lookdev: 是否导入找到的LookDev文件
            
        Returns:
            如果目录存在且包含文件，返回True；否则返回False
        """
        # 确保shot_id格式正确
        if not shot_id.lower().startswith("sc"):
            shot_id = f"Sc{shot_id}"
        else:
            # 转换为首字母大写格式
            shot_id = "Sc" + shot_id[2:]

        # 确保shot_id长度为6
        if len(shot_id) < 6:
            shot_id = shot_id[:2] + shot_id[2:].zfill(4)

        # 获取镜头信息
        episode, sequence, shot_data = self._get_shot_info(shot_id)
        if not all([episode, sequence, shot_data]):
            print(f"找不到镜头 {shot_id} 的信息")
            return False

        return self.check_shot_path(episode, sequence, shot_id, import_lookdev)

    def _check_asset_folders(self, abc_cache_path, asset_list, asset_type):
        """检查资产文件夹是否存在
        
        Args:
            abc_cache_path: abc_cache文件夹路径
            asset_list: 资产列表
            asset_type: 资产类型（角色或道具）
            
        Returns:
            缺失的资产列表
        """
        if not asset_list:
            print(f"没有需要检查的{asset_type}")
            return []

        # 获取abc_cache中的所有文件夹
        try:
            cache_folders = [f.lower() for f in os.listdir(abc_cache_path)
                             if os.path.isdir(os.path.join(abc_cache_path, f))]
        except Exception as e:
            print(f"读取abc_cache文件夹时出错: {str(e)}")
            return asset_list

        # 检查每个资产是否有对应的文件夹（忽略大小写）
        missing_assets = []
        for asset in asset_list:
            asset_lower = asset.lower()
            if asset_lower not in cache_folders:
                missing_assets.append(asset)

        if missing_assets:
            print(f"缺少以下{asset_type}的缓存文件夹: {', '.join(missing_assets)}")
        else:
            print(f"所有{asset_type}的缓存文件夹都存在")

        return missing_assets
