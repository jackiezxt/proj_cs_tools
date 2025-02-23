import maya.cmds as mc
from ..core.checker import GeometryChecker

class ModelCheckUI:
    def __init__(self):
        self.window_name = "modelCheckWindow"
        self.checker = GeometryChecker()
        
    def show(self):
        if mc.window(self.window_name, exists=True):
            mc.deleteUI(self.window_name)
            
        window = mc.window(
            self.window_name,
            title="模型检查工具",
            widthHeight=(300, 200)
        )
        
        mc.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        mc.text(label="当前文件:", align="left")
        mc.text(label=mc.file(q=True, sn=True), align="left")
        
        mc.separator(height=10)
        
        mc.button(
            label="检查当前文件",
            command=lambda x: self.check_current_file()
        )
        
        mc.separator(height=10)
        
        mc.text(label="输入要对比的文件前缀 (如: C013):", align="left")
        self.compare_field = mc.textField()
        
        mc.button(
            label="与之前文件对比",
            command=lambda x: self.compare_with_previous()
        )
        
        mc.showWindow(window)
        
    def check_current_file(self):
        try:
            data = self.checker.get_geometry_info()
            json_path = self.checker.save_check_result(data)
            
            # 显示检查结果
            result = "检查完成！\n\n"
            for group_path, group_info in data.items():
                result += f"组: {group_path}\n"
                for mesh in group_info["meshes"]:
                    result += f"  - {mesh['name']}: {mesh['vertex_count']} 顶点\n"
                result += "\n"
                
            mc.confirmDialog(
                title="检查结果",
                message=f"{result}\n结果已保存到: {json_path}",
                button=["确定"]
            )
            
        except Exception as e:
            mc.confirmDialog(
                title="错误",
                message=str(e),
                button=["确定"],
                icon="critical"
            )
            
    def compare_with_previous(self):
        try:
            # 获取当前数据
            current_data = self.checker.get_geometry_info()
            
            # 获取要对比的文件前缀
            previous_prefix = mc.textField(self.compare_field, q=True, text=True)
            if not previous_prefix:
                raise RuntimeError("请输入要对比的文件前缀")
                
            # 进行对比
            differences = self.checker.compare_with_previous(current_data, previous_prefix)
            
            if differences:
                result = "发现以下差异：\n\n" + "\n".join(differences)
            else:
                result = "两个文件的模型结构完全相同"
                
            mc.confirmDialog(
                title="对比结果",
                message=result,
                button=["确定"]
            )
            
        except Exception as e:
            mc.confirmDialog(
                title="错误",
                message=str(e),
                button=["确定"],
                icon="critical"
            )