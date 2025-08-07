from typing import Dict, List, Any, Optional, Tuple, Union
import os
import json
import time
import logging
import threading
from queue import Queue, Empty

from .llm import LLM
from .rome_model_editor import ROMEModelEditor, EditRequest
from .coat_reasoner import COATReasoner
from .rgcn_processor import RGCNProcessor
from .auto_plan_agent import AutoPlanAgent
from .task_database import TaskDatabase
from .tools.web_crawling_tool import WebCrawlingTool

class EnhancedPersistentThinkingAI:
    """
    強化版持続思考型AI - ROME、COAT、R-GCNを統合した自律的思考システム
    
    強化版持続思考型AIは：
    1. バックグラウンドスレッドで常に考え続ける（タスク完了後も思考を継続）
    2. 知識を蓄積し、修正する（ROMEを使用）
    3. 自己反省を行う（COATを使用）
    4. 知識グラフでコンテクストを強化する（R-GCNを使用）
    5. Webから情報を取得する（WebCrawlingToolを使用）
    6. 外部知識ベースを参照する（ExternalKnowledgeBaseConnectorを使用）
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/phi-2",
        workspace_dir: str = "./workspace",
        device: Optional[str] = None,
        knowledge_db_path: str = "./knowledge_db.json",
        log_path: str = "./thinking_log.jsonl",
        use_compatibility_mode: bool = False,
        tavily_api_key: Optional[str] = None,
        firecrawl_api_key: Optional[str] = None,
        enable_multi_agent: bool = False,
        specialized_agents: Optional[List[Dict[str, Any]]] = None,
        llm_provider: str = "openai",
        openrouter_api_key: Optional[str] = None
    ):
        """
        強化版持続思考型AIの初期化
        
        Args:
            model_name: 使用するローカルモデル名
            workspace_dir: 作業ディレクトリ
            device: 使用するデバイス（'cuda', 'mps', 'cpu'）
            knowledge_db_path: 知識データベースのパス
            log_path: 思考ログのパス
            use_compatibility_mode: DGL/PyTorch非依存の互換モードを使用するかどうか
            tavily_api_key: TavilyのAPIキー
            firecrawl_api_key: FirecrawlのAPIキー
        """
        if llm_provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "dummy_key_for_testing")
            model = "gpt-3.5-turbo"
        elif llm_provider == "openrouter":
            api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY", "dummy_key_for_testing")
            model = model_name if "claude" in model_name else "anthropic/claude-3-7-sonnet"
        else:
            api_key = os.environ.get("OPENAI_API_KEY", "dummy_key_for_testing")
            model = "gpt-3.5-turbo"
        
        self.use_compatibility_mode = use_compatibility_mode
        
        self.llm = LLM(
            api_key=api_key,
            model=model,
            temperature=0.7,
            provider=llm_provider
        )
        
        self.rome_model_editor = ROMEModelEditor(device=device)
        
        self.coat_reasoner = COATReasoner(self.llm)
        
        self.rgcn_processor = RGCNProcessor(device=device, use_compatibility_mode=self.use_compatibility_mode)
        
        self.thinking_queue = Queue()
        self._initialize_knowledge_graph()
        
        self.task_db = TaskDatabase(":memory:")
        self.agent = AutoPlanAgent(
            name="PersistentThinkingAgent",
            description="持続的に思考し、自己改善する自律エージェント",
            llm=self.llm,
            task_db=self.task_db,
            workspace_dir=workspace_dir
        )
        
        self.web_crawler = WebCrawlingTool(
            tavily_api_key=tavily_api_key,
            firecrawl_api_key=firecrawl_api_key
        )
        
        self.enable_multi_agent = enable_multi_agent
        self.multi_agent_discussion = None
        if enable_multi_agent:
            try:
                from .multi_agent_discussion import MultiAgentDiscussion, DiscussionAgent
                self.multi_agent_discussion = MultiAgentDiscussion(
                    knowledge_db_path=knowledge_db_path,
                    log_path=log_path
                )
                
                if specialized_agents:
                    for agent_config in specialized_agents:
                        agent = DiscussionAgent(**agent_config)
                        self.multi_agent_discussion.add_agent(agent)
            except ImportError:
                print("マルチエージェント討論機能を有効にするには langchain をインストールしてください")
                self.enable_multi_agent = False
        
        self.knowledge_db_path = knowledge_db_path
        self._load_knowledge_db()
        
        self.log_path = log_path
        self._setup_log()
        
        self.thinking_state = {
            "current_task": None,
            "reflections": [],
            "knowledge_updates": [],
            "last_thought_time": time.time()
        }
        
        self.knowledge_triples = []
        self.graph = None
        
        self.thinking_thread = None
        self.stop_thinking = False
    def _initialize_knowledge_graph(self):
        """知識グラフを初期化（ファイルが存在しない場合は作成）"""
        self.knowledge_triples = []
        self.graph = None
        
        graph_file_path = "./knowledge_graph.json"
        
        if not os.path.exists(graph_file_path):
            self.graph = self.rgcn_processor.build_graph(self.knowledge_triples)
            self.rgcn_processor.save_graph(graph_file_path)
            print(f"初期知識グラフファイルを作成しました: {graph_file_path}")
        else:
            try:
                self.graph = self.rgcn_processor.load_graph(graph_file_path)
                if self.graph:
                    print(f"知識グラフを読み込みました: {graph_file_path}")
                else:
                    print(f"知識グラフの読み込みに失敗しました。新しいグラフを作成します。")
                    self.graph = self.rgcn_processor.build_graph(self.knowledge_triples)
                    self.rgcn_processor.save_graph(graph_file_path)
            except Exception as e:
                print(f"知識グラフの読み込み中にエラーが発生しました: {str(e)}")
                print("新しいグラフを作成します。")
                self.graph = self.rgcn_processor.build_graph(self.knowledge_triples)
                self.rgcn_processor.save_graph(graph_file_path)
    
    def _load_knowledge_db(self):
        """知識データベースを読み込み"""
        self.knowledge_db = {}
        if os.path.exists(self.knowledge_db_path):
            try:
                with open(self.knowledge_db_path, 'r', encoding='utf-8') as f:
                    self.knowledge_db = json.load(f)
            except Exception as e:
                print(f"知識DB読み込みエラー: {str(e)}")
                self.knowledge_db = {}
    
    def _save_knowledge_db(self):
        """知識データベースを保存"""
        try:
            os.makedirs(os.path.dirname(self.knowledge_db_path), exist_ok=True)
            with open(self.knowledge_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"知識DB保存エラー: {str(e)}")
    
    def _setup_log(self):
        """思考ログを設定"""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', encoding='utf-8') as f:
                pass  # 空ファイルを作成
    
    def _log_thought(self, thought_type: str, content: Dict[str, Any]):
        """思考をログに記録"""
        log_entry = {
            "timestamp": time.time(),
            "type": thought_type,
            "content": content
        }
        
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"思考ログ記録エラー: {str(e)}")
    
    def execute_task(self, goal: str) -> str:
        """
        タスクを実行しながら持続的思考を行う
        
        Args:
            goal: 達成する目標
            
        Returns:
            タスク実行結果と思考プロセスのサマリー
        """
        self.thinking_state["current_task"] = goal
        self._log_thought("task_start", {"goal": goal})
        
        self.thinking_queue.put(goal)
        
        self.start_continuous_thinking()
        
        self._reflect_before_task(goal)
        
        result = self.agent.execute_plan(goal)
        
        self._continuous_thinking_after_task(goal, result)
        
        return result
    
    def _reflect_before_task(self, goal: str):
        """タスク実行前の自己反省"""
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            reflection = f"モックモード: タスク「{goal}」の実行前反省はスキップされました。実際のAPIコールは行われません。"
            
            self.thinking_state["reflections"].append({
                "time": "before_task",
                "content": reflection
            })
            
            self._log_thought("pre_task_reflection", {
                "goal": goal,
                "reflection": reflection,
                "mock_mode": True
            })
            return
            
        prompt = f"""
        以下のタスクを実行する前に、これまでの知識や経験を振り返ってください：
        
        {goal}
        
        何を考慮すべきか、どのような問題が発生する可能性があるか、どのようなアプローチが最適かを考えてください。
        """
        
        reflection = self.llm.generate_text(prompt)
        self.thinking_state["reflections"].append({
            "time": "before_task",
            "content": reflection
        })
        
        self._log_thought("pre_task_reflection", {
            "goal": goal,
            "reflection": reflection
        })
    
    def _continuous_thinking_after_task(self, goal: str, result: str):
        """タスク実行後の継続的思考プロセス"""
        self._analyze_task_result(goal, result)
        
        self._extract_and_store_knowledge(goal, result)
        
        self._update_knowledge_graph(goal, result)
        
        self._reflect_and_improve(goal, result)
        
        self._save_knowledge_db()
    
    def _analyze_task_result(self, goal: str, result: str):
        """タスク実行結果を分析"""
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            analysis = f"モックモード: タスク「{goal}」の結果分析はスキップされました。実際のAPIコールは行われません。"
            
            self._log_thought("task_analysis", {
                "goal": goal,
                "result": result,
                "analysis": analysis,
                "mock_mode": True
            })
            return
            
        prompt = f"""
        以下のタスクの実行結果を分析してください：
        
        目標：{goal}
        
        結果：
        {result}
        
        このタスクの成功点と失敗点、改善可能な点を詳細に分析してください。
        """
        
        analysis = self.llm.generate_text(prompt)
        
        self._log_thought("task_analysis", {
            "goal": goal,
            "result": result,
            "analysis": analysis
        })
        
        self.integrate_task_results(goal, result)
    
    def _extract_and_store_knowledge(self, goal: str, result: str):
        """新しい知識を抽出して保存"""
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            knowledge_json = """[
                {"subject": "モックモード", "fact": "タスク実行中にモックモードが有効でした", "confidence": 1.0}
            ]"""
            
            self._log_thought("knowledge_extraction", {
                "goal": goal,
                "result": result,
                "knowledge": knowledge_json,
                "mock_mode": True
            })
            
            try:
                import json
                knowledge_items = json.loads(knowledge_json)
                for item in knowledge_items:
                    self._update_knowledge(
                        item.get("subject", "モック主題"),
                        item.get("fact", "モックデータ"),
                        item.get("confidence", 0.8),
                        "task_extraction"
                    )
            except Exception as e:
                print(f"モック知識抽出エラー: {str(e)}")
                
            return
            
        prompt = f"""
        以下のタスクと結果から、将来のタスクに役立つ可能性のある知識を抽出してください：
        
        目標：{goal}
        
        結果：
        {result}
        
        以下の形式でJSON配列として返してください：
        [
            {{"subject": "主題", "fact": "事実や知識", "confidence": 0.9}}
        ]
        """
        
        knowledge_json = self.llm.generate_text(prompt)
        
        try:
            import re
            import json
            json_match = re.search(r'\[\s*\{.*\}\s*\]', knowledge_json, re.DOTALL)
            if json_match:
                knowledge_items = json.loads(json_match.group(0))
            else:
                knowledge_items = []
                
            for item in knowledge_items:
                subject = item.get("subject", "")
                fact = item.get("fact", "")
                confidence = item.get("confidence", 0.5)
                
                if subject and fact and confidence > 0.7:
                    original_fact = None
                    if subject in self.knowledge_db:
                        original_fact = self.knowledge_db.get(subject, {}).get("fact")
                    
                    edit_success = self.llm.edit_knowledge(
                        subject=subject,
                        target_fact=fact,
                        original_fact=original_fact
                    )
                    
                    if edit_success:
                        if subject not in self.knowledge_db:
                            self.knowledge_db[subject] = {}
                        
                        self.knowledge_db[subject]["fact"] = fact
                        self.knowledge_db[subject]["confidence"] = confidence
                        self.knowledge_db[subject]["last_updated"] = time.time()
                        
                        self.thinking_state["knowledge_updates"].append({
                            "subject": subject,
                            "from": original_fact,
                            "to": fact,
                            "confidence": confidence
                        })
                        
                        self._log_thought("knowledge_update", {
                            "subject": subject,
                            "original_fact": original_fact,
                            "new_fact": fact,
                            "confidence": confidence,
                            "success": edit_success
                        })
        except Exception as e:
            print(f"知識抽出エラー: {str(e)}")
    
    def _update_knowledge_graph(self, goal: str, result: str):
        """知識グラフを更新"""
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            triples_json = """[
                {"subject": "モックモード", "relation": "実行中", "object": "タスク処理"},
                {"subject": "タスク", "relation": "目標", "object": "知識グラフ更新"}
            ]"""
            
            self._log_thought("knowledge_graph_update", {
                "goal": goal,
                "result": result,
                "triples": triples_json,
                "mock_mode": True
            })
            
            try:
                import json
                triples_items = json.loads(triples_json)
                new_triples = []
                for item in triples_items:
                    s = item.get("subject", "")
                    r = item.get("relation", "")
                    o = item.get("object", "")
                    
                    if s and r and o:
                        new_triples.append((s, r, o))
                        
                if new_triples:
                    self.knowledge_triples.extend(new_triples)
                    self.graph = self.rgcn_processor.build_graph(self.knowledge_triples)
                    self.rgcn_processor.save_graph("./knowledge_graph.json")
            except Exception as e:
                print(f"モック知識グラフ更新エラー: {str(e)}")
                
            return
            
        prompt = f"""
        以下のタスクと結果から、知識グラフのトリプル（主語、関係、目的語）を抽出してください：
        
        目標：{goal}
        
        結果：
        {result}
        
        以下の形式でJSON配列として返してください：
        [
            {{"subject": "主語", "relation": "関係", "object": "目的語"}}
        ]
        """
        
        triples_json = self.llm.generate_text(prompt)
        
        try:
            import re
            import json
            json_match = re.search(r'\[\s*\{.*\}\s*\]', triples_json, re.DOTALL)
            if json_match:
                triples_items = json.loads(json_match.group(0))
            else:
                triples_items = []
                
            new_triples = []
            for item in triples_items:
                s = item.get("subject", "")
                r = item.get("relation", "")
                o = item.get("object", "")
                
                if s and r and o:
                    new_triples.append((s, r, o))
            
            if new_triples:
                self.knowledge_triples.extend(new_triples)
                
                self.knowledge_triples = list(set(self.knowledge_triples))
                
                try:
                    self.graph = self.rgcn_processor.build_graph(self.knowledge_triples)
                    self.rgcn_processor.train(self.graph, num_epochs=10)
                    
                    self._log_thought("knowledge_graph_update", {
                        "new_triples": new_triples,
                        "total_triples": len(self.knowledge_triples)
                    })
                except Exception as e:
                    print(f"R-GCN更新エラー: {str(e)}")
        except Exception as e:
            print(f"知識グラフ更新エラー: {str(e)}")
    
    def _reflect_and_improve(self, goal: str, result: str):
        """自己反省と改善"""
        if not self.coat_reasoner:
            return
            
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            mock_reflection = {
                "coat_chain": [
                    {"action": "観察", "thought": f"タスク「{goal}」の結果を観察しています。"},
                    {"action": "分析", "thought": "モックモードでは詳細な分析は行われません。"},
                    {"action": "改善", "thought": "次回は実際のAPIキーを設定して実行することで改善できます。"}
                ],
                "final_solution": "モックモードでは限定的な自己反省のみ実行されました。"
            }
            
            self.thinking_state["reflections"].append({
                "time": "after_task",
                "chain": mock_reflection.get("coat_chain", []),
                "solution": mock_reflection.get("final_solution", ""),
                "mock_mode": True
            })
            
            self._log_thought("self_reflection", {
                "goal": goal,
                "reflection_task": "モックモードでの自己反省",
                "coat_chain": mock_reflection,
                "mock_mode": True
            })
            return
            
        reflection_task = f"""
        以下のタスクとその結果を振り返り、自己反省を行ってください：
        
        目標：{goal}
        
        結果：
        {result}
        
        どのような改善が可能か、次回同様のタスクに取り組む際にどうすべきかを考えてください。
        """
        
        current_state = f"最近の知識更新: {self.thinking_state['knowledge_updates'][-3:] if self.thinking_state['knowledge_updates'] else '無し'}"
        
        coat_chain_result = self.coat_reasoner.generate_action_thought_chain(
            task_description=reflection_task,
            current_state=current_state
        )
        
        self.thinking_state["reflections"].append({
            "time": "after_task",
            "chain": coat_chain_result.get("coat_chain", []),
            "solution": coat_chain_result.get("final_solution", "")
        })
        
        self._log_thought("self_reflection", {
            "goal": goal,
            "reflection_task": reflection_task,
            "coat_chain": coat_chain_result
        })
    
    def get_thinking_state(self) -> Dict[str, Any]:
        """現在の思考状態を取得"""
        return self.thinking_state
    
    def start_continuous_thinking(self, initial_task=None, thinking_goal=None):
        """バックグラウンドスレッドで継続的思考を開始 - 目標指向版"""
        if self.thinking_thread is not None and self.thinking_thread.is_alive():
            return
            
        self.stop_thinking = False
        
        if thinking_goal:
            self.thinking_state["thinking_goal"] = thinking_goal
            self._log_thought("thinking_goal_set", {
                "goal": thinking_goal,
                "initial_task": initial_task
            })
        
        self.thinking_thread = threading.Thread(
            target=self._continuous_thinking_loop, 
            args=(initial_task, thinking_goal)
        )
        self.thinking_thread.daemon = True
        self.thinking_thread.start()
        
        print(f"バックグラウンドでの継続的思考を開始しました。目標: {thinking_goal or '一般的な改善'}")
    
    def stop_continuous_thinking(self):
        """継続的思考を停止"""
        self.stop_thinking = True
        if self.thinking_thread is not None:
            self.thinking_thread.join(timeout=2.0)
            print("継続的思考を停止しました。")
            
    def continuous_thinking(self, duration_seconds: int = 60):
        """
        指定された期間、継続的に思考を行う
        
        Args:
            duration_seconds: 思考を継続する秒数
        """
        start_time = time.time()
        
        print(f"{duration_seconds}秒間の継続思考を開始します...")
        
        while time.time() - start_time < duration_seconds:
            if self.thinking_state["current_task"]:
                self._think_about_current_task()
            else:
                self._think_about_knowledge()
                
            time.sleep(1)
            
        print("継続思考を終了します。")
    
    def _continuous_thinking_loop(self, initial_task=None, thinking_goal=None):
        """継続的思考のメインループ - 目標指向版"""
        current_task = initial_task
        
        while not self.stop_thinking:
            try:
                if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
                    print("モックモード: 継続的思考をシミュレート中...")
                    self._log_thought("mock_thinking", {
                        "timestamp": time.time(),
                        "message": "モックモードでの継続的思考をシミュレート",
                        "thinking_goal": thinking_goal
                    })
                    time.sleep(10)
                    continue
                
                try:
                    new_task = self.thinking_queue.get_nowait()
                    current_task = new_task
                    print(f"新しいタスクを受け取りました: {current_task}")
                except Empty:
                    pass
                    
                if current_task:
                    try:
                        self._think_about_current_task()
                        
                        if self._should_get_external_info():
                            self._get_external_info(current_task)
                    except Exception as e:
                        print(f"タスク思考中にエラーが発生: {str(e)}")
                        if "api key" in str(e).lower() or "auth" in str(e).lower():
                            print("APIキーエラーを検出: モックモードに切り替えます")
                            self.llm.mock_mode = True
                else:
                    try:
                        if thinking_goal:
                            self._think_about_goal_progress(thinking_goal)
                        else:
                            self._think_about_knowledge()
                    except Exception as e:
                        print(f"知識思考中にエラーが発生: {str(e)}")
                        if "api key" in str(e).lower() or "auth" in str(e).lower():
                            print("APIキーエラーを検出: モックモードに切り替えます")
                            self.llm.mock_mode = True
                
                time.sleep(2.0)
            except Exception as e:
                print(f"継続的思考ループでエラーが発生: {str(e)}")
                if "api key" in str(e).lower() or "auth" in str(e).lower():
                    print("APIキーエラーを検出: モックモードに切り替えます")
                    self.llm.mock_mode = True
                time.sleep(5.0)

    def _think_about_goal_progress(self, thinking_goal):
        """目標に向けた進捗について考える"""
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            thought = f"モックモード: 目標「{thinking_goal}」に向けた進捗思考は制限されています。"
            
            self.thinking_state["reflections"].append({
                "time": time.time(),
                "content": thought,
                "goal": thinking_goal
            })
            
            self._log_thought("goal_progress_thinking", {
                "thinking_goal": thinking_goal,
                "thought": thought,
                "mock_mode": True
            })
            
            self.thinking_state["last_thought_time"] = time.time()
            return
        
        goal_knowledge = self.get_knowledge_for_script(thinking_goal)
        
        prompt = f"""
        以下の目標に向けた進捗と改善について考えてください：
        
        目標：{thinking_goal}
        
        関連する知識：
        {self._format_knowledge_for_prompt(goal_knowledge.get("related_knowledge", []))}
        
        成功パターン：
        {self._format_knowledge_for_prompt(goal_knowledge.get("success_patterns", []))}
        
        最適化のヒント：
        {self._format_knowledge_for_prompt(goal_knowledge.get("optimization_tips", []))}
        
        この目標を達成するために：
        1. 現在の進捗状況の評価
        2. 次に取り組むべき具体的なステップ
        3. 改善可能な領域の特定
        4. 新しいアプローチや戦略の提案
        
        を含む考えを共有してください。
        """
        
        thought = self.llm.generate_text(prompt)
        
        self.thinking_state["reflections"].append({
            "time": time.time(),
            "content": thought,
            "goal": thinking_goal,
            "knowledge_used": len(goal_knowledge.get("related_knowledge", []))
        })
        
        self._log_thought("goal_progress_thinking", {
            "thinking_goal": thinking_goal,
            "thought": thought,
            "knowledge_sources_used": len(goal_knowledge.get("related_knowledge", []))
        })
        
        self.thinking_state["last_thought_time"] = time.time()
    
    def _should_get_external_info(self):
        """外部情報を取得すべきかどうかを判断"""
        import random
        return random.random() < 0.3  # 30%の確率で外部情報を取得
    
    def _get_external_info(self, task):
        """外部情報を取得"""
        try:
            result = self.web_crawler.execute(query=task)
            
            if result.success:
                web_info = result.result
                
                self._process_external_info(task, web_info)
            else:
                print(f"Web情報取得エラー: {result.error}")
        except Exception as e:
            print(f"外部情報取得エラー: {str(e)}")
    
    def _process_external_info(self, task, web_info):
        """取得した外部情報を処理"""
        if not web_info or not web_info.get("results"):
            return
            
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            print(f"モックモード: Web情報処理をスキップします。タスク: {task}")
            return
            
        results = web_info.get("results", [])
        combined_content = "\n\n".join([r.get("content", "") for r in results if r.get("content")])
        
        if not combined_content:
            return
            
        prompt = f"""
        以下のWeb検索結果から、タスク「{task}」に関連する重要な知識を抽出してください：
        
        {combined_content[:4000]}  # 長すぎる場合は切り詰め
        
        以下の形式でJSON配列として返してください：
        [
            {{"subject": "主題", "fact": "事実や知識", "confidence": 0.9}}
        ]
        """
        
        knowledge_json = self.llm.generate_text(prompt)
        
        try:
            import re
            json_match = re.search(r'\[\s*\{.*\}\s*\]', knowledge_json, re.DOTALL)
            if json_match:
                knowledge_items = json.loads(json_match.group(0))
                
                for item in knowledge_items:
                    subject = item.get("subject", "")
                    fact = item.get("fact", "")
                    confidence = item.get("confidence", 0.5)
                    
                    if subject and fact and confidence > 0.7:
                        if subject not in self.knowledge_db:
                            self.knowledge_db[subject] = {}
                        
                        self.knowledge_db[subject]["fact"] = fact
                        self.knowledge_db[subject]["confidence"] = confidence
                        self.knowledge_db[subject]["last_updated"] = time.time()
                        self.knowledge_db[subject]["source"] = "web_search"
                        
                        self._log_thought("web_knowledge_update", {
                            "subject": subject,
                            "fact": fact,
                            "confidence": confidence,
                            "source": "web_search"
                        })
                
                self._save_knowledge_db()
        except Exception as e:
            print(f"Web知識抽出エラー: {str(e)}")
    
    def _think_about_current_task(self):
        """現在のタスクについて目的指向で考える - 蓄積された知識を活用"""
        task = self.thinking_state["current_task"]
        
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            thought = "モックモード: 継続的思考は制限されています。実際のAPIコールは行われません。"
            
            self.thinking_state["reflections"].append({
                "time": time.time(),
                "content": thought
            })
            
            self._log_thought("continuous_thinking", {
                "task": task,
                "thought": thought,
                "mock_mode": True
            })
            
            self.thinking_state["last_thought_time"] = time.time()
            return
        
        related_knowledge = self.get_knowledge_for_script(task)
        
        related_insights = self._get_related_insights(task, limit=5)
        
        multi_agent_insights = related_knowledge.get("multi_agent_insights", [])
        
        prompt = f"""
        現在取り組んでいるタスクについて、蓄積された知識と経験を活用して深く考えてください：
        
        タスク：{task}
        
        関連する知識：
        {self._format_knowledge_for_prompt(related_knowledge.get("related_knowledge", []))}
        
        過去の洞察：
        {self._format_insights_for_prompt(related_insights)}
        
        マルチエージェント討論の結果：
        {self._format_multi_agent_insights_for_prompt(multi_agent_insights)}
        
        以前の考え：
        {self.thinking_state["reflections"][-1].get("content", "なし") if self.thinking_state["reflections"] else "なし"}
        
        上記の情報を踏まえて：
        1. このタスクを成功させるための新しいアプローチや改善点
        2. 過去の経験から学んだ注意すべき点
        3. 目標達成に向けた具体的な次のステップ
        
        を含む新しい考えを共有してください。
        """
        
        thought = self.llm.generate_text(prompt)
        
        self.thinking_state["reflections"].append({
            "time": time.time(),
            "content": thought,
            "knowledge_used": len(related_knowledge.get("related_knowledge", [])),
            "insights_used": len(related_insights),
            "multi_agent_insights_used": len(multi_agent_insights)
        })
        
        self._log_thought("goal_oriented_thinking", {
            "task": task,
            "thought": thought,
            "knowledge_sources": {
                "related_knowledge_count": len(related_knowledge.get("related_knowledge", [])),
                "insights_count": len(related_insights),
                "multi_agent_insights_count": len(multi_agent_insights)
            }
        })
        
        self._extract_insights_from_thought(task, thought)
        
        self.thinking_state["last_thought_time"] = time.time()
    
    def _format_knowledge_for_prompt(self, knowledge_list):
        """知識リストをプロンプト用にフォーマット"""
        if not knowledge_list:
            return "関連する知識はありません。"
        
        formatted = []
        for k in knowledge_list[:5]:
            formatted.append(f"- {k['subject']}: {k['fact']} (確信度: {k['confidence']})")
        return "\n".join(formatted)

    def _format_insights_for_prompt(self, insights_list):
        """洞察リストをプロンプト用にフォーマット"""
        if not insights_list:
            return "過去の洞察はありません。"
        
        formatted = []
        for insight in insights_list[:3]:
            content = insight.get("content", {})
            if isinstance(content, dict):
                if "insight" in content:
                    formatted.append(f"- {content['insight']}")
                elif "thought" in content:
                    formatted.append(f"- {content['thought']}")
        return "\n".join(formatted)

    def _format_multi_agent_insights_for_prompt(self, insights_list):
        """マルチエージェント洞察をプロンプト用にフォーマット"""
        if not insights_list:
            return "マルチエージェント討論の結果はありません。"
        
        formatted = []
        for insight in insights_list[:3]:
            insight_type = insight.get("type", "")
            content = insight.get("content", "")
            if insight_type == "consensus":
                formatted.append(f"- 合意点: {content}")
            elif insight_type == "agent_perspective":
                agent = insight.get("agent", "エージェント")
                formatted.append(f"- {agent}の視点: {content}")
        return "\n".join(formatted)

    def _extract_insights_from_thought(self, task, thought):
        """思考から新しい洞察を抽出して知識ベースに追加"""
        try:
            extract_prompt = f"""
            以下の思考から、将来のタスクに役立つ重要な洞察や学びを抽出してください：
            
            タスク: {task}
            思考: {thought}
            
            以下の形式でJSON配列として返してください：
            [
                {{"subject": "洞察の主題", "fact": "具体的な洞察や学び", "confidence": 0.8}}
            ]
            """
            
            insights_json = self.llm.generate_text(extract_prompt)
            
            import re
            import json
            json_match = re.search(r'\[\s*\{.*\}\s*\]', insights_json, re.DOTALL)
            if json_match:
                insights = json.loads(json_match.group(0))
                for insight in insights:
                    subject = insight.get("subject", "")
                    fact = insight.get("fact", "")
                    confidence = insight.get("confidence", 0.7)
                    
                    if subject and fact and confidence > 0.6:
                        self._update_knowledge(
                            f"思考洞察: {subject}",
                            fact,
                            confidence,
                            "continuous_thinking"
                        )
        except Exception as e:
            print(f"思考からの洞察抽出エラー: {str(e)}")
    
    def _suggest_packages_for_task(self, task_description: str) -> List[Dict[str, Any]]:
        """
        タスクの説明に基づいて適切なPythonパッケージを提案する
        
        Args:
            task_description: タスクの説明
            
        Returns:
            List[Dict]: 推奨パッケージのリスト（名前、説明、用途、信頼度を含む）
        """
        task_categories = {
            "データ分析": {
                "pandas": {
                    "description": "データ操作と分析のための高性能ライブラリ",
                    "confidence": 0.95,
                    "usage": "データフレーム操作、統計分析、データクリーニング"
                },
                "numpy": {
                    "description": "数値計算のための基本ライブラリ",
                    "confidence": 0.9,
                    "usage": "配列操作、数学関数、線形代数"
                },
                "scipy": {
                    "description": "科学技術計算のためのライブラリ",
                    "confidence": 0.8,
                    "usage": "高度な統計、最適化、信号処理"
                }
            },
            "データ可視化": {
                "matplotlib": {
                    "description": "静的でインタラクティブな可視化を作成するライブラリ",
                    "confidence": 0.9,
                    "usage": "グラフ、チャート、ヒストグラム作成"
                },
                "seaborn": {
                    "description": "統計データ可視化のための高レベルインターフェース",
                    "confidence": 0.85,
                    "usage": "複雑な統計プロット、ヒートマップ、ペアプロット"
                },
                "plotly": {
                    "description": "インタラクティブな可視化ライブラリ",
                    "confidence": 0.8,
                    "usage": "インタラクティブグラフ、ダッシュボード"
                }
            },
            "機械学習": {
                "scikit-learn": {
                    "description": "機械学習アルゴリズムとツールのコレクション",
                    "confidence": 0.9,
                    "usage": "分類、回帰、クラスタリング、次元削減"
                },
                "tensorflow": {
                    "description": "深層学習フレームワーク",
                    "confidence": 0.85,
                    "usage": "ニューラルネットワーク、深層学習モデル"
                },
                "pytorch": {
                    "description": "柔軟な深層学習フレームワーク",
                    "confidence": 0.85,
                    "usage": "研究向け深層学習、動的計算グラフ"
                }
            },
            "ウェブスクレイピング": {
                "requests": {
                    "description": "HTTPリクエストを簡単に行うためのライブラリ",
                    "confidence": 0.9,
                    "usage": "APIリクエスト、ウェブページ取得"
                },
                "beautifulsoup4": {
                    "description": "HTMLとXMLの解析ライブラリ",
                    "confidence": 0.9,
                    "usage": "ウェブページからのデータ抽出"
                },
                "selenium": {
                    "description": "ブラウザ自動化ライブラリ",
                    "confidence": 0.8,
                    "usage": "動的ウェブページのスクレイピング"
                }
            },
            "自然言語処理": {
                "nltk": {
                    "description": "自然言語処理ツールキット",
                    "confidence": 0.85,
                    "usage": "テキスト処理、トークン化、ステミング"
                },
                "spacy": {
                    "description": "高度な自然言語処理ライブラリ",
                    "confidence": 0.85,
                    "usage": "品詞タグ付け、固有表現認識、依存構文解析"
                },
                "transformers": {
                    "description": "最先端の自然言語処理モデル",
                    "confidence": 0.8,
                    "usage": "BERT、GPT、T5などの事前学習済みモデル"
                }
            },
            "株価データ": {
                "yfinance": {
                    "description": "Yahoo Financeからの株価データ取得ライブラリ",
                    "confidence": 0.9,
                    "usage": "株価履歴データ、企業情報の取得"
                },
                "pandas-datareader": {
                    "description": "様々なソースからの金融データ取得ライブラリ",
                    "confidence": 0.85,
                    "usage": "株価、為替レート、経済指標の取得"
                },
                "alpha-vantage": {
                    "description": "Alpha Vantage APIのPythonラッパー",
                    "confidence": 0.8,
                    "usage": "リアルタイム株価、テクニカル指標"
                }
            }
        }
        
        keywords = self._extract_keywords_from_text(task_description)
        
        category_scores = {}
        for category in task_categories:
            score = 0
            for keyword in keywords:
                if keyword.lower() in category.lower():
                    score += 3  # カテゴリ名に直接マッチする場合は高いスコア
                
                for package, details in task_categories[category].items():
                    if keyword.lower() in details["description"].lower() or keyword.lower() in details["usage"].lower():
                        score += 1
            
            if score > 0:
                category_scores[category] = score
        
        special_keywords = {
            "株価": ["株価データ", "データ分析", "データ可視化"],
            "グラフ": ["データ可視化", "データ分析"],
            "チャート": ["データ可視化"],
            "予測": ["機械学習", "データ分析"],
            "分類": ["機械学習"],
            "テキスト": ["自然言語処理"],
            "言語": ["自然言語処理"],
            "ウェブ": ["ウェブスクレイピング"],
            "スクレイピング": ["ウェブスクレイピング"],
            "クローリング": ["ウェブスクレイピング"]
        }
        
        for keyword in keywords:
            for special_keyword, categories in special_keywords.items():
                if special_keyword in keyword.lower():
                    for category in categories:
                        category_scores[category] = category_scores.get(category, 0) + 2
        
        japanese_keywords = {
            "株": ["株価データ", "データ分析"],
            "日経": ["株価データ"],
            "証券": ["株価データ"],
            "金融": ["株価データ"],
            "分析": ["データ分析"],
            "可視化": ["データ可視化"],
            "機械学習": ["機械学習"],
            "自然言語": ["自然言語処理"],
            "ウェブ": ["ウェブスクレイピング"]
        }
        
        for keyword in keywords:
            for jp_keyword, categories in japanese_keywords.items():
                if jp_keyword in keyword.lower():
                    for category in categories:
                        category_scores[category] = category_scores.get(category, 0) + 3
        
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        recommended_packages = []
        added_packages = set()
        
        for category, score in sorted_categories[:3]:
            if category in task_categories:
                sorted_packages = sorted(
                    task_categories[category].items(),
                    key=lambda x: x[1]["confidence"],
                    reverse=True
                )
                
                for package_name, details in sorted_packages[:2]:
                    if package_name not in added_packages:
                        recommended_packages.append({
                            "name": package_name,
                            "description": details["description"],
                            "usage": details["usage"],
                            "confidence": details["confidence"] * (score / 10 if score > 10 else 1)  # スコアに基づいて信頼度を調整
                        })
                        added_packages.add(package_name)
        
        if "株価" in task_description.lower() or "日経" in task_description.lower():
            if "yfinance" not in added_packages:
                recommended_packages.append({
                    "name": "yfinance",
                    "description": "Yahoo Financeからの株価データ取得ライブラリ",
                    "usage": "株価履歴データ、企業情報の取得",
                    "confidence": 0.95
                })
                added_packages.add("yfinance")
        
        if "pandas" not in added_packages and len(recommended_packages) > 0:
            recommended_packages.append({
                "name": "pandas",
                "description": "データ操作と分析のための高性能ライブラリ",
                "usage": "データフレーム操作、統計分析、データクリーニング",
                "confidence": 0.9
            })
        
        verified_packages = []
        for package in recommended_packages:
            try:
                import requests
                response = requests.get(f"https://pypi.org/pypi/{package['name']}/json", timeout=5)
                if response.status_code == 200:
                    package_info = response.json()
                    if "info" in package_info:
                        package["pypi_description"] = package_info["info"].get("summary", "")
                        package["pypi_version"] = package_info["info"].get("version", "")
                    verified_packages.append(package)
                    self._log_thought("package_verification_success", {
                        "package": package["name"],
                        "exists_on_pypi": True
                    })
            except Exception as e:
                self._log_thought("package_verification_error", {
                    "package": package["name"],
                    "error": str(e)
                })
        
        return verified_packages
    
    def get_knowledge_for_script(self, task_description: str, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        スクリプト生成用の知識を提供 - 強化版
        
        Args:
            task_description: タスクの説明
            keywords: 検索キーワード
            
        Returns:
            Dict: スクリプト生成に役立つ知識情報
        """
        result = {
            "task": task_description,
            "related_knowledge": [],
            "thinking_insights": [],
            "hypotheses": [],
            "multi_agent_insights": [],
            "recommended_packages": [],
            "success_patterns": [],
            "failure_patterns": [],
            "optimization_tips": []
        }
        
        if not keywords:
            keywords = self._extract_keywords_from_text(task_description)
        
        recommended_packages = self._suggest_packages_for_task(task_description)
        result["recommended_packages"] = recommended_packages
        
        self._log_thought("package_recommendations", {
            "task": task_description,
            "recommended_packages": [p["name"] for p in recommended_packages],
            "package_count": len(recommended_packages)
        })
        
        for subject, data in self.knowledge_db.items():
            fact = data.get("fact", "")
            confidence = data.get("confidence", 0.0)
            
            is_relevant = False
            for keyword in keywords:
                if keyword.lower() in subject.lower() or keyword.lower() in fact.lower():
                    is_relevant = True
                    break
            
            if is_relevant:
                knowledge_item = {
                    "subject": subject,
                    "fact": fact,
                    "confidence": confidence,
                    "last_updated": data.get("last_updated", 0),
                    "source": data.get("source", "unknown")
                }
                
                if "[success_factor]" in subject:
                    result["success_patterns"].append(knowledge_item)
                elif "[failure_factor]" in subject:
                    result["failure_patterns"].append(knowledge_item)
                elif "[optimization]" in subject:
                    result["optimization_tips"].append(knowledge_item)
                else:
                    result["related_knowledge"].append(knowledge_item)
        
        related_insights = self._get_enhanced_related_insights(task_description, limit=10)
        result["thinking_insights"] = related_insights
        
        for insight in related_insights:
            if insight.get("type") == "task_hypothesis":
                content = insight.get("content", {})
                if isinstance(content, dict) and "hypothesis" in content:
                    result["hypotheses"].append({
                        "content": content["hypothesis"],
                        "confidence": content.get("confidence", 0.6),
                        "timestamp": insight.get("timestamp", 0)
                    })
        
        if self.enable_multi_agent and self.multi_agent_discussion:
            try:
                discussion_result = self.multi_agent_discussion.conduct_discussion(
                    topic=f"「{task_description}」に関する仮説と解決アプローチ",
                    rounds=2
                )
                
                if discussion_result:
                    if "consensus" in discussion_result:
                        result["multi_agent_insights"].append({
                            "type": "consensus",
                            "content": discussion_result["consensus"],
                            "confidence": 0.85
                        })
                    
                    if "responses" in discussion_result:
                        for agent_name, response in discussion_result["responses"].items():
                            result["multi_agent_insights"].append({
                                "type": "agent_perspective",
                                "agent": agent_name,
                                "content": response,
                                "confidence": 0.75
                            })
                    
                    if "consensus" in discussion_result:
                        self._update_knowledge(
                            f"マルチエージェント討論: {task_description[:30]}",
                            discussion_result["consensus"],
                            0.85,
                            "multi_agent_discussion"
                        )
            except Exception as e:
                self._log_thought("multi_agent_discussion_error", {
                    "task": task_description,
                    "error": str(e)
                })
        
        self._log_thought("enhanced_knowledge_for_script", {
            "task": task_description,
            "knowledge_count": len(result["related_knowledge"]),
            "success_patterns_count": len(result["success_patterns"]),
            "failure_patterns_count": len(result["failure_patterns"]),
            "optimization_tips_count": len(result["optimization_tips"]),
            "insights_count": len(result["thinking_insights"]),
            "hypotheses_count": len(result["hypotheses"]),
            "multi_agent_insights_count": len(result["multi_agent_insights"]),
            "recommended_packages_count": len(result["recommended_packages"])
        })
        
        return result

    def _get_enhanced_related_insights(self, text: str, limit: int = 10) -> List[Dict]:
        """関連する洞察を取得 - 強化版"""
        insights = []
        try:
            log_path = self.log_path
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    keywords = self._extract_keywords_from_text(text)
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_type = entry.get("type")
                            
                            if entry_type in [
                                "task_insight", "hypothesis_verification", "task_conclusion",
                                "goal_oriented_thinking", "enhanced_task_result_integration",
                                "multi_agent_discussion", "knowledge_reflection"
                            ]:
                                content = entry.get("content", {})
                                content_text = json.dumps(content, ensure_ascii=False).lower()
                                
                                for keyword in keywords:
                                    if keyword in content_text:
                                        insights.append({
                                            "type": entry_type,
                                            "timestamp": entry.get("timestamp"),
                                            "content": content
                                        })
                                        break
                                        
                                if len(insights) >= limit:
                                    break
                        except:
                            continue
        except Exception as e:
            self._log_thought("get_enhanced_related_insights_error", {
                "error": str(e)
            })
            
        return insights
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """テキストからキーワードを抽出"""
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) > 3]
    
    def integrate_task_results(self, goal: str, result: str) -> bool:
        """
        タスク実行結果を知識ベースに統合する - 強化版
        
        Args:
            goal: タスクの目標
            result: タスク実行の結果
            
        Returns:
            bool: 統合が成功したかどうか
        """
        if not result:
            return False
            
        try:
            if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
                knowledge_items = [{
                    "subject": f"タスク結果: {goal[:30]}",
                    "fact": f"モックモードでタスクが実行されました: {result[:100]}",
                    "confidence": 0.7,
                    "category": "general"
                }]
            else:
                extraction_prompt = f"""
                以下のタスクとその実行結果から、将来のタスクに役立つ知識を抽出してください：
                
                目標: {goal}
                結果: {result}
                
                以下の観点から知識を抽出してください：
                1. 成功要因や失敗要因
                2. 使用した手法やアプローチの効果
                3. 遭遇した問題とその解決方法
                4. 改善可能な点や最適化のヒント
                5. 類似タスクに適用できる一般的な原則
                
                以下の形式でJSON配列として返してください：
                [
                    {{
                        "subject": "知識の主題",
                        "fact": "具体的な知識や洞察",
                        "confidence": 0.8,
                        "category": "success_factor|failure_factor|method|problem_solution|optimization|general_principle"
                    }}
                ]
                """
                
                knowledge_json = self.llm.generate_text(extraction_prompt)
                
                import re
                import json
                json_match = re.search(r'\[\s*\{.*\}\s*\]', knowledge_json, re.DOTALL)
                if json_match:
                    knowledge_items = json.loads(json_match.group(0))
                else:
                    knowledge_items = self._basic_result_integration(goal, result)
            
            integrated_count = 0
            for item in knowledge_items:
                subject = item.get("subject", "")
                fact = item.get("fact", "")
                confidence = item.get("confidence", 0.7)
                category = item.get("category", "general")
                
                if subject and fact and confidence > 0.6:
                    enhanced_subject = f"[{category}] {subject}"
                    
                    success = self._update_knowledge(
                        enhanced_subject,
                        fact,
                        confidence,
                        "enhanced_task_result_integration"
                    )
                    
                    if success:
                        integrated_count += 1
            
            self._log_thought("enhanced_task_result_integration", {
                "goal": goal,
                "result_length": len(result),
                "extracted_knowledge_count": len(knowledge_items),
                "integrated_knowledge_count": integrated_count,
                "integration_method": "llm_enhanced" if not (hasattr(self.llm, 'mock_mode') and self.llm.mock_mode) else "mock_mode"
            })
            
            self._analyze_task_relationships(goal, result, knowledge_items)
            
            return integrated_count > 0
            
        except Exception as e:
            self._log_thought("task_result_integration_error", {
                "goal": goal,
                "error": str(e)
            })
            return False

    def _basic_result_integration(self, goal: str, result: str) -> List[Dict]:
        """基本的な結果統合（フォールバック用）"""
        knowledge_items = []
        
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (str, int, float, bool)):
                    subject = f"{goal[:30]} - {key}"
                    fact = str(value)
                    knowledge_items.append({
                        "subject": subject,
                        "fact": fact,
                        "confidence": 0.7,
                        "category": "general"
                    })
        elif isinstance(result, str):
            lines = result.split('\n')
            for line in lines:
                if ':' in line and len(line) > 10:
                    parts = line.split(':', 1)
                    subject = f"{goal[:30]} - {parts[0].strip()}"
                    fact = parts[1].strip()
                    knowledge_items.append({
                        "subject": subject,
                        "fact": fact,
                        "confidence": 0.7,
                        "category": "general"
                    })
        
        return knowledge_items

    def _analyze_task_relationships(self, goal: str, result: str, knowledge_items: List[Dict]):
        """タスク間の関連性を分析"""
        try:
            keywords = self._extract_keywords_from_text(goal)
            related_tasks = []
            
            for subject, data in self.knowledge_db.items():
                if any(keyword.lower() in subject.lower() for keyword in keywords):
                    related_tasks.append({
                        "subject": subject,
                        "fact": data.get("fact", ""),
                        "confidence": data.get("confidence", 0)
                    })
            
            if related_tasks:
                self._log_thought("task_relationship_analysis", {
                    "current_goal": goal,
                    "related_tasks_count": len(related_tasks),
                    "new_knowledge_count": len(knowledge_items),
                    "analysis": f"Found {len(related_tasks)} related tasks in knowledge base"
                })
                
        except Exception as e:
            print(f"タスク関連性分析エラー: {str(e)}")
    
    def _get_related_insights(self, text: str, limit: int = 5) -> List[Dict]:
        """関連する洞察を取得"""
        insights = []
        try:
            log_path = self.log_path
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    keywords = self._extract_keywords_from_text(text)
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get("type") in ["task_insight", "hypothesis_verification", "task_conclusion"]:
                                content = entry.get("content", {})
                                content_text = json.dumps(content, ensure_ascii=False).lower()
                                
                                for keyword in keywords:
                                    if keyword in content_text:
                                        insights.append({
                                            "type": entry.get("type"),
                                            "timestamp": entry.get("timestamp"),
                                            "content": content
                                        })
                                        break
                                        
                                if len(insights) >= limit:
                                    break
                        except:
                            continue
        except Exception as e:
            self._log_thought("get_related_insights_error", {
                "error": str(e)
            })
            
        return insights
    
    def _update_knowledge(self, subject: str, fact: str, confidence: float, source: str = "thinking"):
        """
        知識データベースを更新する
        
        Args:
            subject: 知識の主題
            fact: 事実や情報
            confidence: 確信度 (0.0-1.0)
            source: 知識の出所
        """
        if not subject or not fact:
            return False
            
        self.knowledge_db[subject] = {
            "fact": fact,
            "confidence": confidence,
            "last_updated": time.time(),
            "source": source
        }
        
        self._save_knowledge_db()
        
        if hasattr(self, '_knowledge_graph') and getattr(self, '_knowledge_graph', None) is not None:
            try:
                self._update_knowledge_graph(subject, fact)
            except Exception as e:
                self._log_thought("knowledge_graph_update_error", {
                    "subject": subject,
                    "error": str(e)
                })
                
        return True
        
    def _think_about_knowledge(self):
        """現在の知識ベースについて考える"""
        import random
        
        if not self.knowledge_db:
            return
            
        subjects = list(self.knowledge_db.keys())
        if not subjects:
            return
        
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            subject = random.choice(subjects) if subjects else "モックサブジェクト"
            thought = "モックモード: 知識ベース考察は制限されています。実際のAPIコールは行われません。"
            
            self.thinking_state["reflections"].append({
                "time": time.time(),
                "subject": subject,
                "content": thought
            })
            
            self._log_thought("knowledge_reflection", {
                "subject": subject,
                "fact": "モックモード",
                "thought": thought,
                "mock_mode": True
            })
            
            self.thinking_state["last_thought_time"] = time.time()
            return
            
        subject = random.choice(subjects)
        fact = self.knowledge_db[subject].get("fact", "")
        
        prompt = f"""
        以下の知識についてさらに考察してください：
        
        主題：{subject}
        事実：{fact}
        
        この知識に関連する新しい洞察や、これを発展させる考えを短く共有してください。
        """
        
        thought = self.llm.generate_text(prompt)
        
        self.thinking_state["reflections"].append({
            "time": time.time(),
            "subject": subject,
            "content": thought
        })
        
        self._log_thought("knowledge_reflection", {
            "subject": subject,
            "fact": fact,
            "thought": thought
        })
        
        self.thinking_state["last_thought_time"] = time.time()
