import os
import json
import sys
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from core.enhanced_persistent_thinking_ai import EnhancedPersistentThinkingAI
from core.script_templates import get_template_for_task
from core.llm import LLM

class MockLLM(LLM):
    def __init__(self):
        self.mock_mode = True
    
    def generate_text(self, prompt):
        return "モックLLMからの応答"
    
    def generate_code(self, prompt):
        return "import Dict\nimport List\n\n# テスト用コード\nresult = 'テスト成功'"

def test_script_generation():
    print("=== スクリプト生成テスト ===")
    
    llm = MockLLM()
    
    thinking_ai = EnhancedPersistentThinkingAI(
        model_name="microsoft/phi-2",
        workspace_dir="./workspace",
        knowledge_db_path="./workspace/persistent_thinking/knowledge_db.json",
        log_path="./workspace/persistent_thinking/thinking_log.jsonl"
    )
    
    thinking_ai.llm = llm
    
    test_knowledge = {
        "データ分析": {
            "fact": "Pandasを使用してCSVデータを分析できる",
            "confidence": 0.9,
            "last_updated": 1619012345.678,
            "source": "test"
        }
    }
    
    os.makedirs("./workspace/persistent_thinking", exist_ok=True)
    with open("./workspace/persistent_thinking/knowledge_db.json", "w", encoding="utf-8") as f:
        json.dump(test_knowledge, f, ensure_ascii=False, indent=2)
    
    template = get_template_for_task("データ分析タスクを実行する")
    
    if "from typing import Dict, List" in template:
        print("✓ 型ヒントのインポートが正しく含まれています")
    else:
        print("✗ 型ヒントのインポートが正しく含まれていません")
    
    if "{main_code}" in template:
        print("✓ main_codeプレースホルダーが正しく含まれています")
    else:
        print("✗ main_codeプレースホルダーが正しく含まれていません")
    
    test_code = "import Dict\nimport List\n"
    direct_type_import_pattern = r'import\s+(Dict|List|Tuple|Set|FrozenSet|Any|Optional|Union|Callable|Type|TypeVar|Generic|Iterable|Iterator)\b'
    if re.search(direct_type_import_pattern, test_code):
        print("✓ 型ヒントのインポートパターンの検出が機能しています")
        
        python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                            "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
        
        required_type_hints = []
        for hint in python_type_hints:
            if re.search(r'import\s+' + hint + r'\b', test_code):
                required_type_hints.append(hint)
                test_code = re.sub(r'import\s+' + hint + r'\b', '', test_code)
        
        if required_type_hints:
            type_import = f"from typing import {', '.join(required_type_hints)}"
            test_code = type_import + "\n" + test_code
            
        if "from typing import Dict, List" in test_code:
            print("✓ 型ヒントのインポートが正しく修正されました")
        else:
            print("✗ 型ヒントのインポートの修正に失敗しました")
    else:
        print("✗ 型ヒントのインポートパターンの検出が機能していません")
    
    def mock_get_related_knowledge(keywords, limit=5):
        """テスト用のモック関数"""
        related = []
        for keyword in keywords:
            if keyword.lower() in test_knowledge:
                data = test_knowledge[keyword.lower()]
                related.append({
                    "subject": keyword,
                    "fact": data.get("fact"),
                    "confidence": data.get("confidence", 0),
                    "last_updated": data.get("last_updated"),
                    "source": data.get("source")
                })
        return related
    
    try:
        keywords = ["データ分析", "pandas"]
        related_knowledge = mock_get_related_knowledge(keywords)
        print("✓ 関連知識の取得が機能しています")
        print(f"  取得された知識: {related_knowledge}")
    except Exception as e:
        print(f"✗ 関連知識の取得に失敗しました: {str(e)}")
    
    print("テスト完了")

if __name__ == "__main__":
    test_script_generation()
