import os
import re
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.script_templates import get_template_for_task
from core.tools.planning_tool import PlanningTool

def test_type_hint_fixing():
    """
    型ヒントの修正機能をテストする
    """
    print("=== 型ヒントの修正機能テスト ===")
    
    test_code = """
import Dict
import List
import os
import json
import time
import re
import datetime
import traceback
from typing import Any, Optional, Union, Tuple

def process_data(data_dict: Dict):
    result_list: List = []
    return result_list
"""
    
    planning_tool = PlanningTool(None, None)
    
    missing_modules, modified_code = planning_tool._check_imports(test_code)
    
    python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                        "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
    
    print("\n修正後のコード:")
    print(modified_code[:200] + "...")
    
    direct_type_import_pattern = r'(?:^|\n)\s*import\s+(' + '|'.join(python_type_hints) + r')\b'
    match = re.search(direct_type_import_pattern, modified_code)
    if match:
        print(f"✗ 型ヒントの直接インポートが修正されていません: {match.group(0)}")
        print(f"マッチした位置: {match.start()}-{match.end()}")
        print(f"前後のコンテキスト: {modified_code[max(0, match.start()-20):min(len(modified_code), match.end()+20)]}")
    else:
        print("✓ 型ヒントの直接インポートが修正されました")
    
    template = get_template_for_task("データ分析タスクを実行する")
    
    if "from typing import Dict, List" in template:
        print("✓ テンプレートに型ヒントのインポートが正しく含まれています")
    else:
        print("✗ テンプレートに型ヒントのインポートが正しく含まれていません")
    
    if "global get_related_knowledge" in template:
        print("✓ テンプレートにグローバル変数宣言が含まれています")
    else:
        print("✗ テンプレートにグローバル変数宣言が含まれていません")
    
    print("\n修正後のコード:")
    print(modified_code[:200] + "...")
    print("\nテスト完了")

if __name__ == "__main__":
    test_type_hint_fixing()
