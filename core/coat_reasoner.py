from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time

class COATReasoner:
    """
    COAT（Chain of Adaptive Thought）推論機能
    
    自己反省型の思考チェーンを生成し、問題解決を行う
    """
    
    def __init__(self, llm):
        """
        COATReasonerの初期化
        
        Args:
            llm: 使用するLLMインスタンス
        """
        self.llm = llm
        self.reasoning_history = []
    
    def generate_action_thought_chain(
        self, 
        task_description: str,
        current_state: str = "",
        max_steps: int = 5
    ) -> Dict[str, Any]:
        """
        行動と思考のチェーンを生成
        
        Args:
            task_description: タスクの説明
            current_state: 現在の状態（オプション）
            max_steps: 最大ステップ数
            
        Returns:
            生成されたCOATチェーンと最終解決策を含む辞書
        """
        coat_chain = []
        
        prompt_template = """
        {task_description}
        
        {current_state}
        
        {previous_steps}
        
        次のステップとして、以下の形式で回答してください：
        
        思考: [問題についての思考プロセス]
        行動: [取るべき具体的な行動]
        予測: [その行動の結果として何が起こるかの予測]
        """
        
        for step in range(max_steps):
            previous_steps = ""
            for i, prev_step in enumerate(coat_chain):
                previous_steps += f"ステップ {i+1}:\n"
                previous_steps += f"思考: {prev_step.get('thought', '')}\n"
                previous_steps += f"行動: {prev_step.get('action', '')}\n"
                previous_steps += f"予測: {prev_step.get('prediction', '')}\n\n"
            
            prompt = prompt_template.format(
                task_description=task_description,
                current_state=current_state,
                previous_steps=previous_steps
            )
            
            response = self.llm.generate_text(prompt)
            
            thought = ""
            action = ""
            prediction = ""
            
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith("思考:"):
                    thought = line[len("思考:"):].strip()
                elif line.startswith("行動:"):
                    action = line[len("行動:"):].strip()
                elif line.startswith("予測:"):
                    prediction = line[len("予測:"):].strip()
            
            step_data = {
                "step": step + 1,
                "thought": thought,
                "action": action,
                "prediction": prediction,
                "timestamp": time.time()
            }
            
            coat_chain.append(step_data)
            
            if "解決" in action.lower() or "完了" in action.lower() or "終了" in action.lower():
                break
        
        final_solution_prompt = f"""
        {task_description}
        
        {previous_steps}
        
        上記の思考チェーンに基づいて、最終的な解決策や結論を簡潔にまとめてください。
        """
        
        final_solution = self.llm.generate_text(final_solution_prompt)
        
        result = {
            "coat_chain": coat_chain,
            "final_solution": final_solution
        }
        
        self.reasoning_history.append({
            "task": task_description,
            "result": result,
            "timestamp": time.time()
        })
        
        return result
    
    def apply_coat_reasoning(
        self,
        code: str,
        error_message: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        コードエラーに対してCOAT推論を適用
        
        Args:
            code: 修正対象のコード
            error_message: エラーメッセージ
            
        Returns:
            修正されたコードとCOATチェーンのタプル
        """
        task_description = f"""
        以下のPythonコードにエラーがあります。エラーを修正してください。
        
        ```python
        {code}
        ```
        
        エラーメッセージ:
        ```
        {error_message}
        ```
        
        エラーを分析し、修正したコードを提供してください。
        """
        
        coat_result = self.generate_action_thought_chain(
            task_description=task_description,
            max_steps=3
        )
        
        coat_chain = coat_result.get("coat_chain", [])
        final_solution = coat_result.get("final_solution", "")
        
        import re
        code_match = re.search(r'```python\s*(.*?)\s*```', final_solution, re.DOTALL)
        
        if code_match:
            fixed_code = code_match.group(1).strip()
        else:
            fixed_code = final_solution.strip()
            
            if not fixed_code or len(fixed_code) < 10:  # 短すぎる場合は無視
                fixed_code = code
        
        return fixed_code, coat_chain
    
    def get_reasoning_history(self) -> List[Dict[str, Any]]:
        """推論履歴を取得"""
        return self.reasoning_history
