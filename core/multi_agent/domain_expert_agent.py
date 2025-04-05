from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid

from .agent_base import MultiAgentBase, AgentRole, AgentMessage

class DomainExpertAgent(MultiAgentBase):
    """
    特定のドメインに関する専門知識を提供するエージェント
    
    特定の分野に特化した知識と推論能力を持つ
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        domain: str,
        llm=None,
        knowledge_base: Optional[Dict[str, Any]] = None
    ):
        """
        ドメイン専門家エージェントの初期化
        
        Args:
            agent_id: エージェントID
            name: エージェント名
            description: エージェントの説明
            domain: 専門分野
            llm: 使用するLLMインスタンス
            knowledge_base: 初期知識ベース
        """
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.DOMAIN_EXPERT,
            name=name,
            description=description,
            llm=llm
        )
        
        self.domain = domain
        self.knowledge_base = knowledge_base or {}
        self.consultation_history = []
    
    def provide_expertise(self, query: str) -> Dict[str, Any]:
        """
        専門知識を提供
        
        Args:
            query: 質問内容
            
        Returns:
            専門家の回答
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        prompt = f"""
        あなたは{self.domain}の専門家として以下の質問に回答してください：
        
        質問: {query}
        
        あなたの専門知識に基づいて、詳細かつ正確な回答を提供してください。
        不確かな情報には言及せず、確実な情報のみを提供してください。
        """
        
        response = self.llm.generate_text(prompt)
        
        consultation = {
            "query": query,
            "response": response,
            "timestamp": time.time()
        }
        
        self.consultation_history.append(consultation)
        
        return {
            "domain": self.domain,
            "query": query,
            "response": response
        }
    
    def evaluate_statement(self, statement: str) -> Dict[str, Any]:
        """
        専門分野に関する記述を評価
        
        Args:
            statement: 評価する記述
            
        Returns:
            評価結果
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        prompt = f"""
        あなたは{self.domain}の専門家として以下の記述を評価してください：
        
        記述: {statement}
        
        以下の形式で回答してください：
        
        正確性: [1-10の数値で評価]
        コメント: [評価に関するコメント]
        修正案: [必要に応じて修正案を提示]
        """
        
        evaluation = self.llm.generate_text(prompt)
        
        result = {}
        
        for line in evaluation.split('\n'):
            line = line.strip()
            if line.startswith("正確性:"):
                try:
                    accuracy = int(line[len("正確性:"):].strip().split()[0])
                    result["accuracy"] = min(max(accuracy, 1), 10)  # 1-10の範囲に制限
                except:
                    result["accuracy"] = 0
            elif line.startswith("コメント:"):
                result["comment"] = line[len("コメント:"):].strip()
            elif line.startswith("修正案:"):
                result["correction"] = line[len("修正案:"):].strip()
        
        return result
    
    def suggest_improvements(self, content: str) -> Dict[str, Any]:
        """
        専門分野に関する内容の改善案を提案
        
        Args:
            content: 改善する内容
            
        Returns:
            改善案
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        prompt = f"""
        あなたは{self.domain}の専門家として以下の内容の改善案を提案してください：
        
        内容:
        {content}
        
        専門的な観点から、この内容をより正確で効果的にするための改善案を提案してください。
        """
        
        suggestions = self.llm.generate_text(prompt)
        
        return {
            "domain": self.domain,
            "original_content": content,
            "suggestions": suggestions
        }
    
    def add_to_knowledge_base(self, key: str, value: Any) -> bool:
        """
        知識ベースに情報を追加
        
        Args:
            key: キー
            value: 値
            
        Returns:
            追加が成功したかどうか
        """
        self.knowledge_base[key] = value
        return True
    
    def get_from_knowledge_base(self, key: str) -> Any:
        """
        知識ベースから情報を取得
        
        Args:
            key: キー
            
        Returns:
            取得した値
        """
        return self.knowledge_base.get(key)
    
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
            
            if task_type == "provide_expertise":
                content = message.content
                query = content.get("query", "")
                
                result = self.provide_expertise(query)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "evaluate_statement":
                content = message.content
                statement = content.get("statement", "")
                
                result = self.evaluate_statement(statement)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "suggest_improvements":
                content = message.content
                content_to_improve = content.get("content", "")
                
                result = self.suggest_improvements(content_to_improve)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
        
        return responses
    
    def get_consultation_history(self) -> List[Dict[str, Any]]:
        """相談履歴を取得"""
        return self.consultation_history
