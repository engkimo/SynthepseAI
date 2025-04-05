from typing import Dict, List, Optional, Any, Union
import os
import time
import json

from .base_flow import BaseFlow
from .task_database import TaskDatabase, TaskStatus
from .base_agent import BaseAgent
from .rome_model_editor import ROMEModelEditor
from .coat_reasoner import COATReasoner
from .rgcn_processor import RGCNProcessor
from .multi_agent.multi_agent_system import MultiAgentSystem

class LLLMMultiAgentFlow(BaseFlow):
    """
    LLLM（Larger LLM）マルチエージェントフロー
    
    複数のエージェントを連携させ、ROME・COAT・R-GCNを統合した
    自律的な知的エコシステムを実現する
    """
    
    def __init__(
        self, 
        llm, 
        task_db: TaskDatabase,
        workspace_dir: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        LLLMマルチエージェントフローの初期化
        
        Args:
            llm: 使用するLLMインスタンス
            task_db: タスクデータベース
            workspace_dir: ワークスペースディレクトリ
            config: 設定情報
        """
        super().__init__()
        self.llm = llm
        self.task_db = task_db
        self.workspace_dir = workspace_dir
        self.config = config or {}
        
        self.rome_editor = self._init_rome_editor()
        self.coat_reasoner = self._init_coat_reasoner()
        self.rgcn_processor = self._init_rgcn_processor()
        
        self.multi_agent_system = self._init_multi_agent_system()
        
        self.active_plan_id = None
        self.current_step_index = 0
        self.execution_history = []
    
    def _init_rome_editor(self) -> ROMEModelEditor:
        """ROMEモデルエディタの初期化"""
        device = self.config.get("device", "cpu")
        rome_editor = ROMEModelEditor(device=device)
        
        return rome_editor
    
    def _init_coat_reasoner(self) -> COATReasoner:
        """COAT推論機能の初期化"""
        coat_reasoner = COATReasoner(self.llm)
        
        return coat_reasoner
    
    def _init_rgcn_processor(self) -> RGCNProcessor:
        """R-GCNプロセッサの初期化"""
        device = self.config.get("device", "cpu")
        hidden_dim = self.config.get("rgcn_hidden_dim", 64)
        use_compatibility_mode = self.config.get("use_compatibility_mode", True)
        
        rgcn_processor = RGCNProcessor(
            device=device,
            hidden_dim=hidden_dim,
            use_compatibility_mode=use_compatibility_mode
        )
        
        knowledge_graph_path = os.path.join(self.workspace_dir, "knowledge_graph.json")
        
        if os.path.exists(knowledge_graph_path):
            rgcn_processor.load_graph(knowledge_graph_path)
        
        return rgcn_processor
    
    def _init_multi_agent_system(self) -> MultiAgentSystem:
        """マルチエージェントシステムの初期化"""
        agent_config = {
            "workspace_dir": self.workspace_dir,
            "use_web_tools": "tavily_api_key" in self.config or "firecrawl_api_key" in self.config,
            "mock_mode": self.config.get("mock_mode", False)
        }
        
        multi_agent_system = MultiAgentSystem(
            llm=self.llm,
            config=agent_config,
            rome_editor=self.rome_editor,
            coat_reasoner=self.coat_reasoner,
            rgcn_processor=self.rgcn_processor
        )
        
        return multi_agent_system
    
    def execute(self, input_text: str) -> str:
        """
        LLLMマルチエージェントフローを実行
        
        Args:
            input_text: 入力テキスト（ユーザーの目標）
            
        Returns:
            実行結果
        """
        print(f"LLLMマルチエージェントフローを開始: '{input_text}'")
        
        plan_result = self._generate_plan(input_text)
        
        if not plan_result["success"]:
            return f"計画生成に失敗しました: {plan_result['error']}"
        
        self.active_plan_id = plan_result["plan_id"]
        
        execution_result = self._execute_tasks(self.active_plan_id)
        
        summary = self._generate_summary(self.active_plan_id, execution_result)
        
        knowledge_graph_path = os.path.join(self.workspace_dir, "knowledge_graph.json")
        self.rgcn_processor.save_graph(knowledge_graph_path)
        
        return summary
    
    def _generate_plan(self, goal: str) -> Dict[str, Any]:
        """
        目標から計画を生成
        
        Args:
            goal: ユーザーの目標
            
        Returns:
            計画生成結果
        """
        try:
            print(f"計画生成を開始: '{goal}'")
            
            plan_task = {
                "type": "generate_plan",
                "goal": goal,
                "max_tasks": 10
            }
            
            print("コーディネーターエージェントにタスクを割り当て中...")
            
            task_id = self.multi_agent_system.create_task(
                task_type="generate_plan",
                content=plan_task,
                target_agents=["coordinator"],
                requester_id="system"
            )
            
            print(f"タスクID '{task_id}' が作成されました。結果を待機中...")
            
            coordinator = self.multi_agent_system.coordinator
            if coordinator and task_id in coordinator.active_tasks:
                initial_status = coordinator.active_tasks[task_id]["status"]
                print(f"タスク '{task_id}' の初期状態: {initial_status}")
                
                if initial_status == "created":
                    print(f"タスク '{task_id}' の状態を 'created' から 'processing' に更新します")
                    coordinator.update_task_status(task_id, "processing")
                    
                    print(f"タスクメッセージをコーディネーターに直接送信します")
                    self.multi_agent_system.send_message(
                        sender_id="system",
                        receiver_id="coordinator",
                        content=plan_task,
                        message_type="task",
                        metadata={
                            "task_id": task_id,
                            "task_type": "generate_plan"
                        }
                    )
            
            result = self.multi_agent_system.wait_for_task_result(task_id, timeout=180)
            
            if not result["success"]:
                error_msg = result.get("error", "計画生成中にエラーが発生しました")
                print(f"計画生成エラー: {error_msg}")
                
                if "partial" in result and result["partial"] and "result" in result:
                    print("部分的な結果が利用可能です。これを使用して続行します。")
                    partial_result = result["result"]
                    
                    if isinstance(partial_result, dict) and "plan_id" in partial_result:
                        plan_id = partial_result["plan_id"]
                        tasks = partial_result.get("tasks", [])
                        
                        if tasks:
                            print(f"部分的な結果から計画を作成します: {plan_id}")
                            for i, task_info in enumerate(tasks):
                                self.task_db.add_task(
                                    plan_id=plan_id,
                                    description=task_info["description"],
                                    dependencies=task_info.get("dependencies", [])
                                )
                            
                            return {
                                "success": True,
                                "plan_id": plan_id,
                                "task_count": len(tasks),
                                "warning": "タスクは完全には完了しませんでしたが、部分的な結果を使用しています"
                            }
                
                return {
                    "success": False,
                    "error": error_msg
                }
            
            print("計画生成が成功しました。タスクをデータベースに追加中...")
            
            plan_id = result["result"]["plan_id"]
            tasks = result["result"].get("tasks", [])
            
            for i, task_info in enumerate(tasks):
                self.task_db.add_task(
                    plan_id=plan_id,
                    description=task_info["description"],
                    dependencies=task_info.get("dependencies", [])
                )
            
            print(f"計画 '{plan_id}' が作成されました。タスク数: {len(tasks)}")
            
            return {
                "success": True,
                "plan_id": plan_id,
                "task_count": len(tasks)
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"計画生成中に例外が発生しました: {str(e)}")
            print(f"詳細なエラー情報: {error_details}")
            
            return {
                "success": False,
                "error": f"計画生成エラー: {str(e)}"
            }
    
    def _execute_tasks(self, plan_id: str) -> Dict[str, Any]:
        """
        計画内のタスクを実行
        
        Args:
            plan_id: 計画ID
            
        Returns:
            実行結果
        """
        tasks = self.task_db.get_tasks_by_plan(plan_id)
        
        results = {
            "success": True,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "task_results": []
        }
        
        for task in tasks:
            dependencies = self.task_db.get_task_dependencies(task.id)
            dependency_failed = False
            
            for dep_id in dependencies:
                dep_task = self.task_db.get_task(dep_id)
                if dep_task and dep_task.status == TaskStatus.FAILED:
                    dependency_failed = True
                    break
            
            if dependency_failed:
                self.task_db.update_task(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    result="依存タスクが失敗したため、このタスクはスキップされました"
                )
                results["failed_tasks"] += 1
                continue
            
            execution_result = self._execute_single_task(task)
            results["task_results"].append(execution_result)
            
            if execution_result["success"]:
                results["completed_tasks"] += 1
            else:
                results["failed_tasks"] += 1
                
                repair_result = self._repair_failed_task(task.id)
                
                if repair_result["success"]:
                    results["failed_tasks"] -= 1
                    results["completed_tasks"] += 1
        
        results["success"] = results["failed_tasks"] == 0
        
        return results
    
    def _execute_single_task(self, task) -> Dict[str, Any]:
        """
        単一のタスクを実行
        
        Args:
            task: 実行するタスク
            
        Returns:
            実行結果
        """
        try:
            task_analysis = self._analyze_task(task.description)
            
            agent_id = self._select_agent_for_task(task_analysis)
            
            execution_task = {
                "type": "execute_task",
                "task_id": task.id,
                "description": task.description,
                "task_type": task_analysis["task_type"]
            }
            
            task_id = self.multi_agent_system.create_task(
                task_type="execute_task",
                content=execution_task,
                target_agents=[agent_id]
            )
            
            result = self.multi_agent_system.wait_for_task_result(task_id, timeout=120)
            
            if not result["success"]:
                self.task_db.update_task(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    result=f"実行エラー: {result.get('error', '不明なエラー')}"
                )
                
                return {
                    "task_id": task.id,
                    "success": False,
                    "error": result.get("error", "タスク実行中にエラーが発生しました")
                }
            
            self.task_db.update_task(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result=json.dumps(result["result"], ensure_ascii=False)
            )
            
            if "code" in result["result"]:
                self.task_db.update_task_code(
                    task_id=task.id,
                    code=result["result"].get("code", "")
                )
            
            self.execution_history.append({
                "task_id": task.id,
                "description": task.description,
                "agent_id": agent_id,
                "result": result["result"],
                "timestamp": time.time()
            })
            
            return {
                "task_id": task.id,
                "success": True,
                "result": result["result"]
            }
            
        except Exception as e:
            self.task_db.update_task(
                task_id=task.id,
                status=TaskStatus.FAILED,
                result=f"実行エラー: {str(e)}"
            )
            
            return {
                "task_id": task.id,
                "success": False,
                "error": f"タスク実行エラー: {str(e)}"
            }
    
    def _analyze_task(self, task_description: str) -> Dict[str, Any]:
        """
        タスクの種類を分析
        
        Args:
            task_description: タスクの説明
            
        Returns:
            タスク分析結果
        """
        analysis_task = {
            "type": "analyze_task",
            "description": task_description
        }
        
        task_id = self.multi_agent_system.create_task(
            task_type="analyze_task",
            content=analysis_task,
            target_agents=["reasoning_agent"]
        )
        
        result = self.multi_agent_system.wait_for_task_result(task_id, timeout=30)
        
        if not result["success"]:
            return {
                "task_type": "general",
                "complexity": "medium",
                "required_tools": ["python_execute"]
            }
        
        return result["result"]
    
    def _select_agent_for_task(self, task_analysis: Dict[str, Any]) -> str:
        """
        タスクに適したエージェントを選択
        
        Args:
            task_analysis: タスク分析結果
            
        Returns:
            選択されたエージェントID
        """
        task_type = task_analysis.get("task_type", "general")
        required_tools = task_analysis.get("required_tools", [])
        
        if "web_search" in required_tools or "web_crawling" in task_type:
            return "tool_executor_agent"
        elif "knowledge_graph" in required_tools or "knowledge_processing" in task_type:
            return "knowledge_agent"
        elif "code_generation" in task_type or "programming" in task_type:
            return "reasoning_agent"
        elif task_type in ["analysis", "evaluation", "assessment"]:
            return "evaluation_agent"
        
        return "coordinator"
    
    def _repair_failed_task(self, task_id: str) -> Dict[str, Any]:
        """
        失敗したタスクを修復
        
        Args:
            task_id: 修復するタスクID
            
        Returns:
            修復結果
        """
        task = self.task_db.get_task(task_id)
        
        if not task or task.status != TaskStatus.FAILED:
            return {
                "success": False,
                "error": "修復対象のタスクが見つからないか、失敗状態ではありません"
            }
        
        repair_task = {
            "type": "repair_task",
            "task_id": task_id,
            "description": task.description,
            "error": task.result
        }
        
        task_id = self.multi_agent_system.create_task(
            task_type="repair_task",
            content=repair_task,
            target_agents=["reasoning_agent"]
        )
        
        result = self.multi_agent_system.wait_for_task_result(task_id, timeout=60)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "タスク修復中にエラーが発生しました")
            }
        
        fixed_code = result["result"].get("fixed_code", "")
        
        if fixed_code:
            self.task_db.update_task_code(task.id, fixed_code)
            
            execution_task = {
                "type": "execute_code",
                "task_id": task.id,
                "code": fixed_code
            }
            
            exec_task_id = self.multi_agent_system.create_task(
                task_type="execute_code",
                content=execution_task,
                target_agents=["tool_executor_agent"]
            )
            
            exec_result = self.multi_agent_system.wait_for_task_result(exec_task_id, timeout=60)
            
            if exec_result["success"]:
                self.task_db.update_task(
                    task_id=task.id,
                    status=TaskStatus.COMPLETED,
                    result=json.dumps(exec_result["result"], ensure_ascii=False)
                )
                
                return {
                    "success": True,
                    "message": "タスクの修復と再実行に成功しました"
                }
        
        return {
            "success": False,
            "error": "タスクの修復に失敗しました"
        }
    
    def _generate_summary(self, plan_id: str, execution_result: Dict[str, Any]) -> str:
        """
        実行結果の要約を生成
        
        Args:
            plan_id: 計画ID
            execution_result: 実行結果
            
        Returns:
            生成された要約
        """
        tasks = self.task_db.get_tasks_by_plan(plan_id)
        
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]
        
        summary_task = {
            "type": "generate_summary",
            "plan_id": plan_id,
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "task_results": [
                {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status.name,
                    "result": t.result
                }
                for t in tasks
            ]
        }
        
        task_id = self.multi_agent_system.create_task(
            task_type="generate_summary",
            content=summary_task,
            target_agents=["coordinator"]
        )
        
        result = self.multi_agent_system.wait_for_task_result(task_id, timeout=30)
        
        if not result["success"]:
            return f"""
            実行結果:
            - 完了タスク: {len(completed_tasks)}/{len(tasks)}
            - 失敗タスク: {len(failed_tasks)}/{len(tasks)}
            
            詳細はタスクデータベースを参照してください。
            """
        
        return result["result"]["summary"]
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """実行履歴を取得"""
        return self.execution_history
