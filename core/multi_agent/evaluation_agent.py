from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid

from .agent_base import MultiAgentBase, AgentRole, AgentMessage

class EvaluationAgent(MultiAgentBase):
    """
    評価を担当するエージェント
    
    他のエージェントの出力や結果を評価し、フィードバックを提供する
    """
    
    def __init__(
        self,
        agent_id: str = "evaluation_agent",
        name: str = "評価エージェント",
        description: str = "他のエージェントの出力や結果を評価し、フィードバックを提供する",
        llm=None
    ):
        """
        評価エージェントの初期化
        
        Args:
            agent_id: エージェントID
            name: エージェント名
            description: エージェントの説明
            llm: 使用するLLMインスタンス
        """
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.EVALUATION,
            name=name,
            description=description,
            llm=llm
        )
        
        self.evaluation_history = []
    
    def evaluate_text(self, text: str, criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        テキストを評価
        
        Args:
            text: 評価するテキスト
            criteria: 評価基準
            
        Returns:
            評価結果
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        criteria = criteria or {
            "clarity": "明確さ（1-10）",
            "accuracy": "正確さ（1-10）",
            "completeness": "完全性（1-10）",
            "relevance": "関連性（1-10）"
        }
        
        criteria_text = "\n".join([f"- {name}: {desc}" for name, desc in criteria.items()])
        
        prompt = f"""
        以下のテキストを評価してください：
        
        {text}
        
        以下の基準で評価してください：
        {criteria_text}
        
        各基準について1-10の数値で評価し、コメントを付けてください。
        最後に総合評価（1-10）とフィードバックを提供してください。
        
        以下の形式でJSON配列として返してください：
        {{
            "criteria": {{
                "clarity": {{"score": 8, "comment": "コメント"}},
                "accuracy": {{"score": 7, "comment": "コメント"}},
                "completeness": {{"score": 9, "comment": "コメント"}},
                "relevance": {{"score": 8, "comment": "コメント"}}
            }},
            "overall": {{"score": 8, "comment": "総合的なフィードバック"}}
        }}
        """
        
        evaluation_json = self.llm.generate_text(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', evaluation_json, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group(0))
                
                self.evaluation_history.append({
                    "type": "text",
                    "content": text,
                    "evaluation": evaluation,
                    "timestamp": time.time()
                })
                
                return evaluation
            else:
                return {"error": "評価のJSONパースに失敗しました"}
        except Exception as e:
            return {"error": f"評価エラー: {str(e)}"}
    
    def evaluate_code(self, code: str) -> Dict[str, Any]:
        """
        コードを評価
        
        Args:
            code: 評価するコード
            
        Returns:
            評価結果
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        prompt = f"""
        以下のコードを評価してください：
        
        ```
        {code}
        ```
        
        以下の基準で評価してください：
        - 正確性（1-10）: コードが正しく動作するか
        - 効率性（1-10）: コードの実行効率
        - 可読性（1-10）: コードの読みやすさ
        - スタイル（1-10）: コーディング規約の遵守
        - セキュリティ（1-10）: セキュリティ上の問題がないか
        
        各基準について1-10の数値で評価し、コメントを付けてください。
        最後に総合評価（1-10）とフィードバック、改善案を提供してください。
        
        以下の形式でJSON配列として返してください：
        {{
            "criteria": {{
                "correctness": {{"score": 8, "comment": "コメント"}},
                "efficiency": {{"score": 7, "comment": "コメント"}},
                "readability": {{"score": 9, "comment": "コメント"}},
                "style": {{"score": 8, "comment": "コメント"}},
                "security": {{"score": 6, "comment": "コメント"}}
            }},
            "overall": {{"score": 8, "comment": "総合的なフィードバック"}},
            "improvements": ["改善案1", "改善案2"]
        }}
        """
        
        evaluation_json = self.llm.generate_text(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', evaluation_json, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group(0))
                
                self.evaluation_history.append({
                    "type": "code",
                    "content": code,
                    "evaluation": evaluation,
                    "timestamp": time.time()
                })
                
                return evaluation
            else:
                return {"error": "評価のJSONパースに失敗しました"}
        except Exception as e:
            return {"error": f"評価エラー: {str(e)}"}
    
    def evaluate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        計画を評価
        
        Args:
            plan: 評価する計画
            
        Returns:
            評価結果
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        plan_json = json.dumps(plan, ensure_ascii=False, indent=2)
        
        prompt = f"""
        以下の計画を評価してください：
        
        {plan_json}
        
        以下の基準で評価してください：
        - 実現可能性（1-10）: 計画が実現可能か
        - 完全性（1-10）: 計画が完全か
        - 効率性（1-10）: 計画が効率的か
        - リスク管理（1-10）: リスクが適切に管理されているか
        
        各基準について1-10の数値で評価し、コメントを付けてください。
        最後に総合評価（1-10）とフィードバック、改善案を提供してください。
        
        以下の形式でJSON配列として返してください：
        {{
            "criteria": {{
                "feasibility": {{"score": 8, "comment": "コメント"}},
                "completeness": {{"score": 7, "comment": "コメント"}},
                "efficiency": {{"score": 9, "comment": "コメント"}},
                "risk_management": {{"score": 8, "comment": "コメント"}}
            }},
            "overall": {{"score": 8, "comment": "総合的なフィードバック"}},
            "improvements": ["改善案1", "改善案2"]
        }}
        """
        
        evaluation_json = self.llm.generate_text(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', evaluation_json, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group(0))
                
                self.evaluation_history.append({
                    "type": "plan",
                    "content": plan,
                    "evaluation": evaluation,
                    "timestamp": time.time()
                })
                
                return evaluation
            else:
                return {"error": "評価のJSONパースに失敗しました"}
        except Exception as e:
            return {"error": f"評価エラー: {str(e)}"}
    
    def compare_solutions(self, solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        複数の解決策を比較
        
        Args:
            solutions: 比較する解決策のリスト
            
        Returns:
            比較結果
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        solutions_json = json.dumps(solutions, ensure_ascii=False, indent=2)
        
        prompt = f"""
        以下の複数の解決策を比較評価してください：
        
        {solutions_json}
        
        各解決策の長所と短所を分析し、最も優れた解決策を選んでください。
        また、それぞれの解決策の改善案も提案してください。
        
        以下の形式でJSON配列として返してください：
        {{
            "evaluations": [
                {{
                    "solution_id": 0,
                    "strengths": ["長所1", "長所2"],
                    "weaknesses": ["短所1", "短所2"],
                    "score": 8,
                    "improvements": ["改善案1", "改善案2"]
                }},
                // 他の解決策の評価
            ],
            "best_solution": 0,  // 最も優れた解決策のインデックス
            "reasoning": "選択理由"
        }}
        """
        
        comparison_json = self.llm.generate_text(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', comparison_json, re.DOTALL)
            if json_match:
                comparison = json.loads(json_match.group(0))
                
                self.evaluation_history.append({
                    "type": "comparison",
                    "content": solutions,
                    "comparison": comparison,
                    "timestamp": time.time()
                })
                
                return comparison
            else:
                return {"error": "比較のJSONパースに失敗しました"}
        except Exception as e:
            return {"error": f"比較エラー: {str(e)}"}
    
    def _process_single_message(self, message: AgentMessage) -> List[AgentMessage]:
        """
        単一のメッセージを処理
        
        Args:
            message: 処理するメッセージ
            
        Returns:
            処理結果として生成されたメッセージのリスト
        """
        responses = []
        
        if message.message_type == "task":
            metadata = message.metadata or {}
            task_id = metadata.get("task_id")
            task_type = metadata.get("task_type")
            
            if task_type == "evaluate_text":
                content = message.content
                text = content.get("text", "")
                criteria = content.get("criteria")
                
                result = self.evaluate_text(text, criteria)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "evaluate_code":
                content = message.content
                code = content.get("code", "")
                
                result = self.evaluate_code(code)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "evaluate_plan":
                content = message.content
                plan = content.get("plan", {})
                
                result = self.evaluate_plan(plan)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "compare_solutions":
                content = message.content
                solutions = content.get("solutions", [])
                
                result = self.compare_solutions(solutions)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
        
        return responses
    
    def get_evaluation_history(self) -> List[Dict[str, Any]]:
        """評価履歴を取得"""
        return self.evaluation_history
