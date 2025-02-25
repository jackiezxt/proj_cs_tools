import maya.cmds as mc
from ..core.shader_exporter import ShaderExporter
from ..core.shader_importer import ShaderImporter

class ShaderManagerUI:
    def __init__(self):
        self.window_name = "lookdevTransferWindow"
        self.exporter = None
        self.importer = None
        
    def show(self):
        if mc.window(self.window_name, exists=True):
            mc.deleteUI(self.window_name)
            
        window = mc.window(
            self.window_name,
            title="材质传递工具",
            widthHeight=(400, 150)
        )
        
        mc.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # 导出路径设置
        mc.rowLayout(numberOfColumns=4, columnWidth4=(80, 200, 50, 50), adjustableColumn=2)
        mc.text(label="导出路径: ")
        self.path_field = mc.textField()
        mc.button(label="浏览", command=self.browse_path)
        mc.button(label="导出", command=self.export_shaders)
        mc.setParent('..')
        
        mc.separator(height=10, style='in')
        
        # 材质赋予
        mc.button(
            label="赋予材质",
            height=50,
            command=self.apply_shaders
        )
        
        # 初始化导出器并设置默认路径
        try:
            self.exporter = ShaderExporter()
            mc.textField(self.path_field, e=True, tx=self.exporter.export_path)
        except Exception as e:
            mc.confirmDialog(title='错误', message=str(e), button=['确定'])
            
        mc.showWindow(window)
        
    def browse_path(self, *args):
        path = mc.fileDialog2(
            fileMode=3,
            dialogStyle=2,
            caption="选择导出路径"
        )
        if path:
            mc.textField(self.path_field, e=True, tx=path[0])
            if self.exporter:
                self.exporter.set_export_path(path[0])
                
    def export_shaders(self, *args):
        try:
            if not self.exporter:
                self.exporter = ShaderExporter()
                
            json_path, ma_path = self.exporter.export_shaders()
            
            message = f"导出成功！\n\nJSON文件：{json_path}"
            if ma_path:
                message += f"\n材质文件：{ma_path}"
                
            mc.confirmDialog(title='成功', message=message, button=['确定'])
            
        except Exception as e:
            mc.confirmDialog(title='错误', message=str(e), button=['确定'])
            
    def apply_shaders(self, *args):
        try:
            self.importer = ShaderImporter()
            unmatched = self.importer.apply_shaders()
            
            if unmatched:
                message = "以下物体未能正确赋予材质：\n\n" + "\n".join(unmatched)
                mc.confirmDialog(title='警告', message=message, button=['确定'])
            else:
                mc.confirmDialog(title='成功', message='材质赋予完成！', button=['确定'])
                
        except Exception as e:
            mc.confirmDialog(title='错误', message=str(e), button=['确定'])