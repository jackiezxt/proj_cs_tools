import os
import maya.standalone
import maya.cmds as cmds
from maya_tools import alembic_exporter


def process_maya_files(root_dir):
    # 初始化 Maya 独立环境
    maya.standalone.initialize()

    # 遍历目录下的所有 Maya 文件
    total_files = 0
    success_count = 0
    fail_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(('.ma', '.mb')):
                total_files += 1
                maya_file = os.path.join(dirpath, filename)
                print(f"正在处理: {maya_file}")
                try:
                    # 打开 Maya 文件
                    cmds.file(maya_file, open=True, force=True)
                    # 导出 Alembic
                    exported_files = alembic_exporter.export_alembic()
                    print(f"处理完成: {maya_file}")
                    print(f"导出文件: {exported_files}")
                    success_count += 1
                except Exception as e:
                    print(f"处理失败: {maya_file}")
                    print(f"错误信息: {str(e)}")
                    fail_count += 1
    
    # 打印处理总结
    print(f"\n处理统计:")
    print(f"总文件数: {total_files}")
    print(f"成功文件数: {success_count}")
    print(f"失败文件数: {fail_count}")

    # 关闭 Maya 独立环境
    maya.standalone.uninitialize()


if __name__ == "__main__":
    # 设置要处理的根目录
    root_dir = r"X:/projects/CSprojectFiles/Shot/Animation/PV/Sq04"
    process_maya_files(root_dir)
