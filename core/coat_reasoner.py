from typing import Dict, List, Any, Optional, Tuple
import json
import re

class COATReasoner:
    """
    COAT（Chain-of-Action-Thought）を実装し、自己反省型推論を行うクラス
    """
    
    def __init__(self, llm):
        self.llm = llm
        
    def generate_action_thought_chain(self, task_description: str, current_state: str, error_message: str = None) -> Dict:
        """
        Chain-of-Action-Thoughtを生成
        
        Args:
            task_description: タスクの説明
            current_state: 現在の状態
            error_message: エラーメッセージ（ある場合）
            
        Returns:
            アクション、思考、予測のチェーン
        """
        error_context = ""
        if error_message:
            error_context = f"""
            エラーが発生しました：
            ```
            {error_message}
            ```
            
            このエラーを分析し、以下のCOATチェーンを立てて修正してください。
            """
            
        prompt = f"""
        {task_description}
        
        {current_state}
        
        {error_context}
        
        Chain-of-Action-Thought (COAT)方式で段階的に問題を解決してください。以下の形式で回答してください：
        
        ```json
        {{
            "coat_chain": [
                {{
                    "thought": "何が問題か、なぜそれが起きているのか考える",
                    "action": "問題を解決するための具体的なアクション",
                    "prediction": "このアクションの予測される結果"
                }},
                ...追加のステップ
            ],
            "final_solution": "最終的な解決策のコードまたは説明"
        }}
        ```
        
        各ステップは「考え」から始め、その考えに基づく「アクション」を決定し、そのアクションの「予測」で終わります。
        少なくとも3つのステップを含めてください。
        """
        
        response = self.llm.generate_text(prompt)
        
        coat_chain = self._extract_json(response)
        
        return coat_chain
    
    def _extract_json(self, text: str) -> Dict:
        """テキストからJSONを抽出"""
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, text)
        
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                return {
                    "coat_chain": [
                        {
                            "thought": "問題が特定できませんでした",
                            "action": "デフォルトの修正手順を適用",
                            "prediction": "問題が解決する可能性がある"
                        }
                    ],
                    "final_solution": "問題の詳細を分析し、適切な解決策を提案できませんでした。"
                }
        else:
            return {
                "coat_chain": [
                    {
                        "thought": "応答からJSONが抽出できませんでした",
                        "action": "デフォルトの修正手順を適用",
                        "prediction": "問題が解決する可能性がある"
                    }
                ],
                "final_solution": "JSONの抽出に失敗しました。応答の形式が正しくない可能性があります。"
            }
            
    def apply_coat_reasoning(self, code: str, error_message: str) -> Tuple[str, List[Dict]]:
        """
        COATを適用してコードを修正
        
        Args:
            code: 修正するコード
            error_message: エラーメッセージ
            
        Returns:
            (修正されたコード, 実行されたCOATチェーン)
        """
        coat_chain_result = self.generate_action_thought_chain(
            task_description="コードのエラーを修正する",
            current_state=f"現在のコード:\n```python\n{code}\n```",
            error_message=error_message
        )
        
        final_solution = coat_chain_result.get("final_solution", "")
        
        code_pattern = r'```python\s+(.*?)\s+```'
        match = re.search(code_pattern, final_solution, re.DOTALL)
        
        if match:
            fixed_code = match.group(1)
        else:
            fixed_code = final_solution
            
        return fixed_code, coat_chain_result.get("coat_chain", [])
