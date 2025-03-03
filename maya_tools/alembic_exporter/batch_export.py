import os
import maya.standalone
import maya.cmds as cmds
from maya_tools import alembic_exporter


def process_maya_files(root_dir):
    # 初始化 Maya 独立环境
    maya.standalone.initialize()

    # 遍历目录下的所有 Maya 文件
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(('.ma', '.mb')):
                maya_file = os.path.join(dirpath, filename)
                print(f"正在处理: {maya_file}")
                try:
                    # 打开 Maya 文件
                    cmds.file(maya_file, open=True, force=True)
                    # 导出 Alembic
                    alembic_exporter.export_char_alembic()
                    print(f"处理完成: {maya_file}")
                except Exception as e:
                    print(f"处理失败: {maya_file}")
                    print(f"错误信息: {str(e)}")

    # 关闭 Maya 独立环境
    maya.standalone.uninitialize()


if __name__ == "__main__":
    # 设置要处理的根目录
    root_dir = r"X:/projects/CSprojectFiles/Shot/Animation/PV/Sq04"
    process_maya_files(root_dir)
