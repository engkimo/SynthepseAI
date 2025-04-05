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
                        elif len(result_agents) > 0 and task_status == "processing" and time.time() - self.active_tasks[task_id].get("updated_at", 0) > 10:
                            print(f"タスク '{task_id}' は長時間処理中のままですが、少なくとも1つの結果があります。完了としてマークします。")
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
                
                if task_type == "generate_plan":
                    self._process_generate_plan_task(task_id, message, responses)
                elif task_type == "execute_task":
                    self._process_execute_task(task_id, message, responses)
                elif task_type == "analyze_task":
                    self._process_analyze_task(task_id, message, responses)
                elif task_type == "generate_summary":
                    self._process_generate_summary_task(task_id, message, responses)
                else:
                    print(f"警告: 未知のタスクタイプ '{task_type}' です")
                    self.add_task_result(
                        task_id=task_id,
                        agent_id=self.agent_id,
                        result={
                            "success": False,
                            "error": f"未知のタスクタイプ: {task_type}"
                        }
                    )
                    self.update_task_status(task_id, "completed")
            else:
                print(f"警告: タスク '{task_id}' が見つからないか、IDが指定されていません")
        
        elif message.message_type == "heartbeat":
            if message.sender_id in self.registered_agents:
                self.registered_agents[message.sender_id]["last_active"] = time.time()
                self.registered_agents[message.sender_id]["status"] = "active"
        
        return responses
        
    def _process_generate_plan_task(self, task_id: str, message: AgentMessage, responses: List[AgentMessage]):
        """
        計画生成タスクを処理
        
        Args:
            task_id: タスクID
            message: 受信したメッセージ
            responses: 応答メッセージのリスト
        """
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
                
    def _process_execute_task(self, task_id: str, message: AgentMessage, responses: List[AgentMessage]):
        """
        タスク実行処理
        
        Args:
            task_id: タスクID
            message: 受信したメッセージ
            responses: 応答メッセージのリスト
        """
        print(f"タスク実行 '{task_id}' の処理")
        content = message.content
        
        self.add_task_result(
            task_id=task_id,
            agent_id=self.agent_id,
            result={
                "success": True,
                "message": "タスク実行が完了しました",
                "task_id": content.get("task_id", ""),
                "description": content.get("description", "")
            }
        )
        
        self.update_task_status(task_id, "completed")
        
        requester_id = self.active_tasks[task_id].get("requester_id")
        if requester_id:
            notification = self.send_message(
                receiver_id=requester_id,
                content=self.get_task_results(task_id),
                message_type="task_completed",
                metadata={"task_id": task_id}
            )
            responses.append(notification)
            
    def _process_analyze_task(self, task_id: str, message: AgentMessage, responses: List[AgentMessage]):
        """
        タスク分析処理
        
        Args:
            task_id: タスクID
            message: 受信したメッセージ
            responses: 応答メッセージのリスト
        """
        print(f"タスク分析 '{task_id}' の処理")
        content = message.content
        description = content.get("description", "")
        
        reasoning_agents = self.get_agents_by_role(AgentRole.MAIN_REASONING)
        
        if not reasoning_agents:
            print(f"警告: 推論エージェントが見つかりません。コーディネーターが直接タスクを処理します。")
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
            
            self.add_task_result(
                task_id=task_id,
                agent_id=self.agent_id,
                result=analysis_result
            )
            
            self.update_task_status(task_id, "completed")
            
            requester_id = self.active_tasks[task_id].get("requester_id")
            if requester_id:
                notification = self.send_message(
                    receiver_id=requester_id,
                    content=analysis_result,
                    message_type="task_completed",
                    metadata={"task_id": task_id}
                )
                responses.append(notification)
        else:
            reasoning_agent_id = reasoning_agents[0]
            print(f"タスク分析を推論エージェント '{reasoning_agent_id}' に委譲します")
            
            self.active_tasks[task_id]["target_agents"] = [reasoning_agent_id]
            
            task_message = self.send_message(
                receiver_id=reasoning_agent_id,
                content={"description": description},
                message_type="task",
                metadata={
                    "task_id": task_id,
                    "task_type": "analyze_task"
                }
            )
            responses.append(task_message)
            
            self.update_task_status(task_id, "processing")
            
    def _process_generate_summary_task(self, task_id: str, message: AgentMessage, responses: List[AgentMessage]):
        """
        要約生成処理
        
        Args:
            task_id: タスクID
            message: 受信したメッセージ
            responses: 応答メッセージのリスト
        """
        print(f"要約生成 '{task_id}' の処理")
        content = message.content
        
        plan_id = content.get("plan_id", "")
        completed_tasks = content.get("completed_tasks", 0)
        failed_tasks = content.get("failed_tasks", 0)
        task_results = content.get("task_results", [])
        
        summary = f"""
        実行結果サマリー:
        
        計画ID: {plan_id}
        完了タスク: {completed_tasks}
        失敗タスク: {failed_tasks}
        
        タスク詳細:
        """
        
        for task in task_results:
            task_id_in_result = task.get("id", "")
            description = task.get("description", "")
            status = task.get("status", "")
            
            summary += f"\n- タスク {task_id_in_result}: {description} ({status})"
        
        # タスク結果を追加
        self.add_task_result(
            task_id=task_id,
            agent_id=self.agent_id,
            result={
                "success": True,
                "summary": summary
            }
        )
        
        self.update_task_status(task_id, "completed")
        
        if task_id in self.active_tasks:
            requester_id = self.active_tasks[task_id].get("requester_id")
            if requester_id:
                notification = self.send_message(
                    receiver_id=requester_id,
                    content={"summary": summary},
                    message_type="task_completed",
                    metadata={"task_id": task_id}
                )
                responses.append(notification)
        else:
            print(f"警告: タスク '{task_id}' が見つかりません。結果通知をスキップします。")
        
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
                        "result": {
                            "plan_id": plan_id,
                            "tasks": tasks
                        }
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"計画データの解析に失敗しました: {str(e)}",
                        "result": {
                            "plan_id": plan_id,
                            "tasks": []
                        }
                    }
            else:
                mock_tasks = [
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
                
                if "ソフトバンク" in goal or "SoftBank" in goal:
                    if "クリスタルインテリジェンス" in goal or "Crystal Intelligence" in goal:
                        mock_tasks = [
                            {
                                "id": "task_1",
                                "description": "ソフトバンクのクリスタルインテリジェンスに関する基本情報を収集する",
                                "dependencies": []
                            },
                            {
                                "id": "task_2",
                                "description": "クリスタルインテリジェンスの技術的特徴と革新性を分析する",
                                "dependencies": ["task_1"]
                            },
                            {
                                "id": "task_3",
                                "description": "クリスタルインテリジェンスの市場における位置づけと競合技術を調査する",
                                "dependencies": ["task_1"]
                            },
                            {
                                "id": "task_4",
                                "description": "クリスタルインテリジェンスの将来的な発展方向と可能性を予測する",
                                "dependencies": ["task_2", "task_3"]
                            },
                            {
                                "id": "task_5",
                                "description": "クリスタルインテリジェンスがAI業界全体に与える影響を考察する",
                                "dependencies": ["task_4"]
                            }
                        ]
                    else:
                        mock_tasks.append({
                            "id": "task_4",
                            "description": "ソフトバンクの最新の技術投資動向を調査する",
                            "dependencies": ["task_1"]
                        })
                        mock_tasks.append({
                            "id": "task_5",
                            "description": "ソフトバンクの技術戦略と将来展望を分析する",
                            "dependencies": ["task_2"]
                        })
                elif "財務省" in goal or "Ministry of Finance" in goal:
                    mock_tasks.append({
                        "id": "task_4",
                        "description": "財務省の最近の政策動向を調査する",
                        "dependencies": ["task_1"]
                    })
                    mock_tasks.append({
                        "id": "task_5",
                        "description": "デモの背景となる経済状況を分析する",
                        "dependencies": ["task_2"]
                    })
                
                print(f"モックモード: {len(mock_tasks)}個のタスクを生成しました")
                
                return {
                    "success": True,
                    "result": {
                        "plan_id": plan_id,
                        "tasks": mock_tasks
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"計画生成中にエラーが発生しました: {str(e)}",
                "result": {
                    "plan_id": f"plan_{int(time.time())}",
                    "tasks": []
                }
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
