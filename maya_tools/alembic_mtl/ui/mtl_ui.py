# coding: utf-8
"""
材质赋予工具的UI模块
"""
import maya.cmds as mc
from ..core.mtl_logic import MaterialAssignLogic

class MaterialAssignUI:
    """材质赋予工具UI类"""
    
    def __init__(self):
        self.window_name = "materialAssignToolUI"
        self.logic = MaterialAssignLogic()
        self.shaded_items = []  # 有材质的项目
        self.default_items = []  # 无材质的项目
        self.left_list = None    # 左侧列表UI控件
        self.right_list = None   # 右侧列表UI控件
        self.sync_selection = True  # 是否同步选择
        
        # 创建UI
        self.create_ui()
    
    def create_ui(self):
        """创建UI界面"""
        # 如果窗口已存在，则删除
        if mc.window(self.window_name, exists=True):
            mc.deleteUI(self.window_name)
        
        # 创建窗口
        mc.window(self.window_name, title="材质赋予工具", width=800, height=600)
        
        # 主布局
        main_layout = mc.columnLayout(adjustableColumn=True)
        
        # 顶部说明
        mc.frameLayout(label="使用说明", collapsable=True, collapse=False)
        mc.columnLayout(adjustableColumn=True)
        mc.text(label="左侧列表: 有材质的模型", align="left")
        mc.text(label="右侧列表: 没有材质的模型 (使用默认材质)", align="left")
        mc.text(label="注意: 只有面数相同的模型才能进行材质赋予", align="left")
        mc.text(label="操作: 选择左右两侧要匹配的模型，然后点击'赋予材质'按钮", align="left")
        mc.setParent('..')
        mc.setParent('..')
        
        # 刷新按钮和同步选择复选框
        buttons_row = mc.rowLayout(numberOfColumns=2, columnWidth2=(390, 390))
        mc.button(label="刷新场景模型", width=380, command=self.refresh_lists)
        self.sync_checkbox = mc.checkBox(label="同步左右列表选择", value=self.sync_selection, 
                                        changeCommand=self.toggle_sync_selection)
        mc.setParent('..')
        mc.separator(height=10)
        
        # 列表布局
        lists_layout = mc.rowLayout(numberOfColumns=2, columnWidth2=(390, 390), adjustableColumn=1)
        
        # 左侧列表 (有材质的模型)
        left_column = mc.columnLayout(adjustableColumn=True)
        mc.text(label="有材质的模型:", align="left", font="boldLabelFont")
        self.left_list = mc.textScrollList(width=380, height=400, allowMultiSelection=False, 
                                          selectCommand=self.on_left_list_selected)
        mc.setParent('..')
        
        # 右侧列表 (无材质的模型)
        right_column = mc.columnLayout(adjustableColumn=True)
        mc.text(label="无材质的模型:", align="left", font="boldLabelFont")
        self.right_list = mc.textScrollList(width=380, height=400, allowMultiSelection=False,
                                           selectCommand=self.on_right_list_selected)
        mc.setParent('..')
        
        mc.setParent('..')  # 回到主布局
        
        # 信息显示区域
        self.info_text = mc.text(label="就绪。请刷新场景模型列表。", align="left")
        mc.separator(height=10)
        
        # 按钮区域
        buttons_layout = mc.rowLayout(numberOfColumns=2, columnWidth2=(390, 390))
        mc.button(label="赋予材质 (选中项)", width=380, command=self.assign_selected)
        mc.button(label="为所有匹配模型赋予材质", width=380, command=self.assign_all)
        mc.setParent('..')
        
        # 显示窗口
        mc.showWindow(self.window_name)
        
        # 初始刷新模型列表
        self.refresh_lists()
    
    def toggle_sync_selection(self, value):
        """切换是否同步选择"""
        self.sync_selection = value
        
        # 如果开启同步，则尝试自动匹配
        if self.sync_selection and self.shaded_items and self.default_items:
            # 先检查是否已经有选中的项目
            left_index = mc.textScrollList(self.left_list, query=True, selectIndexedItem=True)
            right_index = mc.textScrollList(self.right_list, query=True, selectIndexedItem=True)
            
            if left_index:
                # 如果左侧有选中项，触发左侧选择事件
                self.on_left_list_selected()
            elif right_index:
                # 如果右侧有选中项，触发右侧选择事件
                self.on_right_list_selected()
            else:
                # 如果两侧都没有选中项，执行自动匹配
                self.auto_match_first_item()
    
    def on_left_list_selected(self):
        """左侧列表选择变化时的处理"""
        if not self.sync_selection:
            return
            
        # 获取左侧选中的项目索引
        left_index = mc.textScrollList(self.left_list, query=True, selectIndexedItem=True)
        if not left_index:
            return
            
        # 获取选中模型的面数
        left_item = self.shaded_items[left_index[0]-1]
        left_face_count = left_item['data'].polyCount
        
        # 查找右侧列表中面数匹配的第一个模型
        matching_index = None
        for i, item in enumerate(self.default_items):
            if item['data'].polyCount == left_face_count:
                matching_index = i + 1  # 列表索引从1开始
                break
        
        # 如果找到匹配的项目，选中它
        if matching_index:
            # 取消之前的选择避免触发右侧列表的选择事件
            mc.textScrollList(self.right_list, edit=True, deselectAll=True)
            # 设置右侧列表选择
            mc.textScrollList(self.right_list, edit=True, selectIndexedItem=matching_index)
    
    def on_right_list_selected(self):
        """右侧列表选择变化时的处理"""
        if not self.sync_selection:
            return
            
        # 获取右侧选中的项目索引
        right_index = mc.textScrollList(self.right_list, query=True, selectIndexedItem=True)
        if not right_index:
            return
            
        # 获取选中模型的面数
        right_item = self.default_items[right_index[0]-1]
        right_face_count = right_item['data'].polyCount
        
        # 查找左侧列表中面数匹配的第一个模型
        matching_index = None
        for i, item in enumerate(self.shaded_items):
            if item['data'].polyCount == right_face_count:
                matching_index = i + 1  # 列表索引从1开始
                break
        
        # 如果找到匹配的项目，选中它
        if matching_index:
            # 取消之前的选择避免触发左侧列表的选择事件
            mc.textScrollList(self.left_list, edit=True, deselectAll=True)
            # 设置左侧列表选择
            mc.textScrollList(self.left_list, edit=True, selectIndexedItem=matching_index)
    
    def refresh_lists(self, *args):
        """刷新模型列表"""
        # 更新状态文本
        mc.text(self.info_text, edit=True, label="正在刷新场景模型列表...")
        
        # 清空列表
        mc.textScrollList(self.left_list, edit=True, removeAll=True)
        mc.textScrollList(self.right_list, edit=True, removeAll=True)
        
        # 获取场景数据
        self.logic.refresh_scene_data()
        mesh_data = self.logic.get_mesh_names_without_namespace()
        
        # 更新左侧列表(有材质的模型)
        self.shaded_items = mesh_data['shaded']
        for item in self.shaded_items:
            display_text = f"{item['display_name']} ({item['data'].polyCount}面)"
            mc.textScrollList(self.left_list, edit=True, append=display_text)
        
        # 更新右侧列表(无材质的模型)
        self.default_items = mesh_data['default']
        for item in self.default_items:
            display_text = f"{item['display_name']} ({item['data'].polyCount}面)"
            mc.textScrollList(self.right_list, edit=True, append=display_text)
        
        # 更新状态文本
        shaded_count = len(self.shaded_items)
        default_count = len(self.default_items)
        mc.text(self.info_text, edit=True, 
            label=f"刷新完成。找到 {shaded_count} 个有材质的模型和 {default_count} 个无材质的模型。")
            
        # 如果同步选择开启，且两侧列表都有项目，则自动选中第一个匹配的项目
        if self.sync_selection and self.shaded_items and self.default_items:
            self.auto_match_first_item()
            
    def auto_match_first_item(self):
        """自动匹配第一个项目"""
        # 先尝试根据面数找到适合的匹配对
        for i, shaded_item in enumerate(self.shaded_items):
            shaded_face_count = shaded_item['data'].polyCount
            
            for j, default_item in enumerate(self.default_items):
                if default_item['data'].polyCount == shaded_face_count:
                    # 找到匹配的面数，选中两边对应的项目
                    mc.textScrollList(self.left_list, edit=True, selectIndexedItem=i+1)
                    mc.textScrollList(self.right_list, edit=True, selectIndexedItem=j+1)
                    
                    # 更新状态文本
                    mc.text(self.info_text, edit=True, 
                        label=f"自动匹配: {shaded_item['display_name']} 和 {default_item['display_name']} (面数: {shaded_face_count})")
                    return
        
        # 如果没有找到面数匹配的，就简单地选择两边的第一项
        if self.shaded_items and self.default_items:
            mc.textScrollList(self.left_list, edit=True, selectIndexedItem=1)
            mc.textScrollList(self.right_list, edit=True, selectIndexedItem=1)
    
    def assign_selected(self, *args):
        """为选中的项目赋予材质"""
        # 获取选中的项目索引
        left_index = mc.textScrollList(self.left_list, query=True, selectIndexedItem=True)
        right_index = mc.textScrollList(self.right_list, query=True, selectIndexedItem=True)
        
        # 检查是否有选择
        if not left_index or not right_index:
            mc.text(self.info_text, edit=True, label="错误: 请在左右两侧列表中各选择一个模型")
            return
        
        # 获取选中的项目数据
        shaded_mesh = self.shaded_items[left_index[0]-1]['data']
        default_mesh = self.default_items[right_index[0]-1]['data']
        
        # 执行材质赋予
        result = self.logic.assign_one_to_one(shaded_mesh, default_mesh)
        
        # 更新状态
        if result:
            mc.text(self.info_text, edit=True, 
                label=f"成功将 {shaded_mesh.name} 的材质赋予给 {default_mesh.name}")
        else:
            mc.text(self.info_text, edit=True, 
                label=f"材质赋予失败，请检查选择的模型")
    
    def assign_all(self, *args):
        """为所有匹配的模型赋予材质"""
        # 执行批量赋予
        result = self.logic.assign_all_matching()
        
        # 更新状态
        if result:
            mc.text(self.info_text, edit=True, label="批量材质赋予完成")
        else:
            mc.text(self.info_text, edit=True, label="批量材质赋予失败，请查看脚本编辑器获取详细信息")

# 显示UI函数
def show_window():
    """显示材质赋予工具UI"""
    ui = MaterialAssignUI()
    return ui 