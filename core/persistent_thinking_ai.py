from typing import Dict, List, Any, Optional, Tuple, Union
import os
import json
import time

from .llm import LLM
from .rome_model_editor import ROMEModelEditor, EditRequest
from .coat_reasoner import COATReasoner
from .rgcn_processor import RGCNProcessor
from .auto_plan_agent import AutoPlanAgent
from .task_database import TaskDatabase

class PersistentThinkingAI:
    """
    持続思考型AI - ROME、COAT、R-GCNを統合した自律的思考システム
    
    持続思考型AIは：
    1. 常に考え続ける（タスク完了後も思考を継続）
    2. 知識を蓄積し、修正する（ROMEを使用）
    3. 自己反省を行う（COATを使用）
    4. 知識グラフでコンテクストを強化する（R-GCNを使用）
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/phi-2",
        workspace_dir: str = "./workspace",
        device: Optional[str] = None,
        knowledge_db_path: str = "./knowledge_db.json",
        log_path: str = "./thinking_log.jsonl",
        use_compatibility_mode: bool = False
    ):
        """
        持続思考型AIの初期化
        
        Args:
            model_name: 使用するローカルモデル名
            workspace_dir: 作業ディレクトリ
            device: 使用するデバイス（'cuda', 'mps', 'cpu'）
            knowledge_db_path: 知識データベースのパス
            log_path: 思考ログのパス
            use_compatibility_mode: DGL/PyTorch非依存の互換モードを使用するかどうか
        """
        api_key = os.environ.get("OPENAI_API_KEY", "dummy_key_for_testing")
        
        self.use_compatibility_mode = use_compatibility_mode
        
        self.llm = LLM(
            api_key=api_key,
            model="gpt-3.5-turbo",  # 現在のLLMクラスで利用可能なモデル
            temperature=0.7
        )
        
        self.rome_model_editor = ROMEModelEditor(device=device)
        
        self.coat_reasoner = COATReasoner(self.llm)
        
        self.rgcn_processor = RGCNProcessor(device=device, use_compatibility_mode=self.use_compatibility_mode)
        
        self.task_db = TaskDatabase(":memory:")
        self.agent = AutoPlanAgent(
            name="PersistentThinkingAgent",
            description="持続的に思考し、自己改善する自律エージェント",
            llm=self.llm,
            task_db=self.task_db,
            workspace_dir=workspace_dir
        )
        
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
        
        self._reflect_before_task(goal)
        
        result = self.agent.execute_plan(goal)
        
        self._continuous_thinking_after_task(goal, result)
        
        return result
    
    def _reflect_before_task(self, goal: str):
        """タスク実行前の自己反省"""
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
    
    def _extract_and_store_knowledge(self, goal: str, result: str):
        """新しい知識を抽出して保存"""
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
    
    def _think_about_current_task(self):
        """現在のタスクについて考える"""
        task = self.thinking_state["current_task"]
        
        prompt = f"""
        現在取り組んでいるタスクについて、新たな視点や考え方はありますか？
        
        タスク：{task}
        
        以前の考え：
        {self.thinking_state["reflections"][-1].get("content", self.thinking_state["reflections"][-1].get("solution", "なし")) if self.thinking_state["reflections"] else "なし"}
        
        新しい考えを短く共有してください。
        """
        
        thought = self.llm.generate_text(prompt)
        
        self.thinking_state["reflections"].append({
            "time": time.time(),
            "content": thought
        })
        
        self._log_thought("continuous_thinking", {
            "task": task,
            "thought": thought
        })
        
        self.thinking_state["last_thought_time"] = time.time()
    
    def _think_about_knowledge(self):
        """現在の知識ベースについて考える"""
        import random
        
        if not self.knowledge_db:
            return
            
        subjects = list(self.knowledge_db.keys())
        if not subjects:
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
