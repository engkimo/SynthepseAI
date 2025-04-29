import os
import sys
import json
import re
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.script_templates import get_template_for_task
from core.tools.planning_tool import PlanningTool

class MockLLM:
    """テスト用のモックLLM"""
    def __init__(self):
        self.mock_mode = True
    
    def generate_text(self, prompt):
        return "モックLLMからの応答"
    
    def generate_code(self, prompt):
        return '''
import Dict
import List
import os
import json
import time

def analyze_data(data_dict: Dict) -> List:
    """データを分析する関数"""
    result_list: List = []
    for key, value in data_dict.items():
        result_list.append(f"{key}: {value}")
    return result_list

data = {"name": "テスト", "value": 123}
result = analyze_data(data)
print(result)
'''

def test_check_imports_method():
    """_check_importsメソッドのテスト"""
    print("=== _check_importsメソッドのテスト ===")
    
    test_code = '''
import Dict
import List
import os
import json
import time

def analyze_data(data_dict: Dict) -> List:
    """データを分析する関数"""
    result_list: List = []
    for key, value in data_dict.items():
        result_list.append(f"{key}: {value}")
    return result_list

data = {"name": "テスト", "value": 123}
result = analyze_data(data)
print(result)
'''
    
    planning_tool = PlanningTool(None, None)
    
    missing_modules, modified_code = planning_tool._check_imports(test_code)
    
    print(f"検出された不足モジュール: {missing_modules}")
    
    python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                        "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
    direct_type_import_pattern = r'(?:^|\n)\s*import\s+(' + '|'.join(python_type_hints) + r')\b'
    
    match = re.search(direct_type_import_pattern, modified_code)
    if match:
        print("✗ 修正後のコードに型ヒントの直接インポートが含まれています")
        print(f"  マッチした内容: {match.group(0)}")
        print(f"  マッチした位置: {match.start()}-{match.end()}")
        print(f"  前後のコンテキスト: {modified_code[max(0, match.start()-20):min(len(modified_code), match.end()+20)]}")
    else:
        print("✓ 修正後のコードに型ヒントの直接インポートは含まれていません")
    
    if "from typing import" in modified_code:
        print("✓ 修正後のコードにtypingからのインポートが含まれています")
        typing_import_match = re.search(r'from typing import[^\n]*', modified_code)
        if typing_import_match:
            print(f"  インポート行: {typing_import_match.group(0)}")
    else:
        print("✗ 修正後のコードにtypingからのインポートが含まれていません")
    
    print("\n修正後のコード（一部）:")
    print(modified_code[:300] + "...\n")

def test_template_generation():
    """スクリプトテンプレート生成のテスト"""
    print("=== スクリプトテンプレート生成テスト ===")
    
    template = get_template_for_task("データ分析タスクを実行する")
    
    if "from typing import" in template:
        print("✓ テンプレートに型ヒントのインポートが含まれています")
    else:
        print("✗ テンプレートに型ヒントのインポートが含まれていません")
    
    if "{main_code}" in template:
        print("✓ テンプレートにmain_codeプレースホルダーが含まれています")
    else:
        print("✗ テンプレートにmain_codeプレースホルダーが含まれていません")
    
    if "{imports}" in template:
        print("✓ テンプレートにimportsプレースホルダーが含まれています")
    else:
        print("✗ テンプレートにimportsプレースホルダーが含まれていません")
    
    if "global get_related_knowledge" in template:
        print("✓ テンプレートにグローバル変数宣言が含まれています")
    else:
        print("✗ テンプレートにグローバル変数宣言が含まれていません")
    
    print("\nテンプレート（一部）:")
    print(template[:300] + "...\n")

if __name__ == "__main__":
    test_template_generation()
    print("\n" + "-" * 50 + "\n")
    test_check_imports_method()
