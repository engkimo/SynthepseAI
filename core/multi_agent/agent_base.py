from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid
from enum import Enum

class AgentRole(Enum):
    """
    マルチエージェントシステムにおける各エージェントの役割
    """
    MAIN_REASONING = "main_reasoning"  # メイン推論エージェント
    KNOWLEDGE = "knowledge"  # 知識管理エージェント
    EVALUATION = "evaluation"  # 評価エージェント
    DOMAIN_EXPERT = "domain_expert"  # ドメイン専門家エージェント
    TOOL_EXECUTOR = "tool_executor"  # ツール実行エージェント
    COORDINATOR = "coordinator"  # 調整エージェント

class AgentMessage:
    """
    エージェント間のメッセージ
    """
    def __init__(
        self,
        sender_id: str,
        receiver_id: str,
        content: Any,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        エージェントメッセージの初期化
        
        Args:
            sender_id: 送信者ID
            receiver_id: 受信者ID
            content: メッセージ内容
            message_type: メッセージタイプ（"text", "command", "result", "error"など）
            metadata: 追加メタデータ
        """
        self.id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.message_type = message_type
        self.metadata = metadata or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """メッセージを辞書に変換"""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "message_type": self.message_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """辞書からメッセージを作成"""
        message = cls(
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            content=data["content"],
            message_type=data.get("message_type", "text"),
            metadata=data.get("metadata", {})
        )
        message.id = data.get("id", message.id)
        message.timestamp = data.get("timestamp", message.timestamp)
        return message

class MultiAgentBase:
    """
    マルチエージェントシステムの基底クラス
    """
    
    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        name: str,
        description: str,
        llm=None
    ):
        """
        マルチエージェントの初期化
        
        Args:
            agent_id: エージェントID
            role: エージェントの役割
            name: エージェント名
            description: エージェントの説明
            llm: 使用するLLMインスタンス
        """
        self.agent_id = agent_id
        self.role = role
        self.name = name
        self.description = description
        self.llm = llm
        
        self.message_queue = []
        self.message_history = []
        self.state = {}
        
    def receive_message(self, message: AgentMessage) -> bool:
        """
        メッセージを受信
        
        Args:
            message: 受信するメッセージ
            
        Returns:
            メッセージが正常に受信されたかどうか
        """
        if message.receiver_id != self.agent_id and message.receiver_id != "broadcast":
            return False
            
        self.message_queue.append(message)
        self.message_history.append(message)
        return True
    
    def send_message(self, receiver_id: str, content: Any, message_type: str = "text", metadata: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """
        メッセージを送信
        
        Args:
            receiver_id: 受信者ID
            content: メッセージ内容
            message_type: メッセージタイプ
            metadata: 追加メタデータ
            
        Returns:
            送信されたメッセージ
        """
        message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            metadata=metadata
        )
        
        self.message_history.append(message)
        return message
    
    def process_messages(self) -> List[AgentMessage]:
        """
        キューにあるメッセージを処理
        
        Returns:
            処理結果として生成されたメッセージのリスト
        """
        responses = []
        
        while self.message_queue:
            message = self.message_queue.pop(0)
            response = self._process_single_message(message)
            if response:
                responses.extend(response)
                
        return responses
    
    def _process_single_message(self, message: AgentMessage) -> List[AgentMessage]:
        """
        単一のメッセージを処理
        
        Args:
            message: 処理するメッセージ
            
        Returns:
            処理結果として生成されたメッセージのリスト
        """
        return []
    
    def get_state(self) -> Dict[str, Any]:
        """
        現在の状態を取得
        
        Returns:
            エージェントの状態
        """
        return self.state
    
    def update_state(self, updates: Dict[str, Any]):
        """
        状態を更新
        
        Args:
            updates: 更新内容
        """
        self.state.update(updates)
    
    def get_message_history(self) -> List[Dict[str, Any]]:
        """
        メッセージ履歴を取得
        
        Returns:
            メッセージ履歴の辞書リスト
        """
        return [message.to_dict() for message in self.message_history]
    
    def clear_message_queue(self):
        """メッセージキューをクリア"""
        self.message_queue = []
