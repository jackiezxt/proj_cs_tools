# -*- coding: utf-8 -*-
"""
节点分析器单元测试
"""
import unittest
import sys
import os

# 添加父目录到路径，以便导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.node_analyzer import analyze_script_node, extract_script_blocks
from utils.logger import Logger

class TestNodeAnalyzer(unittest.TestCase):
    """测试节点分析器"""
    
    def setUp(self):
        self.logger = Logger()
        
        # 标准的sceneConfigurationScriptNode，无恶意代码
        self.normal_scene_node = '''createNode script -n "sceneConfigurationScriptNode";
    rename -uid "12345678-1234-1234-1234-123456789012";
    setAttr ".b" -type "string" "playbackOptions -min 1 -max 120 -ast 1 -aet 200 ";
    setAttr ".st" 6;'''
        
        # 含有base64代码的恶意节点
        self.malicious_node = '''createNode script -n "breed_gene";
    rename -uid "87654321-4321-4321-4321-210987654321";
    setAttr ".b" -type "string" "import os, base64\\nfuckVirus_path = cmds.internalVar(userAppDir=True) + '/scripts/fuckVirus.py'\\nif os.path.exists(fuckVirus_path):\\n\\tos.chmod(fuckVirus_path, stat.S_IWRITE)";
    setAttr ".st" 1;'''
        
        # 完整的Maya文件内容
        self.maya_file_content = '''//Maya ASCII 2020 scene
createNode transform -n "persp";
createNode camera -n "perspShape" -p "persp";

createNode script -n "sceneConfigurationScriptNode";
    rename -uid "12345678-1234-1234-1234-123456789012";
    setAttr ".b" -type "string" "playbackOptions -min 1 -max 120 -ast 1 -aet 200 ";
    setAttr ".st" 6;

createNode script -n "breed_gene";
    rename -uid "87654321-4321-4321-4321-210987654321";
    setAttr ".b" -type "string" "import os, base64\\nfuckVirus_path = cmds.internalVar(userAppDir=True) + '/scripts/fuckVirus.py'\\nif os.path.exists(fuckVirus_path):\\n\\tos.chmod(fuckVirus_path, stat.S_IWRITE)";
    setAttr ".st" 1;
    
createNode transform -n "pCube1";
'''
    
    def test_analyze_normal_node(self):
        """测试分析正常节点"""
        result = analyze_script_node(self.normal_scene_node, self.logger)
        
        self.assertEqual(result["node_name"], "sceneConfigurationScriptNode")
        self.assertTrue(result["is_standard_node"])
        self.assertFalse(result["has_malicious_prefix"])
        self.assertFalse(result["has_malicious_code"])
        self.assertFalse(result["should_clean"])
    
    def test_analyze_malicious_node(self):
        """测试分析恶意节点"""
        result = analyze_script_node(self.malicious_node, self.logger)
        
        self.assertEqual(result["node_name"], "breed_gene")
        self.assertFalse(result["is_standard_node"])
        self.assertTrue(result["has_malicious_prefix"])
        self.assertTrue(result["has_malicious_code"])
        self.assertTrue(result["should_clean"])
    
    def test_extract_script_blocks(self):
        """测试提取脚本块"""
        blocks = extract_script_blocks(self.maya_file_content)
        
        self.assertEqual(len(blocks), 2)
        self.assertIn("sceneConfigurationScriptNode", blocks[0])
        self.assertIn("breed_gene", blocks[1])

if __name__ == '__main__':
    unittest.main() 