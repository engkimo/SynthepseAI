from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid
import os

from .agent_base import MultiAgentBase, AgentRole, AgentMessage
from .coordinator_agent import CoordinatorAgent
from .knowledge_agent import KnowledgeAgent
from .reasoning_agent import ReasoningAgent
from .tool_executor_agent import ToolExecutorAgent
from .domain_expert_agent import DomainExpertAgent
from .evaluation_agent import EvaluationAgent

class MultiAgentSystem:
    """
    マルチエージェントシステム
    
    複数のエージェントを管理し、協調動作させる
    """
    
    def __init__(
        self,
        llm=None,
        device: Optional[str] = None,
        knowledge_db_path: str = "./knowledge_db.json",
        graph_path: str = "./knowledge_graph.json",
        tavily_api_key: Optional[str] = None,
        firecrawl_api_key: Optional[str] = None,
        use_compatibility_mode: bool = False,
        config: Optional[Dict[str, Any]] = None,
        rome_editor=None,
        coat_reasoner=None,
        rgcn_processor=None
    ):
        """
        マルチエージェントシステムの初期化
        
        Args:
            llm: 使用するLLMインスタンス
            device: 使用するデバイス（'cuda', 'mps', 'cpu'）
            knowledge_db_path: 知識データベースのパス
            graph_path: 知識グラフのパス
            tavily_api_key: TavilyのAPIキー
            firecrawl_api_key: FirecrawlのAPIキー
            use_compatibility_mode: 互換モードを使用するかどうか
            config: 追加設定情報
            rome_editor: ROMEモデルエディタ
            coat_reasoner: COAT推論機能
            rgcn_processor: R-GCNプロセッサ
        """
        self.agents = {}
        self.coordinator = None  # 初期化時はNone、_initialize_agentsで設定
        self.llm = llm
        self.device = device
        self.knowledge_db_path = knowledge_db_path
        self.graph_path = graph_path
        self.tavily_api_key = tavily_api_key
        self.firecrawl_api_key = firecrawl_api_key
        self.use_compatibility_mode = use_compatibility_mode
        self.config = config or {}
        self.rome_editor = rome_editor
        self.coat_reasoner = coat_reasoner
        self.rgcn_processor = rgcn_processor
        
        self._initialize_agents()
        
        if self.coordinator is None:
            raise ValueError("調整エージェントの初期化に失敗しました")
    
    def _initialize_agents(self):
        """エージェントを初期化"""
        self.config = self.config or {}
        
        mock_mode = self.config.get("mock_mode", False)
        if mock_mode:
            print("マルチエージェントシステムはモックモードで動作中です")
        
        coordinator = CoordinatorAgent(llm=self.llm)
        self.coordinator = coordinator
        self.agents[coordinator.agent_id] = coordinator
        
        knowledge_agent = KnowledgeAgent(
            llm=self.llm,
            device=self.device,
            knowledge_db_path=self.knowledge_db_path,
            graph_path=self.graph_path,
            use_compatibility_mode=self.use_compatibility_mode
        )
        self.agents[knowledge_agent.agent_id] = knowledge_agent
        
        reasoning_agent = ReasoningAgent(llm=self.llm)
        self.agents[reasoning_agent.agent_id] = reasoning_agent
        
        tool_config = {
            "use_web_tools": (self.tavily_api_key is not None or self.firecrawl_api_key is not None) and not mock_mode,
            "mock_mode": mock_mode
        }
        
        tool_executor_agent = ToolExecutorAgent(
            llm=self.llm,
            config=tool_config
        )
        self.agents[tool_executor_agent.agent_id] = tool_executor_agent
        
        evaluation_agent = EvaluationAgent(llm=self.llm)
        self.agents[evaluation_agent.agent_id] = evaluation_agent
        
        for agent_id, agent in self.agents.items():
            if agent_id != coordinator.agent_id:
                coordinator.register_agent(
                    agent_id=agent.agent_id,
                    role=agent.role,
                    name=agent.name,
                    description=agent.description
                )
    
    def add_domain_expert(self, domain: str, name: Optional[str] = None, description: Optional[str] = None) -> str:
        """
        ドメイン専門家エージェントを追加
        
        Args:
            domain: 専門分野
            name: エージェント名（指定しない場合は自動生成）
            description: エージェントの説明（指定しない場合は自動生成）
            
        Returns:
            追加されたエージェントのID
        """
        if self.coordinator is None:
            raise ValueError("調整エージェントが初期化されていません")
            
        agent_id = f"domain_expert_{domain}_{str(uuid.uuid4())[:8]}"
        name = name or f"{domain}専門家"
        description = description or f"{domain}に関する専門知識を提供する"
        
        domain_expert = DomainExpertAgent(
            agent_id=agent_id,
            name=name,
            description=description,
            domain=domain,
            llm=self.llm
        )
        
        self.agents[agent_id] = domain_expert
        
        self.coordinator.register_agent(
            agent_id=domain_expert.agent_id,
            role=domain_expert.role,
            name=domain_expert.name,
            description=domain_expert.description
        )
        
        return agent_id
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        エージェントを削除
        
        Args:
            agent_id: 削除するエージェントのID
            
        Returns:
            削除が成功したかどうか
        """
        if self.coordinator is None:
            raise ValueError("調整エージェントが初期化されていません")
            
        if agent_id not in self.agents:
            return False
            
        if agent_id == self.coordinator.agent_id:
            return False  # 調整エージェントは削除できない
            
        self.coordinator.unregister_agent(agent_id)
        del self.agents[agent_id]
        
        return True
    
    def send_message(self, sender_id: str, receiver_id: str, content: Any, message_type: str = "text", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        メッセージを送信
        
        Args:
            sender_id: 送信者ID
            receiver_id: 受信者ID
            content: メッセージ内容
            message_type: メッセージタイプ
            metadata: 追加メタデータ
            
        Returns:
            送信が成功したかどうか
        """
        if sender_id not in self.agents and sender_id != "system":
            print(f"警告: 送信者 '{sender_id}' が見つかりません")
            print(f"利用可能なエージェント: {list(self.agents.keys())}")
            return False
            
        if receiver_id not in self.agents and receiver_id != "broadcast":
            print(f"警告: 受信者 '{receiver_id}' が見つかりません")
            print(f"利用可能なエージェント: {list(self.agents.keys())}")
            return False
            
        print(f"メッセージを送信: {sender_id} -> {receiver_id}, タイプ={message_type}")
        
        if sender_id == "system":
            from .agent_base import AgentMessage
            message = AgentMessage(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                message_type=message_type,
                metadata=metadata
            )
        else:
            sender = self.agents[sender_id]
            message = sender.send_message(
                receiver_id=receiver_id,
                content=content,
                message_type=message_type,
                metadata=metadata
            )
        
        if receiver_id == "broadcast":
            success_count = 0
            for agent_id, agent in self.agents.items():
                if agent_id != sender_id or sender_id == "system":
                    if agent.receive_message(message):
                        success_count += 1
            print(f"ブロードキャストメッセージが {success_count} 件のエージェントに送信されました")
            return success_count > 0
        else:
            receiver = self.agents[receiver_id]
            result = receiver.receive_message(message)
            if result:
                print(f"メッセージが '{receiver_id}' に正常に送信されました")
            else:
                print(f"メッセージの '{receiver_id}' への送信に失敗しました")
            return result
    
    def process_messages(self) -> Dict[str, List[AgentMessage]]:
        """
        すべてのエージェントのメッセージを処理
        
        Returns:
            エージェントIDから処理結果のメッセージリストへのマッピング
        """
        results = {}
        total_processed = 0
        
        if isinstance(self.agents, dict):
            for agent_id, agent in self.agents.items():
                queue_size = len(agent.message_queue)
                if queue_size > 0:
                    print(f"エージェント '{agent_id}' のメッセージキュー: {queue_size}件")
        elif isinstance(self.agents, list):
            for agent in self.agents:
                if hasattr(agent, 'agent_id') and hasattr(agent, 'message_queue'):
                    queue_size = len(agent.message_queue)
                    if queue_size > 0:
                        print(f"エージェント '{agent.agent_id}' のメッセージキュー: {queue_size}件")
        
        if isinstance(self.agents, dict):
            for agent_id, agent in self.agents.items():
                responses = agent.process_messages()
                total_processed += len(responses)
                
                if responses:
                    print(f"エージェント '{agent_id}' が {len(responses)} 件のメッセージを処理しました")
                    results[agent_id] = responses
                    
                    for response in responses:
                        self._forward_message(response, agent_id)
        elif isinstance(self.agents, list):
            for agent in self.agents:
                if hasattr(agent, 'agent_id') and hasattr(agent, 'process_messages'):
                    agent_id = agent.agent_id
                    responses = agent.process_messages()
                    total_processed += len(responses)
                    
                    if responses:
                        print(f"エージェント '{agent_id}' が {len(responses)} 件のメッセージを処理しました")
                        results[agent_id] = responses
                        
                        for response in responses:
                            self._forward_message(response, agent_id)
        
        if total_processed > 0:
            print(f"合計 {total_processed} 件のメッセージが処理されました")
            
        return results
        
    def _forward_message(self, message, sender_agent_id):
        """メッセージを転送"""
        total_processed = 0
        results = []
        
        if message.receiver_id == "broadcast":
            print(f"ブロードキャストメッセージを送信: タイプ={message.message_type}")
            
            if isinstance(self.agents, dict):
                for other_id, other_agent in self.agents.items():
                    if other_id != sender_agent_id:
                        other_agent.receive_message(message)
                        total_processed += 1
            elif isinstance(self.agents, list):
                for other_agent in self.agents:
                    if hasattr(other_agent, 'agent_id') and other_agent.agent_id != sender_agent_id:
                        other_agent.receive_message(message)
                        total_processed += 1
        else:
            receiver = self._get_agent_by_id(message.receiver_id)
            if receiver:
                print(f"メッセージを '{message.receiver_id}' に転送: タイプ={message.message_type}")
                receiver.receive_message(message)
                total_processed += 1
            else:
                print(f"警告: 受信者 '{message.receiver_id}' が見つかりません。メッセージは破棄されます。")
        
        if total_processed > 0:
            print(f"合計 {total_processed} 件のメッセージが処理されました")
            
        return results
    
    def create_task(self, task_type: str, content: Any, target_agents: Optional[List[str]] = None, requester_id: Optional[str] = None) -> str:
        """
        タスクを作成
        
        Args:
            task_type: タスクのタイプ
            content: タスクの内容
            target_agents: ターゲットエージェントのリスト（指定しない場合は適切なエージェントを自動選択）
            requester_id: タスクを要求したエージェントのID
            
        Returns:
            作成されたタスクのID
        """
        if self.coordinator is None:
            raise ValueError("調整エージェントが初期化されていません")
            
        if requester_id is None:
            requester_id = "system"
        
        if target_agents:
            valid_agents = []
            for agent_id in target_agents:
                agent_exists = False
                
                if isinstance(self.agents, dict):
                    agent_exists = agent_id in self.agents
                elif isinstance(self.agents, list):
                    agent_exists = any(hasattr(a, 'agent_id') and a.agent_id == agent_id for a in self.agents)
                
                if agent_exists:
                    valid_agents.append(agent_id)
                else:
                    print(f"警告: ターゲットエージェント '{agent_id}' が見つかりません")
                    
                    if isinstance(self.agents, dict):
                        print(f"利用可能なエージェント: {list(self.agents.keys())}")
                    elif isinstance(self.agents, list):
                        print(f"利用可能なエージェント: {[a.agent_id for a in self.agents if hasattr(a, 'agent_id')]}")
                    else:
                        print(f"エージェントコンテナの型が不明です: {type(self.agents)}")
                    
                    if agent_id == "coordinator" and self.coordinator:
                        print(f"'coordinator' を '{self.coordinator.agent_id}' に置き換えます")
                        valid_agents.append(self.coordinator.agent_id)
            
            if not valid_agents:
                print(f"エラー: 有効なターゲットエージェントがありません")
                valid_agents = [self.coordinator.agent_id]
                
            target_agents = valid_agents
            
        task_id = self.coordinator.create_task(task_type, content, target_agents, requester_id)
        print(f"タスク '{task_id}' が作成されました: タイプ={task_type}, ターゲット={target_agents}")
        return task_id
    
    def get_task_results(self, task_id: str) -> Dict[str, Any]:
        """
        タスク結果を取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスク結果の辞書
        """
        if self.coordinator is None:
            raise ValueError("調整エージェントが初期化されていません")
            
        return self.coordinator.get_task_results(task_id)
    
    def run_until_completion(self, task_id: str, max_iterations: int = 300, timeout: float = 30.0) -> Dict[str, Any]:
        """
        タスクが完了するまで実行
        
        Args:
            task_id: タスクID
            max_iterations: 最大反復回数
            timeout: タイムアウト（秒）
            
        Returns:
            タスク結果
        """
        from .agent_base import AgentMessage
        
        if self.coordinator is None:
            raise ValueError("調整エージェントが初期化されていません")
            
        start_time = time.time()
        iterations = 0
        last_status_change_time = start_time
        
        print(f"タスク '{task_id}' の完了を待機中... (タイムアウト: {timeout}秒, 最大反復: {max_iterations})")
        
        if task_id not in self.coordinator.active_tasks:
            print(f"警告: タスク '{task_id}' が調整エージェントのアクティブタスクリストに存在しません")
            print(f"アクティブタスク: {list(self.coordinator.active_tasks.keys())}")
            return {"error": f"タスク '{task_id}' が見つかりません", "task_id": task_id}
        else:
            print(f"タスク '{task_id}' の初期状態: {self.coordinator.active_tasks[task_id]['status']}")
            print(f"ターゲットエージェント: {self.coordinator.active_tasks[task_id]['target_agents']}")
            
            if self.coordinator.active_tasks[task_id]['status'] == 'created':
                print(f"タスク '{task_id}' の状態を 'created' から 'processing' に強制更新します")
                self.coordinator.update_task_status(task_id, 'processing')
                last_status_change_time = time.time()
        
        task_info = self.coordinator.active_tasks[task_id]
        for agent_id in task_info['target_agents']:
            agent = self._get_agent_by_id(agent_id)
            if agent:
                print(f"タスクメッセージを '{agent_id}' に直接送信します")
                self.send_message(
                    sender_id="system",
                    receiver_id=agent_id,
                    content=task_info['content'],
                    message_type="task",
                    metadata={
                        "task_id": task_id,
                        "task_type": task_info['type']
                    }
                )
            else:
                print(f"警告: エージェント '{agent_id}' が見つかりません")
                if agent_id == "coordinator" and self.coordinator:
                    print(f"コーディネーターエージェントにタスクを直接割り当てます")
                    message = AgentMessage(
                        sender_id="system",
                        receiver_id="coordinator",
                        content=task_info['content'],
                        message_type="task",
                        metadata={
                            "task_id": task_id,
                            "task_type": task_info['type']
                        }
                    )
                    self.coordinator.receive_message(message)
        
        while iterations < max_iterations and time.time() - start_time < timeout:
            processed_results = self.process_messages()
            
            if processed_results:
                print(f"イテレーション {iterations}: メッセージが処理されました")
                for agent_id, messages in processed_results.items():
                    print(f"  エージェント '{agent_id}': {len(messages)}件のメッセージを処理")
            
            if task_id not in self.coordinator.active_tasks:
                print(f"警告: タスク '{task_id}' がアクティブタスクリストから削除されました")
                break
                
            task_status = self.coordinator.active_tasks[task_id]['status']
            
            current_time = time.time()
            status_wait_time = current_time - last_status_change_time
            
            if task_status == "processing" and (iterations > 30 and iterations % 30 == 0 or status_wait_time > 10):
                print(f"タスク '{task_id}' は処理中のままです（{status_wait_time:.1f}秒経過）。結果を確認します...")
                results = self.coordinator.get_task_results(task_id)
                if results:
                    print(f"タスク '{task_id}' に結果がありますが、完了マークがされていません。強制的に完了にします。")
                    self.coordinator.update_task_status(task_id, "completed")
                    task_status = "completed"
                    last_status_change_time = current_time
            
            if iterations % 10 == 0 or task_status != self.coordinator.active_tasks[task_id].get('previous_status', ''):
                elapsed = time.time() - start_time
                print(f"タスク '{task_id}' の状態: {task_status} ({elapsed:.1f}秒経過, {iterations}回目の確認)")
                
                if task_status != self.coordinator.active_tasks[task_id].get('previous_status', ''):
                    last_status_change_time = current_time
                    self.coordinator.active_tasks[task_id]['previous_status'] = task_status
            
            if task_status == "completed":
                print(f"タスク '{task_id}' が完了しました。結果を取得します。")
                result = self.get_task_results(task_id)
                if not result:
                    print(f"警告: タスク '{task_id}' は完了していますが、結果が見つかりません")
                    return {"error": "タスクは完了していますが、結果が見つかりません", "task_id": task_id}
                return result
                
            iterations += 1
            time.sleep(0.1)  # 短い待機時間
        
        elapsed = time.time() - start_time
        print(f"タスク '{task_id}' がタイムアウトしました。({elapsed:.1f}秒経過, {iterations}回の確認)")
        
        if task_id in self.coordinator.active_tasks:
            task_info = self.coordinator.active_tasks[task_id]
            print(f"タスク情報:")
            print(f"  タイプ: {task_info.get('type')}")
            print(f"  ステータス: {task_info.get('status')}")
            print(f"  作成時刻: {task_info.get('created_at')}")
            print(f"  更新時刻: {task_info.get('updated_at')}")
            print(f"  ターゲットエージェント: {task_info.get('target_agents')}")
            print(f"  結果数: {len(task_info.get('results', {}))}")
            
            target_agents = task_info.get("target_agents", [])
            for agent_id in target_agents:
                print(f"エージェント '{agent_id}' の状態を確認中...")
                agent = self._get_agent_by_id(agent_id)
                if agent:
                    print(f"  エージェント '{agent_id}' が見つかりました")
                    if hasattr(agent, 'message_queue'):
                        print(f"  メッセージキュー長: {len(agent.message_queue)}")
                else:
                    print(f"  エージェント '{agent_id}' が見つかりません")
        else:
            print(f"タスク '{task_id}' の情報が見つかりません")
        
        return {"error": "タスクが完了しませんでした", "task_id": task_id}
        
    def _get_agent_by_id(self, agent_id: str):
        """IDからエージェントを取得"""
        if agent_id == "coordinator" and self.coordinator:
            return self.coordinator
            
        if isinstance(self.agents, dict):
            return self.agents.get(agent_id)
        
        elif isinstance(self.agents, list):
            if not all(hasattr(a, 'agent_id') for a in self.agents):
                print(f"警告: エージェントリストに無効なオブジェクトが含まれています: {self.agents}")
                self.agents = [a for a in self.agents if hasattr(a, 'agent_id')]
                
            return next((a for a in self.agents if a.agent_id == agent_id), None)
        
        else:
            print(f"警告: エージェントコンテナの型が不明です: {type(self.agents)}")
            return None
        
    def wait_for_task_result(self, task_id: str, timeout: float = 30.0) -> Dict[str, Any]:
        """
        タスク結果を待機
        
        Args:
            task_id: タスクID
            timeout: タイムアウト（秒）
            
        Returns:
            タスク結果
        """
        print(f"タスク '{task_id}' の結果を待機中... (タイムアウト: {timeout}秒)")
        
        if self.coordinator and task_id not in self.coordinator.active_tasks:
            print(f"警告: タスク '{task_id}' が調整エージェントのアクティブタスクリストに存在しません")
            return {
                "success": False,
                "error": f"タスク '{task_id}' が見つかりません"
            }
        
        result = self.run_until_completion(task_id, max_iterations=int(timeout * 10), timeout=timeout)
        
        if "error" in result:
            print(f"タスク '{task_id}' の実行に失敗しました: {result['error']}")
            
            if self.coordinator and hasattr(self.coordinator, 'active_tasks'):
                task_info = self.coordinator.active_tasks.get(task_id, {})
                if task_info:
                    task_status = task_info.get("status", "不明")
                    print(f"タスクステータス: {task_status}")
                    
                    results = task_info.get("results", {})
                    if results:
                        print(f"部分的な結果が {len(results)} 件あります")
                        for agent_id, result_data in results.items():
                            print(f"  エージェント '{agent_id}' からの結果: {result_data.get('timestamp')}")
                        
                        if len(results) > 0:
                            print(f"タスク '{task_id}' は完了していませんが、部分的な結果を返します")
                            
                            first_agent_id = list(results.keys())[0]
                            first_result = results[first_agent_id].get("result", {})
                            
                            return {
                                "success": True,
                                "result": first_result,
                                "partial": True,
                                "warning": "タスクは完了していませんが、部分的な結果を返しています"
                            }
            
            return {
                "success": False,
                "error": result.get("error", "タスクが完了しませんでした")
            }
        
        print(f"タスク '{task_id}' が正常に完了しました")
        
        if not isinstance(result, dict):
            return {
                "success": True,
                "result": result
            }
        
        return {
            "success": True,
            "result": result
        }
    
    def add_knowledge(self, subject: str, fact: str, confidence: float = 0.9) -> Dict[str, Any]:
        """
        知識を追加
        
        Args:
            subject: 主題
            fact: 事実
            confidence: 確信度
            
        Returns:
            タスク結果
        """
        task_id = self.create_task(
            task_type="add_knowledge",
            content={
                "subject": subject,
                "fact": fact,
                "confidence": confidence
            },
            target_agents=[agent.agent_id for agent in self.agents.values() if agent.role == AgentRole.KNOWLEDGE]
        )
        
        return self.run_until_completion(task_id)
    
    def search_knowledge(self, query: str) -> Dict[str, Any]:
        """
        知識を検索
        
        Args:
            query: 検索クエリ
            
        Returns:
            検索結果
        """
        task_id = self.create_task(
            task_type="search_knowledge",
            content={"query": query},
            target_agents=[agent.agent_id for agent in self.agents.values() if agent.role == AgentRole.KNOWLEDGE]
        )
        
        return self.run_until_completion(task_id)
    
    def web_search(self, query: str, search_depth: str = "basic") -> Dict[str, Any]:
        """
        Web検索を実行
        
        Args:
            query: 検索クエリ
            search_depth: 検索の深さ（"basic"または"deep"）
            
        Returns:
            検索結果
        """
        task_id = self.create_task(
            task_type="web_search",
            content={
                "query": query,
                "search_depth": search_depth
            },
            target_agents=[agent.agent_id for agent in self.agents.values() if agent.role == AgentRole.TOOL_EXECUTOR]
        )
        
        return self.run_until_completion(task_id)
    
    def generate_reasoning_chain(self, task_description: str, current_state: str = "", max_steps: int = 5) -> Dict[str, Any]:
        """
        推論チェーンを生成
        
        Args:
            task_description: タスクの説明
            current_state: 現在の状態
            max_steps: 最大ステップ数
            
        Returns:
            生成された推論チェーン
        """
        task_id = self.create_task(
            task_type="reasoning_chain",
            content={
                "task_description": task_description,
                "current_state": current_state,
                "max_steps": max_steps
            },
            target_agents=[agent.agent_id for agent in self.agents.values() if agent.role == AgentRole.MAIN_REASONING]
        )
        
        return self.run_until_completion(task_id)
    
    def fix_code_with_reasoning(self, code: str, error_message: str) -> Dict[str, Any]:
        """
        推論を使用してコードを修正
        
        Args:
            code: 修正対象のコード
            error_message: エラーメッセージ
            
        Returns:
            修正されたコード
        """
        task_id = self.create_task(
            task_type="fix_code",
            content={
                "code": code,
                "error_message": error_message
            },
            target_agents=[agent.agent_id for agent in self.agents.values() if agent.role == AgentRole.MAIN_REASONING]
        )
        
        return self.run_until_completion(task_id)
    
    def evaluate_text(self, text: str, criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        テキストを評価
        
        Args:
            text: 評価するテキスト
            criteria: 評価基準
            
        Returns:
            評価結果
        """
        task_id = self.create_task(
            task_type="evaluate_text",
            content={
                "text": text,
                "criteria": criteria
            },
            target_agents=[agent.agent_id for agent in self.agents.values() if agent.role == AgentRole.EVALUATION]
        )
        
        return self.run_until_completion(task_id)
    
    def provide_domain_expertise(self, domain: str, query: str) -> Dict[str, Any]:
        """
        ドメイン専門知識を提供
        
        Args:
            domain: 専門分野
            query: 質問内容
            
        Returns:
            専門家の回答
        """
        domain_experts = [
            agent for agent in self.agents.values()
            if agent.role == AgentRole.DOMAIN_EXPERT and hasattr(agent, 'domain') and agent.domain == domain
        ]
        
        if not domain_experts:
            expert_id = self.add_domain_expert(domain)
            target_agents = [expert_id]
        else:
            target_agents = [expert.agent_id for expert in domain_experts]
        
        task_id = self.create_task(
            task_type="provide_expertise",
            content={"query": query},
            target_agents=target_agents
        )
        
        return self.run_until_completion(task_id)
    
    def extract_knowledge_from_text(self, text: str) -> Dict[str, Any]:
        """
        テキストから知識を抽出
        
        Args:
            text: 抽出元のテキスト
            
        Returns:
            抽出された知識
        """
        task_id = self.create_task(
            task_type="extract_knowledge",
            content={"text": text},
            target_agents=[agent.agent_id for agent in self.agents.values() if agent.role == AgentRole.KNOWLEDGE]
        )
        
        return self.run_until_completion(task_id)
    
    def save_state(self, path: str) -> bool:
        """
        システムの状態を保存
        
        Args:
            path: 保存先のパス
            
        Returns:
            保存が成功したかどうか
        """
        if self.coordinator is None:
            raise ValueError("調整エージェントが初期化されていません")
            
        try:
            knowledge_agents = [
                agent for agent in self.agents.values()
                if agent.role == AgentRole.KNOWLEDGE
            ]
            
            for agent in knowledge_agents:
                if hasattr(agent, '_save_knowledge_db'):
                    agent._save_knowledge_db()
                if hasattr(agent, '_save_knowledge_graph'):
                    agent._save_knowledge_graph()
            
            system_state = {
                "agents": {},
                "coordinator": {
                    "registered_agents": self.coordinator.registered_agents,
                    "active_tasks": self.coordinator.active_tasks
                }
            }
            
            for agent_id, agent in self.agents.items():
                if agent_id != self.coordinator.agent_id:
                    system_state["agents"][agent_id] = {
                        "role": agent.role.value if hasattr(agent.role, 'value') else str(agent.role),
                        "name": agent.name,
                        "description": agent.description,
                        "state": agent.get_state()
                    }
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(system_state, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            print(f"状態保存エラー: {str(e)}")
            return False
    
    def load_state(self, path: str) -> bool:
        """
        システムの状態を読み込み
        
        Args:
            path: 読み込み元のパス
            
        Returns:
            読み込みが成功したかどうか
        """
        if self.coordinator is None:
            raise ValueError("調整エージェントが初期化されていません")
            
        if not os.path.exists(path):
            return False
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                system_state = json.load(f)
                
            if "coordinator" in system_state:
                coordinator_state = system_state["coordinator"]
                self.coordinator.registered_agents = coordinator_state.get("registered_agents", {})
                self.coordinator.active_tasks = coordinator_state.get("active_tasks", {})
                
            if "agents" in system_state:
                for agent_id, agent_state in system_state["agents"].items():
                    if agent_id in self.agents:
                        self.agents[agent_id].update_state(agent_state.get("state", {}))
                        
            return True
        except Exception as e:
            print(f"状態読み込みエラー: {str(e)}")
            return False
