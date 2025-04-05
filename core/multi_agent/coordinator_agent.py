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
    
    def create_task(self, task_type: str, content: Any, target_agents: Optional[List[str]] = None, requester_id: Optional[str] = None) -> str:
        """
        新しいタスクを作成
        
        Args:
            task_type: タスクのタイプ
            content: タスクの内容
            target_agents: ターゲットエージェントのリスト（指定しない場合は適切なエージェントを自動選択）
            requester_id: タスクを要求したエージェントのID
            
        Returns:
            作成されたタスクのID
        """
        task_id = str(uuid.uuid4())
        
        print(f"新しいタスクを作成: タイプ={task_type}, 要求者={requester_id}")
        
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
            elif task_type == "generate_plan":
                target_role = AgentRole.COORDINATOR
            else:
                target_role = AgentRole.MAIN_REASONING
                
            target_agents = self.get_agents_by_role(target_role)
            print(f"役割 {target_role} に基づいてターゲットエージェントを選択: {target_agents}")
            
        if len(target_agents) == 1 and target_agents[0] == self.agent_id:
            print(f"コーディネーター自身がターゲットです。タスク '{task_id}' を直接処理します。")
            
            self.active_tasks[task_id] = {
                "type": task_type,
                "content": content,
                "target_agents": target_agents,
                "status": "processing",  # 直接「処理中」に設定
                "created_at": time.time(),
                "updated_at": time.time(),
                "results": {},
                "requester_id": requester_id
            }
            
            self.receive_message(AgentMessage(
                sender_id=self.agent_id,
                receiver_id=self.agent_id,
                content=content,
                message_type="task",
                metadata={
                    "task_id": task_id,
                    "task_type": task_type
                }
            ))
        else:
            self.active_tasks[task_id] = {
                "type": task_type,
                "content": content,
                "target_agents": target_agents,
                "status": "created",
                "created_at": time.time(),
                "updated_at": time.time(),
                "results": {},
                "requester_id": requester_id
            }
            
            print(f"タスク '{task_id}' を作成しました。ターゲットエージェント: {target_agents}")
            
            for agent_id in target_agents:
                print(f"タスクメッセージを '{agent_id}' に送信します")
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
            print(f"警告: タスク '{task_id}' が見つかりません。結果を追加できません。")
            return False
            
        print(f"タスク '{task_id}' に結果を追加: エージェント={agent_id}")
        self.active_tasks[task_id]["results"][agent_id] = {
            "result": result,
            "timestamp": time.time()
        }
        
        target_agents = set(self.active_tasks[task_id]["target_agents"])
        result_agents = set(self.active_tasks[task_id]["results"].keys())
        
        print(f"タスク '{task_id}' - ターゲットエージェント: {target_agents}")
        print(f"タスク '{task_id}' - 結果を提供したエージェント: {result_agents}")
        
        if target_agents.issubset(result_agents):
            print(f"すべてのターゲットエージェントから結果を受け取りました。タスク '{task_id}' を完了としてマークします。")
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
        
        print(f"コーディネーターがメッセージを処理: タイプ={message.message_type}, 送信者={message.sender_id}")
        
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
                print(f"タスク結果を受信: タスクID={task_id}, 送信者={message.sender_id}")
                success = self.add_task_result(
                    task_id=task_id,
                    agent_id=message.sender_id,
                    result=message.content
                )
                
                if success:
                    print(f"タスク '{task_id}' の結果が正常に追加されました")
                    
                    if task_id in self.active_tasks:
                        task_status = self.active_tasks[task_id]["status"]
                        print(f"タスク '{task_id}' の現在の状態: {task_status}")
                        
                        target_agents = set(self.active_tasks[task_id]["target_agents"])
                        result_agents = set(self.active_tasks[task_id]["results"].keys())
                        
                        print(f"ターゲットエージェント: {target_agents}")
                        print(f"結果を提供したエージェント: {result_agents}")
                        
                        if target_agents.issubset(result_agents) and task_status != "completed":
                            print(f"すべてのエージェントから結果を受け取りました。タスク '{task_id}' を完了としてマークします。")
                            self.update_task_status(task_id, "completed")
                
                if task_id in self.active_tasks and self.active_tasks[task_id]["status"] == "completed":
                    requester_id = self.active_tasks[task_id].get("requester_id")
                    if requester_id:
                        print(f"タスク '{task_id}' の完了を通知: 要求者={requester_id}")
                        notification = self.send_message(
                            receiver_id=requester_id,
                            content=self.get_task_results(task_id),
                            message_type="task_completed",
                            metadata={"task_id": task_id}
                        )
                        responses.append(notification)
        
        elif message.message_type == "task":
            metadata = message.metadata or {}
            task_id = metadata.get("task_id")
            task_type = metadata.get("task_type")
            
            print(f"タスクメッセージを受信: タスクID={task_id}, タイプ={task_type}")
            
            if task_id and task_id in self.active_tasks:
                print(f"コーディネーターがタスク '{task_id}' を処理中... タイプ: {task_type}")
                self.update_task_status(task_id, "processing")
            
            if task_id and task_type == "generate_plan":
                print(f"計画生成タスク '{task_id}' の処理を開始")
                plan_result = self._handle_generate_plan_task(message.content)
                
                print(f"計画生成タスク '{task_id}' の結果を追加")
                self.add_task_result(
                    task_id=task_id,
                    agent_id=self.agent_id,
                    result=plan_result
                )
                
                if task_id in self.active_tasks:
                    print(f"計画生成タスク '{task_id}' を完了としてマークします")
                    self.update_task_status(task_id, "completed")
                    
                    requester_id = self.active_tasks[task_id].get("requester_id")
                    if requester_id:
                        print(f"計画生成タスク '{task_id}' の完了を通知: {requester_id}")
                        notification = self.send_message(
                            receiver_id=requester_id,
                            content=plan_result,
                            message_type="task_completed",
                            metadata={"task_id": task_id}
                        )
                        responses.append(notification)
        
        elif message.message_type == "heartbeat":
            if message.sender_id in self.registered_agents:
                self.registered_agents[message.sender_id]["last_active"] = time.time()
                self.registered_agents[message.sender_id]["status"] = "active"
        
        return responses
        
    def _handle_generate_plan_task(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        計画生成タスクを処理
        
        Args:
            content: タスク内容
            
        Returns:
            計画生成結果
        """
        goal = content.get("goal", "")
        max_tasks = content.get("max_tasks", 5)
        
        if not goal:
            return {
                "success": False,
                "error": "目標が指定されていません"
            }
            
        try:
            plan_id = f"plan_{int(time.time())}"
            
            if self.llm:
                plan_prompt = f"""
                目標: {goal}
                
                この目標を達成するための計画を作成してください。
                計画は最大{max_tasks}個のタスクに分割し、各タスクには以下の情報を含めてください:
                
                1. タスクの説明
                2. 依存関係（他のタスクIDがある場合）
                
                JSON形式で出力してください。
                """
                
                plan_response = self.llm.generate(plan_prompt)
                
                try:
                    import re
                    json_match = re.search(r'```json\n(.*?)\n```', plan_response, re.DOTALL)
                    
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = plan_response
                        
                    plan_data = json.loads(json_str)
                    
                    tasks = []
                    for i, task in enumerate(plan_data.get("tasks", [])):
                        task_id = f"task_{i+1}"
                        tasks.append({
                            "id": task_id,
                            "description": task.get("description", ""),
                            "dependencies": task.get("dependencies", [])
                        })
                    
                    return {
                        "success": True,
                        "plan_id": plan_id,
                        "tasks": tasks
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"計画データの解析に失敗しました: {str(e)}"
                    }
            else:
                return {
                    "success": True,
                    "plan_id": plan_id,
                    "tasks": [
                        {
                            "id": "task_1",
                            "description": f"{goal}に関する情報を収集する",
                            "dependencies": []
                        },
                        {
                            "id": "task_2",
                            "description": f"収集した情報を分析する",
                            "dependencies": ["task_1"]
                        },
                        {
                            "id": "task_3",
                            "description": f"分析結果をまとめる",
                            "dependencies": ["task_2"]
                        }
                    ]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"計画生成中にエラーが発生しました: {str(e)}"
            }
    
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
