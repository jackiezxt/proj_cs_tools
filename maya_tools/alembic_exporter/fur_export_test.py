"""
毛发生长面(Fur_Grp)导出测试脚本

此脚本用于在Maya中测试毛发生长面(Fur_Grp)的查找和导出功能。
可以直接在Maya脚本编辑器中运行此脚本进行测试。
"""

import maya.cmds as mc
from maya_tools.alembic_exporter.core.helpers import get_fur_groups
from maya_tools.alembic_exporter.export import export_fur_alembic

def test_find_fur_groups():
    """测试查找场景中的毛发生长面Fur_Grp组"""
    print("\n===== 开始测试查找毛发生长面Fur_Grp组 =====")
    
    # 获取场景中的毛发生长面组
    fur_groups = get_fur_groups()
    
    if not fur_groups:
        print("未在场景中找到任何毛发生长面Fur_Grp组")
        return False
    
    # 输出找到的毛发生长面组
    print(f"在场景中找到 {len(fur_groups)} 个角色的毛发生长面组:")
    
    for asset_id, groups in fur_groups.items():
        print(f"\n角色 {asset_id} 的毛发生长面组 ({len(groups)}个):")
        for i, group in enumerate(groups, 1):
            print(f"  {i}. {group}")
            
            # 获取并打印毛发生长面组的子节点
            children = mc.listRelatives(group, children=True, fullPath=True) or []
            if children:
                print(f"     包含 {len(children)} 个子节点:")
                for j, child in enumerate(children[:5], 1):  # 仅显示前5个子节点
                    print(f"     {j}. {child}")
                
                if len(children) > 5:
                    print(f"     ...还有 {len(children) - 5} 个子节点未显示")
    
    return True

def test_export_fur():
    """测试导出毛发生长面Fur_Grp为Alembic缓存"""
    print("\n===== 开始测试导出毛发生长面Fur_Grp =====")
    
    # 确保Maya文件已保存
    current_file = mc.file(q=True, sn=True)
    if not current_file:
        print("错误: 请先保存Maya文件，然后再尝试导出")
        return False
    
    # 尝试导出
    try:
        print("正在导出毛发生长面Fur_Grp...")
        exported_files = export_fur_alembic()
        
        if exported_files:
            print(f"\n成功导出 {len(exported_files)} 个毛发生长面Fur_Grp的Alembic缓存:")
            for i, file_path in enumerate(exported_files, 1):
                print(f"{i}. {file_path}")
            return True
        else:
            print("未导出任何文件，可能是场景中没有找到毛发生长面Fur_Grp")
            return False
    
    except Exception as e:
        print(f"导出过程中发生错误: {str(e)}")
        return False

def run_tests():
    """运行所有测试"""
    print("\n============================================")
    print("     毛发生长面(Fur_Grp)导出测试开始       ")
    print("============================================\n")
    
    # 测试查找毛发生长面Fur_Grp
    found_groups = test_find_fur_groups()
    
    # 如果找到毛发生长面组，询问是否导出
    if found_groups:
        result = mc.confirmDialog(
            title='确认导出',
            message='是否要导出找到的毛发生长面Fur_Grp？',
            button=['导出', '取消'],
            defaultButton='导出',
            cancelButton='取消',
            dismissString='取消'
        )
        
        if result == '导出':
            # 测试导出毛发生长面Fur_Grp
            test_export_fur()
    
    print("\n============================================")
    print("     毛发生长面(Fur_Grp)导出测试完成       ")
    print("============================================\n")

# 如果直接运行此脚本，则执行所有测试
if __name__ == "__main__":
    run_tests() 