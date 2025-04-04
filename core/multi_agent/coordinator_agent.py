from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid

from .agent_base import MultiAgentBase, AgentRole, AgentMessage

class CoordinatorAgent(MultiAgentBase):
    """
    マルチエージェントシステムの調整を行うエージェント
    
    エージェント間の通信を管理し、タスクの割り当てと結果の集約を行う
    """
    
    def __init__(
        self,
        agent_id: str = "coordinator",
        name: str = "調整エージェント",
        description: str = "エージェント間の通信を管理し、タスクの割り当てと結果の集約を行う",
        llm=None
    ):
        """
        調整エージェントの初期化
        
        Args:
            agent_id: エージェントID
            name: エージェント名
            description: エージェントの説明
            llm: 使用するLLMインスタンス
        """
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.COORDINATOR,
            name=name,
            description=description,
            llm=llm
        )
        
        self.registered_agents = {}  # エージェントIDから情報へのマッピング
        self.active_tasks = {}  # タスクIDからタスク情報へのマッピング
        
    def register_agent(self, agent_id: str, role: AgentRole, name: str, description: str) -> bool:
        """
        エージェントを登録
        
        Args:
            agent_id: エージェントID
            role: エージェントの役割
            name: エージェント名
            description: エージェントの説明
            
        Returns:
            登録が成功したかどうか
        """
        if agent_id in self.registered_agents:
            return False
            
        self.registered_agents[agent_id] = {
            "role": role,
            "name": name,
            "description": description,
            "status": "active",
            "last_active": time.time()
        }
        
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        エージェントの登録を解除
        
        Args:
            agent_id: エージェントID
            
        Returns:
            登録解除が成功したかどうか
        """
        if agent_id not in self.registered_agents:
            return False
            
        del self.registered_agents[agent_id]
        return True
    
    def get_agents_by_role(self, role: AgentRole) -> List[str]:
        """
        指定された役割のエージェントIDを取得
        
        Args:
            role: エージェントの役割
            
        Returns:
            エージェントIDのリスト
        """
        return [
            agent_id for agent_id, info in self.registered_agents.items()
            if info["role"] == role and info["status"] == "active"
        ]
    
    def create_task(self, task_type: str, content: Any, target_agents: Optional[List[str]] = None) -> str:
        """
        新しいタスクを作成
        
        Args:
            task_type: タスクのタイプ
            content: タスクの内容
            target_agents: ターゲットエージェントのリスト（指定しない場合は適切なエージェントを自動選択）
            
        Returns:
            作成されたタスクのID
        """
        task_id = str(uuid.uuid4())
        
        if target_agents is None:
            if task_type == "reasoning":
                target_role = AgentRole.MAIN_REASONING
            elif task_type == "knowledge":
                target_role = AgentRole.KNOWLEDGE
            elif task_type == "evaluation":
                target_role = AgentRole.EVALUATION
            elif task_type == "domain_expert":
                target_role = AgentRole.DOMAIN_EXPERT
            elif task_type == "tool_execution":
                target_role = AgentRole.TOOL_EXECUTOR
            else:
                target_role = AgentRole.MAIN_REASONING
                
            target_agents = self.get_agents_by_role(target_role)
            
        self.active_tasks[task_id] = {
            "type": task_type,
            "content": content,
            "target_agents": target_agents,
            "status": "created",
            "created_at": time.time(),
            "updated_at": time.time(),
            "results": {}
        }
        
        for agent_id in target_agents:
            self.send_message(
                receiver_id=agent_id,
                content=content,
                message_type="task",
                metadata={
                    "task_id": task_id,
                    "task_type": task_type
                }
            )
        
        return task_id
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        タスクのステータスを更新
        
        Args:
            task_id: タスクID
            status: 新しいステータス
            
        Returns:
            更新が成功したかどうか
        """
        if task_id not in self.active_tasks:
            return False
            
        self.active_tasks[task_id]["status"] = status
        self.active_tasks[task_id]["updated_at"] = time.time()
        
        return True
    
    def add_task_result(self, task_id: str, agent_id: str, result: Any) -> bool:
        """
        タスク結果を追加
        
        Args:
            task_id: タスクID
            agent_id: 結果を提供したエージェントID
            result: タスク結果
            
        Returns:
            追加が成功したかどうか
        """
        if task_id not in self.active_tasks:
            return False
            
        self.active_tasks[task_id]["results"][agent_id] = {
            "result": result,
            "timestamp": time.time()
        }
        
        target_agents = set(self.active_tasks[task_id]["target_agents"])
        result_agents = set(self.active_tasks[task_id]["results"].keys())
        
        if target_agents.issubset(result_agents):
            self.update_task_status(task_id, "completed")
            
        return True
    
    def get_task_results(self, task_id: str) -> Dict[str, Any]:
        """
        タスク結果を取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスク結果の辞書
        """
        if task_id not in self.active_tasks:
            return {}
            
        return self.active_tasks[task_id]["results"]
    
    def _process_single_message(self, message: AgentMessage) -> List[AgentMessage]:
        """
        単一のメッセージを処理
        
        Args:
            message: 処理するメッセージ
            
        Returns:
            処理結果として生成されたメッセージのリスト
        """
        responses = []
        
        if message.message_type == "register":
            content = message.content
            success = self.register_agent(
                agent_id=message.sender_id,
                role=content.get("role"),
                name=content.get("name"),
                description=content.get("description")
            )
            
            response = self.send_message(
                receiver_id=message.sender_id,
                content={"success": success},
                message_type="register_response"
            )
            responses.append(response)
            
        elif message.message_type == "task_result":
            metadata = message.metadata or {}
            task_id = metadata.get("task_id")
            
            if task_id:
                success = self.add_task_result(
                    task_id=task_id,
                    agent_id=message.sender_id,
                    result=message.content
                )
                
                if success and self.active_tasks[task_id]["status"] == "completed":
                    requester_id = self.active_tasks[task_id].get("requester_id")
                    if requester_id:
                        notification = self.send_message(
                            receiver_id=requester_id,
                            content=self.get_task_results(task_id),
                            message_type="task_completed",
                            metadata={"task_id": task_id}
                        )
                        responses.append(notification)
        
        elif message.message_type == "heartbeat":
            if message.sender_id in self.registered_agents:
                self.registered_agents[message.sender_id]["last_active"] = time.time()
                self.registered_agents[message.sender_id]["status"] = "active"
        
        return responses
    
    def broadcast_message(self, content: Any, message_type: str = "broadcast", metadata: Optional[Dict[str, Any]] = None) -> List[AgentMessage]:
        """
        すべての登録済みエージェントにメッセージをブロードキャスト
        
        Args:
            content: メッセージ内容
            message_type: メッセージタイプ
            metadata: 追加メタデータ
            
        Returns:
            送信されたメッセージのリスト
        """
        messages = []
        
        for agent_id in self.registered_agents:
            message = self.send_message(
                receiver_id=agent_id,
                content=content,
                message_type=message_type,
                metadata=metadata
            )
            messages.append(message)
            
        return messages
    
    def check_agent_status(self):
        """
        エージェントのステータスをチェックし、非アクティブなエージェントを検出
        """
        current_time = time.time()
        timeout = 60  # 60秒間応答がないエージェントは非アクティブとみなす
        
        for agent_id, info in self.registered_agents.items():
            if current_time - info["last_active"] > timeout:
                self.registered_agents[agent_id]["status"] = "inactive"
