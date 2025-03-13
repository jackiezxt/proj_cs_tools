import maya.cmds as mc
from maya_tools.common.config_manager import ConfigManager
from maya_tools.alembic_exporter.export import export_xgen_guides

class XGenGuidesManager:
    def __init__(self):
        """初始化XGen Guides管理器"""
        # 创建配置管理器实例
        self.config_manager = ConfigManager()
        
    @staticmethod
    def get_selected_guides():
        """获取选中的guides物体"""
        selected = mc.ls(selection=True)
        if not selected:
            return []
        return selected
        
    @staticmethod
    def _remove_namespace(node_name):
        """移除节点名称中的namespace
        
        Args:
            node_name (str): 带namespace的节点名称
            
        Returns:
            str: 不带namespace的节点名称
        """
        # 如果有namespace，取最后一个冒号后的部分
        if ':' in node_name:
            return node_name.split(':')[-1]
        return node_name

    def export_guides(self, guides_list, asset_id=None, collection=None, start_frame=None, end_frame=None):
        """导出guides到abc文件
        
        Args:
            guides_list (list): 要导出的guides物体列表
            asset_id (str): 资产ID，如c001
            collection (str): Collection名称，如COL_Hair
            start_frame (int, optional): 开始帧. Defaults to None.
            end_frame (int, optional): 结束帧. Defaults to None.
        
        Returns:
            bool: 是否成功导出至少一个文件
        """
        if not guides_list:
            print("错误：guides_list为空")
            return False
            
        if not asset_id:
            print("错误：未提供asset_id")
            return False
            
        if not collection:
            print("错误：未提供collection名称")
            return False
            
        # 让用户选择导出目录（只选择一次）
        export_dir = mc.fileDialog2(
            fileMode=3,  # 3表示目录选择模式
            caption="选择导出目录",
            okCaption="选择"
        )
        
        if not export_dir:  # 用户取消选择
            print("错误：用户取消选择导出目录")
            return False
            
        export_dir = export_dir[0]  # fileDialog2返回的是列表
        print(f"选择的导出目录: {export_dir}")
            
        # 创建guide计数字典
        guide_counts = {}
        successful_exports = 0
        
        # 遍历每个guides物体进行导出
        for guide in guides_list:
            # 获取不带namespace的名称用于文件命名
            guide_name = self._remove_namespace(guide)
            print(f"\n处理guide: {guide_name} (原始名称: {guide})")
            
            # 获取当前guide的计数，如果不存在则初始化为1
            guide_counts[guide_name] = guide_counts.get(guide_name, 0) + 1
            current_count = guide_counts[guide_name]
            
            # 构建导出ID（包含序号）
            export_id = f"{asset_id}_{current_count:02d}"
            print(f"导出ID: {export_id}")
            
            # 使用统一的导出函数，传入原始guide名称（带namespace）用于导出
            exported_files = export_xgen_guides(
                [guide], 
                export_id, 
                collection, 
                start_frame, 
                end_frame, 
                export_dir
            )
            
            if exported_files:
                successful_exports += 1
                print(f"成功导出guide {guide_name} 到: {exported_files[0]}")
            else:
                print(f"导出 {guide_name} 失败")
                
        print(f"\n导出总结:")
        print(f"- 总计处理: {len(guides_list)} 个guides")
        print(f"- 成功导出: {successful_exports} 个文件")
        
        return successful_exports > 0  # 如果至少有一个guide被成功导出，返回True