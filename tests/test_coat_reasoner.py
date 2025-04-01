import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.coat_reasoner import COATReasoner

class TestCOATReasoner(unittest.TestCase):
    
    def setUp(self):
        """テスト前の準備"""
        self.llm_mock = MagicMock()
        self.reasoner = COATReasoner(self.llm_mock)
    
    def test_init(self):
        """初期化のテスト"""
        self.assertEqual(self.reasoner.llm, self.llm_mock)
    
    def test_extract_json_valid(self):
        """有効なJSONの抽出をテスト"""
        valid_json_text = """
        Some text before the JSON
        
        {
            "coat_chain": [
                {
                    "thought": "Test thought",
                    "action": "Test action",
                    "prediction": "Test prediction"
                }
            ],
            "final_solution": "Test solution"
        }
        
        Some text after the JSON
        """
        
        expected_json = {
            "coat_chain": [
                {
                    "thought": "Test thought",
                    "action": "Test action",
                    "prediction": "Test prediction"
                }
            ],
            "final_solution": "Test solution"
        }
        
        result = self.reasoner._extract_json(valid_json_text)
        self.assertEqual(result, expected_json)
    
    def test_extract_json_invalid(self):
        """無効なJSONの抽出をテスト（デフォルト値が返されるべき）"""
        invalid_json_text = """
        Some text without any valid JSON
        """
        
        result = self.reasoner._extract_json(invalid_json_text)
        self.assertIn("coat_chain", result)
        self.assertIn("final_solution", result)
        self.assertEqual(len(result["coat_chain"]), 1)
    
    def test_generate_action_thought_chain(self):
        """アクション思考チェーンの生成をテスト"""
        mock_response = """
        ```json
        {
            "coat_chain": [
                {
                    "thought": "エラーはインデックスが範囲外のようだ",
                    "action": "リストの長さをチェックする条件を追加",
                    "prediction": "インデックスエラーが解消される"
                },
                {
                    "thought": "例外処理が不足している",
                    "action": "try-except文を追加",
                    "prediction": "エラーが適切に処理される"
                }
            ],
            "final_solution": "修正されたコード"
        }
        ```
        """
        self.llm_mock.generate_text.return_value = mock_response
        
        expected_result = {
            "coat_chain": [
                {
                    "thought": "エラーはインデックスが範囲外のようだ",
                    "action": "リストの長さをチェックする条件を追加",
                    "prediction": "インデックスエラーが解消される"
                },
                {
                    "thought": "例外処理が不足している",
                    "action": "try-except文を追加",
                    "prediction": "エラーが適切に処理される"
                }
            ],
            "final_solution": "修正されたコード"
        }
        
        result = self.reasoner.generate_action_thought_chain(
            task_description="テストタスク",
            current_state="現在の状態",
            error_message="インデックスエラー"
        )
        
        self.llm_mock.generate_text.assert_called_once()
        prompt_arg = self.llm_mock.generate_text.call_args[0][0]
        self.assertIn("テストタスク", prompt_arg)
        self.assertIn("現在の状態", prompt_arg)
        self.assertIn("インデックスエラー", prompt_arg)
        
        self.assertEqual(result, expected_result)
    
    def test_apply_coat_reasoning(self):
        """COATを適用したコード修正をテスト"""
        mock_chain_result = {
            "coat_chain": [
                {
                    "thought": "エラーはインデックスが範囲外のようだ",
                    "action": "リストの長さをチェックする条件を追加",
                    "prediction": "インデックスエラーが解消される"
                }
            ],
            "final_solution": """
            ```python
            def process_list(items):
                if len(items) > 0:  # 修正: 空リストのチェックを追加
                    return items[0]
                return None
            ```
            """
        }
        
        with patch.object(self.reasoner, 'generate_action_thought_chain', return_value=mock_chain_result):
            code = "def process_list(items):\n    return items[0]"
            error_message = "IndexError: list index out of range"
            
            fixed_code, coat_chain = self.reasoner.apply_coat_reasoning(code, error_message)
            
            self.assertIn("if len(items) > 0", fixed_code)
            
            self.assertEqual(len(coat_chain), 1)
            self.assertEqual(coat_chain[0]["thought"], "エラーはインデックスが範囲外のようだ")

if __name__ == '__main__':
    unittest.main()
