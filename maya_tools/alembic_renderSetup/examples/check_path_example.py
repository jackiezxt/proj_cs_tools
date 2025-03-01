from maya_tools.alembic_renderSetup.core.path_checker import PathChecker

# 创建路径检查器
checker = PathChecker()

# 检查特定镜头路径，不导入LookDev文件
result = checker.check_shot_path("PV", "Sq01", "Sc0040", import_lookdev=False)
print(f"路径检查结果: {result}")

# 使用镜头ID检查，并导入LookDev文件
result = checker.check_shot_by_id("sc0040", import_lookdev=True)
print(f"镜头ID检查结果: {result}")

# 也可以单独检查某个资产的LookDev文件
lookdev_file = checker._check_lookdev_file("C001", "Chars", import_file=True)
if lookdev_file:
    print(f"找到并导入了LookDev文件: {lookdev_file}")
