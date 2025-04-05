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
            "use_web_tools": self.tavily_api_key is not None or self.firecrawl_api_key is not None
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
        if sender_id not in self.agents:
            return False
            
        if receiver_id not in self.agents and receiver_id != "broadcast":
            return False
            
        sender = self.agents[sender_id]
        message = sender.send_message(
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            metadata=metadata
        )
        
        if receiver_id == "broadcast":
            for agent_id, agent in self.agents.items():
                if agent_id != sender_id:
                    agent.receive_message(message)
        else:
            receiver = self.agents[receiver_id]
            receiver.receive_message(message)
            
        return True
    
    def process_messages(self) -> Dict[str, List[AgentMessage]]:
        """
        すべてのエージェントのメッセージを処理
        
        Returns:
            エージェントIDから処理結果のメッセージリストへのマッピング
        """
        results = {}
        
        for agent_id, agent in self.agents.items():
            responses = agent.process_messages()
            
            if responses:
                results[agent_id] = responses
                
                for response in responses:
                    if response.receiver_id in self.agents:
                        receiver = self.agents[response.receiver_id]
                        receiver.receive_message(response)
                    elif response.receiver_id == "broadcast":
                        for other_id, other_agent in self.agents.items():
                            if other_id != agent_id:
                                other_agent.receive_message(response)
        
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
            
        return self.coordinator.create_task(task_type, content, target_agents, requester_id)
    
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
    
    def run_until_completion(self, task_id: str, max_iterations: int = 10, timeout: float = 30.0) -> Dict[str, Any]:
        """
        タスクが完了するまで実行
        
        Args:
            task_id: タスクID
            max_iterations: 最大反復回数
            timeout: タイムアウト（秒）
            
        Returns:
            タスク結果
        """
        if self.coordinator is None:
            raise ValueError("調整エージェントが初期化されていません")
            
        start_time = time.time()
        iterations = 0
        
        while iterations < max_iterations and time.time() - start_time < timeout:
            self.process_messages()
            
            task_status = self.coordinator.active_tasks.get(task_id, {}).get("status")
            
            if task_status == "completed":
                return self.get_task_results(task_id)
                
            iterations += 1
            time.sleep(0.1)  # 短い待機時間
            
        return {"error": "タスクが完了しませんでした", "task_id": task_id}
        
    def wait_for_task_result(self, task_id: str, timeout: float = 30.0) -> Dict[str, Any]:
        """
        タスク結果を待機
        
        Args:
            task_id: タスクID
            timeout: タイムアウト（秒）
            
        Returns:
            タスク結果
        """
        result = self.run_until_completion(task_id, max_iterations=int(timeout * 10), timeout=timeout)
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"]
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
