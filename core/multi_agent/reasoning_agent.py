from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid

from .agent_base import MultiAgentBase, AgentRole, AgentMessage
from ..coat_reasoner import COATReasoner

class ReasoningAgent(MultiAgentBase):
    """
    推論を担当するエージェント
    
    COATを使用した自己反省型の推論を行う
    """
    
    def __init__(
        self,
        agent_id: str = "reasoning_agent",
        name: str = "推論エージェント",
        description: str = "自己反省型の推論を行い、問題解決を支援する",
        llm=None
    ):
        """
        推論エージェントの初期化
        
        Args:
            agent_id: エージェントID
            name: エージェント名
            description: エージェントの説明
            llm: 使用するLLMインスタンス
        """
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.MAIN_REASONING,
            name=name,
            description=description,
            llm=llm
        )
        
        self.coat_reasoner = COATReasoner(llm) if llm else None
        self.reasoning_history = []
        
    def generate_reasoning_chain(
        self, 
        task_description: str,
        current_state: str = "",
        max_steps: int = 5
    ) -> Dict[str, Any]:
        """
        推論チェーンを生成
        
        Args:
            task_description: タスクの説明
            current_state: 現在の状態
            max_steps: 最大ステップ数
            
        Returns:
            生成された推論チェーンと最終解決策を含む辞書
        """
        if not self.coat_reasoner:
            return {"error": "COATReasonerが初期化されていません"}
            
        result = self.coat_reasoner.generate_action_thought_chain(
            task_description=task_description,
            current_state=current_state,
            max_steps=max_steps
        )
        
        self.reasoning_history.append({
            "task": task_description,
            "result": result,
            "timestamp": time.time()
        })
        
        return result
    
    def fix_code_with_reasoning(
        self,
        code: str,
        error_message: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        推論を使用してコードを修正
        
        Args:
            code: 修正対象のコード
            error_message: エラーメッセージ
            
        Returns:
            修正されたコードと推論チェーンのタプル
        """
        if not self.coat_reasoner:
            return code, []
            
        fixed_code, coat_chain = self.coat_reasoner.apply_coat_reasoning(
            code=code,
            error_message=error_message
        )
        
        return fixed_code, coat_chain
    
    def analyze_problem(self, problem_description: str) -> Dict[str, Any]:
        """
        問題を分析
        
        Args:
            problem_description: 問題の説明
            
        Returns:
            分析結果
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        prompt = f"""
        以下の問題を分析し、解決策を提案してください：
        
        {problem_description}
        
        以下の形式で回答してください：
        
        問題の理解: [問題の本質的な理解]
        課題: [解決すべき主要な課題]
        解決策: [提案する解決策]
        次のステップ: [実行すべき具体的なステップ]
        """
        
        analysis = self.llm.generate_text(prompt)
        
        result = {}
        
        for line in analysis.split('\n'):
            line = line.strip()
            if line.startswith("問題の理解:"):
                result["understanding"] = line[len("問題の理解:"):].strip()
            elif line.startswith("課題:"):
                result["challenges"] = line[len("課題:"):].strip()
            elif line.startswith("解決策:"):
                result["solution"] = line[len("解決策:"):].strip()
            elif line.startswith("次のステップ:"):
                result["next_steps"] = line[len("次のステップ:"):].strip()
        
        return result
    
    def generate_plan(self, goal: str, context: str = "") -> Dict[str, Any]:
        """
        目標達成のための計画を生成
        
        Args:
            goal: 達成する目標
            context: 追加コンテキスト
            
        Returns:
            生成された計画
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        prompt = f"""
        以下の目標を達成するための計画を作成してください：
        
        目標: {goal}
        
        コンテキスト:
        {context}
        
        以下の形式でJSON配列として返してください：
        {{
            "title": "計画のタイトル",
            "description": "計画の説明",
            "steps": [
                {{"id": 1, "name": "ステップ1", "description": "ステップ1の説明"}},
                {{"id": 2, "name": "ステップ2", "description": "ステップ2の説明"}}
            ]
        }}
        """
        
        plan_json = self.llm.generate_text(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', plan_json, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
                return plan
            else:
                return {"error": "計画のJSONパースに失敗しました"}
        except Exception as e:
            return {"error": f"計画の生成エラー: {str(e)}"}
    
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
            
            if task_type == "reasoning_chain":
                content = message.content
                task_description = content.get("task_description", "")
                current_state = content.get("current_state", "")
                max_steps = content.get("max_steps", 5)
                
                result = self.generate_reasoning_chain(
                    task_description=task_description,
                    current_state=current_state,
                    max_steps=max_steps
                )
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "fix_code":
                content = message.content
                code = content.get("code", "")
                error_message = content.get("error_message", "")
                
                fixed_code, coat_chain = self.fix_code_with_reasoning(
                    code=code,
                    error_message=error_message
                )
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content={
                        "fixed_code": fixed_code,
                        "reasoning_chain": coat_chain
                    },
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "analyze_problem":
                content = message.content
                problem_description = content.get("problem_description", "")
                
                analysis = self.analyze_problem(problem_description)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=analysis,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "analyze_task":
                content = message.content
                description = content.get("description", "")
                
                analysis_result = {}
                
                if self.llm:
                    prompt = f"""
                    以下のタスクを分析し、必要なツールと複雑さを評価してください：
                    
                    タスク: {description}
                    
                    以下の形式で回答してください：
                    
                    タスクタイプ: [web_search/code_generation/analysis/general]
                    複雑さ: [low/medium/high]
                    必要なツール: [ツールのリスト（例: web_crawler, python_execute）]
                    """
                    
                    analysis_text = self.llm.generate_text(prompt)
                    
                    for line in analysis_text.split('\n'):
                        line = line.strip()
                        if line.startswith("タスクタイプ:"):
                            analysis_result["task_type"] = line[len("タスクタイプ:"):].strip()
                        elif line.startswith("複雑さ:"):
                            analysis_result["complexity"] = line[len("複雑さ:"):].strip()
                        elif line.startswith("必要なツール:"):
                            tools_str = line[len("必要なツール:"):].strip()
                            analysis_result["required_tools"] = [t.strip() for t in tools_str.split(',')]
                else:
                    analysis_result = {
                        "task_type": "general",
                        "complexity": "medium",
                        "required_tools": ["python_execute"]
                    }
                    
                    if "検索" in description or "情報収集" in description or "調査" in description:
                        analysis_result["task_type"] = "web_search"
                        analysis_result["required_tools"] = ["web_crawler"]
                    elif "コード" in description or "プログラム" in description or "実装" in description:
                        analysis_result["task_type"] = "code_generation"
                        analysis_result["required_tools"] = ["python_execute"]
                    elif "分析" in description or "評価" in description or "検証" in description:
                        analysis_result["task_type"] = "analysis"
                        analysis_result["required_tools"] = ["python_execute"]
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=analysis_result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "generate_plan":
                content = message.content
                goal = content.get("goal", "")
                context = content.get("context", "")
                
                plan = self.generate_plan(goal, context)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=plan,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
        
        return responses
    
    def get_reasoning_history(self) -> List[Dict[str, Any]]:
        """推論履歴を取得"""
        return self.reasoning_history
