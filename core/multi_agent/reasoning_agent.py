from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid
import traceback

from .agent_base import MultiAgentBase, AgentRole, AgentMessage
from ..coat_reasoner import COATReasoner

class ReasoningAgent(MultiAgentBase):
    """
    推論を担当するエージェント
    
    COATを使用した自己反省型の推論を行う
    """
    
    def __init__(
        self,
        agent_id: str = "reasoning_agent",
        name: str = "推論エージェント",
        description: str = "自己反省型の推論を行い、問題解決を支援する",
        llm=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        推論エージェントの初期化
        
        Args:
            agent_id: エージェントID
            name: エージェント名
            description: エージェントの説明
            llm: 使用するLLMインスタンス
            config: 設定情報
        """
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.MAIN_REASONING,
            name=name,
            description=description,
            llm=llm
        )
        
        self.config = config or {}
        self.mock_mode = self.config.get("mock_mode", False)
        self.task_processing_errors = {}  # タスク処理エラーを追跡
        self.reasoning_history = []  # 推論履歴
        self.active_tasks = {}  # 処理中のタスクを追跡
        
        if self.mock_mode:
            print(f"推論エージェント '{agent_id}' はモックモードで動作中です")
            self.coat_reasoner = None
        else:
            self.coat_reasoner = COATReasoner(llm) if llm else None
            
        self.reasoning_history = []
        self.task_processing_errors = {}
        
    def generate_reasoning_chain(
        self, 
        task_description: str,
        current_state: str = "",
        max_steps: int = 5
    ) -> Dict[str, Any]:
        """
        推論チェーンを生成
        
        Args:
            task_description: タスクの説明
            current_state: 現在の状態
            max_steps: 最大ステップ数
            
        Returns:
            生成された推論チェーンと最終解決策を含む辞書
        """
        if not self.coat_reasoner:
            return {"error": "COATReasonerが初期化されていません"}
            
        result = self.coat_reasoner.generate_action_thought_chain(
            task_description=task_description,
            current_state=current_state,
            max_steps=max_steps
        )
        
        self.reasoning_history.append({
            "task": task_description,
            "result": result,
            "timestamp": time.time()
        })
        
        return result
    
    def fix_code_with_reasoning(
        self,
        code: str,
        error_message: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        推論を使用してコードを修正
        
        Args:
            code: 修正対象のコード
            error_message: エラーメッセージ
            
        Returns:
            修正されたコードと推論チェーンのタプル
        """
        if not self.coat_reasoner:
            return code, []
            
        fixed_code, coat_chain = self.coat_reasoner.apply_coat_reasoning(
            code=code,
            error_message=error_message
        )
        
        return fixed_code, coat_chain
    
    def analyze_problem(self, problem_description: str) -> Dict[str, Any]:
        """
        問題を分析
        
        Args:
            problem_description: 問題の説明
            
        Returns:
            分析結果
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        prompt = f"""
        以下の問題を分析し、解決策を提案してください：
        
        {problem_description}
        
        以下の形式で回答してください：
        
        問題の理解: [問題の本質的な理解]
        課題: [解決すべき主要な課題]
        解決策: [提案する解決策]
        次のステップ: [実行すべき具体的なステップ]
        """
        
        analysis = self.llm.generate_text(prompt)
        
        result = {}
        
        for line in analysis.split('\n'):
            line = line.strip()
            if line.startswith("問題の理解:"):
                result["understanding"] = line[len("問題の理解:"):].strip()
            elif line.startswith("課題:"):
                result["challenges"] = line[len("課題:"):].strip()
            elif line.startswith("解決策:"):
                result["solution"] = line[len("解決策:"):].strip()
            elif line.startswith("次のステップ:"):
                result["next_steps"] = line[len("次のステップ:"):].strip()
        
        return result
    
    def generate_plan(self, goal: str, context: str = "") -> Dict[str, Any]:
        """
        目標達成のための計画を生成
        
        Args:
            goal: 達成する目標
            context: 追加コンテキスト
            
        Returns:
            生成された計画
        """
        if not self.llm:
            return {"error": "LLMが初期化されていません"}
            
        prompt = f"""
        以下の目標を達成するための計画を作成してください：
        
        目標: {goal}
        
        コンテキスト:
        {context}
        
        以下の形式でJSON配列として返してください：
        {{
            "title": "計画のタイトル",
            "description": "計画の説明",
            "steps": [
                {{"id": 1, "name": "ステップ1", "description": "ステップ1の説明"}},
                {{"id": 2, "name": "ステップ2", "description": "ステップ2の説明"}}
            ]
        }}
        """
        
        plan_json = self.llm.generate_text(prompt)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', plan_json, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
                return plan
            else:
                return {"error": "計画のJSONパースに失敗しました"}
        except Exception as e:
            return {"error": f"計画の生成エラー: {str(e)}"}
    
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
            is_retry = metadata.get("retry", False)
            retry_count = metadata.get("retry_count", 0)
            
            if is_retry:
                print(f"推論エージェント: タスク '{task_id}' (タイプ: {task_type}) の再処理を開始します (再試行回数: {retry_count})")
            else:
                print(f"推論エージェント: タスク '{task_id}' (タイプ: {task_type}) の処理を開始します")
            
            if task_id in self.active_tasks:
                current_status = self.active_tasks[task_id].get("status")
                start_time = self.active_tasks[task_id].get("start_time", time.time())
                elapsed = time.time() - start_time
                
                print(f"推論エージェント: タスク '{task_id}' は既に処理中です (状態: {current_status}, 経過時間: {elapsed:.1f}秒)")
                
                if current_status == "completed" and "result" in self.active_tasks[task_id]:
                    print(f"推論エージェント: タスク '{task_id}' は既に完了しています。結果を再送信します。")
                    result = self.active_tasks[task_id]["result"]
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=result,
                        message_type="task_result",
                        metadata={"task_id": task_id, "resent": True}
                    )
                    print(f"推論エージェント: タスク '{task_id}' の結果を再送信しました")
                    responses.append(response)
                    return responses
                
                if current_status == "processing" and elapsed > 10.0:
                    print(f"推論エージェント: タスク '{task_id}' は10秒以上処理中のままです。強制的に完了させます。")
                    
                    mock_result = self._generate_mock_result(task_type, message.content)
                    mock_result["forced_completion"] = True
                    mock_result["processing_time"] = elapsed
                    
                    self.active_tasks[task_id]["status"] = "completed"
                    self.active_tasks[task_id]["end_time"] = time.time()
                    self.active_tasks[task_id]["result"] = mock_result
                    
                    self.reasoning_history.append({
                        "task_id": task_id,
                        "task_type": task_type,
                        "timestamp": time.time(),
                        "result": mock_result,
                        "forced_completion": True
                    })
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=mock_result,
                        message_type="task_result",
                        metadata={"task_id": task_id, "forced_completion": True}
                    )
                    print(f"推論エージェント: タスク '{task_id}' の強制完了結果を送信しました")
                    responses.append(response)
                    return responses
            
            self.active_tasks[task_id] = {
                "type": task_type,
                "content": message.content,
                "start_time": time.time(),
                "sender_id": message.sender_id,
                "status": "processing",
                "step": "initialized",
                "is_retry": is_retry,
                "retry_count": retry_count
            }
            
            def update_step(step_name):
                if task_id in self.active_tasks:
                    self.active_tasks[task_id]["step"] = step_name
                    self.active_tasks[task_id]["last_update"] = time.time()
                    print(f"推論エージェント: タスク '{task_id}' の処理ステップを '{step_name}' に更新しました")
            
            try:
                update_step("starting")
                
                if self.mock_mode:
                    print(f"推論エージェント: モックモードでタスク '{task_id}' を処理します")
                    
                    processing_time = 0.5 + (hash(task_id) % 5) * 0.1  # 0.5〜0.9秒のランダムな処理時間
                    print(f"推論エージェント: モック処理時間 {processing_time:.1f}秒をシミュレート")
                    
                    update_step("processing")
                    time.sleep(processing_time * 0.5)
                    
                    update_step("finalizing")
                    time.sleep(processing_time * 0.5)
                    
                    mock_result = self._generate_mock_result(task_type, message.content)
                    mock_result["processing_time"] = processing_time
                    mock_result["task_id"] = task_id
                    
                    self.active_tasks[task_id]["status"] = "completed"
                    self.active_tasks[task_id]["end_time"] = time.time()
                    self.active_tasks[task_id]["result"] = mock_result
                    
                    self.reasoning_history.append({
                        "task_id": task_id,
                        "task_type": task_type,
                        "timestamp": time.time(),
                        "result": mock_result,
                        "is_mock": True,
                        "processing_time": processing_time
                    })
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=mock_result,
                        message_type="task_result",
                        metadata={"task_id": task_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' のモック結果を送信しました (処理時間: {processing_time:.1f}秒)")
                    responses.append(response)
                    return responses
                
                if task_type == "reasoning_chain":
                    content = message.content
                    task_description = content.get("task_description", "")
                    current_state = content.get("current_state", "")
                    max_steps = content.get("max_steps", 5)
                    
                    print(f"推論エージェント: 推論チェーンを生成します: '{task_description[:50]}...'")
                    
                    result = self.generate_reasoning_chain(
                        task_description=task_description,
                        current_state=current_state,
                        max_steps=max_steps
                    )
                    
                    self.active_tasks[task_id]["status"] = "completed"
                    self.active_tasks[task_id]["end_time"] = time.time()
                    self.active_tasks[task_id]["result"] = result
                    
                    self.reasoning_history.append({
                        "task_id": task_id,
                        "task_type": task_type,
                        "timestamp": time.time(),
                        "result": result
                    })
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=result,
                        message_type="task_result",
                        metadata={"task_id": task_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' の推論チェーン結果を送信しました")
                    responses.append(response)
                    
                elif task_type == "fix_code":
                    content = message.content
                    code = content.get("code", "")
                    error_message = content.get("error_message", "")
                    
                    print(f"推論エージェント: コード修正を行います: エラー '{error_message[:50]}...'")
                    
                    fixed_code, coat_chain = self.fix_code_with_reasoning(
                        code=code,
                        error_message=error_message
                    )
                    
                    result = {
                        "fixed_code": fixed_code,
                        "reasoning_chain": coat_chain
                    }
                    
                    self.active_tasks[task_id]["status"] = "completed"
                    self.active_tasks[task_id]["end_time"] = time.time()
                    self.active_tasks[task_id]["result"] = result
                    
                    self.reasoning_history.append({
                        "task_id": task_id,
                        "task_type": task_type,
                        "timestamp": time.time(),
                        "result": result
                    })
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=result,
                        message_type="task_result",
                        metadata={"task_id": task_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' のコード修正結果を送信しました")
                    responses.append(response)
                    
                elif task_type == "analyze_problem":
                    content = message.content
                    problem_description = content.get("problem_description", "")
                    
                    print(f"推論エージェント: 問題分析を行います: '{problem_description[:50]}...'")
                    
                    analysis = self.analyze_problem(problem_description)
                    
                    self.active_tasks[task_id]["status"] = "completed"
                    self.active_tasks[task_id]["end_time"] = time.time()
                    self.active_tasks[task_id]["result"] = analysis
                    
                    self.reasoning_history.append({
                        "task_id": task_id,
                        "task_type": task_type,
                        "timestamp": time.time(),
                        "result": analysis
                    })
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=analysis,
                        message_type="task_result",
                        metadata={"task_id": task_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' の問題分析結果を送信しました")
                    responses.append(response)
                    
                elif task_type == "analyze_task":
                    content = message.content
                    description = content.get("description", "")
                    
                    print(f"推論エージェント: タスク分析を行います: '{description[:50]}...'")
                    
                    analysis_result = {}
                    
                    if self.llm:
                        prompt = f"""
                        以下のタスクを分析し、必要なツールと複雑さを評価してください：
                        
                        タスク: {description}
                        
                        以下の形式で回答してください：
                        
                        タスクタイプ: [web_search/code_generation/analysis/general]
                        複雑さ: [low/medium/high]
                        必要なツール: [ツールのリスト（例: web_crawler, python_execute）]
                        """
                        
                        analysis_text = self.llm.generate_text(prompt)
                        
                        for line in analysis_text.split('\n'):
                            line = line.strip()
                            if line.startswith("タスクタイプ:"):
                                analysis_result["task_type"] = line[len("タスクタイプ:"):].strip()
                            elif line.startswith("複雑さ:"):
                                analysis_result["complexity"] = line[len("複雑さ:"):].strip()
                            elif line.startswith("必要なツール:"):
                                tools_str = line[len("必要なツール:"):].strip()
                                analysis_result["required_tools"] = [t.strip() for t in tools_str.split(',')]
                    else:
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
                    
                    self.active_tasks[task_id]["status"] = "completed"
                    self.active_tasks[task_id]["end_time"] = time.time()
                    self.active_tasks[task_id]["result"] = analysis_result
                    
                    self.reasoning_history.append({
                        "task_id": task_id,
                        "task_type": task_type,
                        "timestamp": time.time(),
                        "result": analysis_result
                    })
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=analysis_result,
                        message_type="task_result",
                        metadata={"task_id": task_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' のタスク分析結果を送信しました")
                    responses.append(response)
                    
                elif task_type == "generate_plan":
                    content = message.content
                    goal = content.get("goal", "")
                    context = content.get("context", "")
                    
                    print(f"推論エージェント: 計画生成を行います: '{goal[:50]}...'")
                    
                    plan = self.generate_plan(goal, context)
                    
                    self.active_tasks[task_id]["status"] = "completed"
                    self.active_tasks[task_id]["end_time"] = time.time()
                    self.active_tasks[task_id]["result"] = plan
                    
                    self.reasoning_history.append({
                        "task_id": task_id,
                        "task_type": task_type,
                        "timestamp": time.time(),
                        "result": plan
                    })
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=plan,
                        message_type="task_result",
                        metadata={"task_id": task_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' の計画生成結果を送信しました")
                    responses.append(response)
                else:
                    print(f"推論エージェント: 未知のタスクタイプ '{task_type}' です。デフォルト応答を生成します。")
                    
                    default_response = {
                        "success": False,
                        "error": f"未知のタスクタイプ: {task_type}",
                        "message": "このタスクタイプは推論エージェントでは処理できません。"
                    }
                    
                    self.active_tasks[task_id]["status"] = "completed"
                    self.active_tasks[task_id]["end_time"] = time.time()
                    self.active_tasks[task_id]["result"] = default_response
                    
                    self.reasoning_history.append({
                        "task_id": task_id,
                        "task_type": task_type,
                        "timestamp": time.time(),
                        "result": default_response
                    })
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=default_response,
                        message_type="task_result",
                        metadata={"task_id": task_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' のデフォルト応答を送信しました")
                    responses.append(response)
                
            except Exception as e:
                error_message = str(e)
                stack_trace = traceback.format_exc()
                print(f"推論エージェント: タスク '{task_id}' の処理中にエラーが発生しました: {error_message}")
                print(f"スタックトレース:\n{stack_trace}")
                
                self.task_processing_errors[task_id] = {
                    "error": error_message,
                    "stack_trace": stack_trace,
                    "timestamp": time.time()
                }
                
                error_response = {
                    "success": False,
                    "error": error_message,
                    "message": "タスク処理中にエラーが発生しました。"
                }
                
                self.active_tasks[task_id]["status"] = "error"
                self.active_tasks[task_id]["end_time"] = time.time()
                self.active_tasks[task_id]["result"] = error_response
                self.active_tasks[task_id]["error"] = {
                    "message": error_message,
                    "stack_trace": stack_trace
                }
                
                self.reasoning_history.append({
                    "task_id": task_id,
                    "task_type": task_type,
                    "timestamp": time.time(),
                    "result": error_response,
                    "error": error_message
                })
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=error_response,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                print(f"推論エージェント: タスク '{task_id}' のエラー応答を送信しました")
                responses.append(response)
        
        return responses
    
    def get_reasoning_history(self) -> List[Dict[str, Any]]:
        """推論履歴を取得"""
        return self.reasoning_history
        
    def _generate_mock_result(self, task_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        モックモード用の結果を生成
        
        Args:
            task_type: タスクタイプ
            content: タスク内容
            
        Returns:
            モック結果
        """
        print(f"モック結果を生成: タスクタイプ={task_type}")
        
        debug_info = {
            "mock": True,
            "generated_at": time.time(),
            "task_type": task_type,
            "content_keys": list(content.keys()) if isinstance(content, dict) else "not_a_dict"
        }
        
        if task_type == "reasoning_chain":
            task_description = content.get("task_description", "")
            result = {
                "chain": [
                    {"thought": f"タスク '{task_description[:30]}...' について考えています", "action": "情報を分析する"},
                    {"thought": "関連する概念を整理します", "action": "概念を構造化する"},
                    {"thought": "解決策を検討します", "action": "最適な解決策を選択する"}
                ],
                "solution": f"タスク '{task_description[:30]}...' に対するモック解決策です。これは実際のAPIコールなしで生成されています。",
                "debug_info": debug_info
            }
            return result
            
        elif task_type == "fix_code":
            code = content.get("code", "")
            error_message = content.get("error_message", "")
            result = {
                "fixed_code": f"# モックで修正されたコード\n# 元のエラー: {error_message}\n\n{code}\n# このコードはモックモードで修正されました",
                "reasoning_chain": [
                    {"thought": f"エラー '{error_message[:30]}...' を分析しています", "action": "エラーの原因を特定する"},
                    {"thought": "コードの問題箇所を特定しました", "action": "コードを修正する"}
                ],
                "debug_info": debug_info
            }
            return result
            
        elif task_type == "analyze_problem":
            problem_description = content.get("problem_description", "")
            result = {
                "understanding": f"問題 '{problem_description[:30]}...' の理解（モック）",
                "challenges": "モックで生成された課題リスト",
                "solution": "モックで生成された解決策",
                "next_steps": "モックで生成された次のステップ",
                "debug_info": debug_info
            }
            return result
            
        elif task_type == "analyze_task":
            description = content.get("description", "")
            task_type_guess = "web_search"
            
            if "コード" in description or "プログラム" in description:
                task_type_guess = "code_generation"
            elif "分析" in description or "評価" in description:
                task_type_guess = "analysis"
                
            result = {
                "task_type": task_type_guess,
                "complexity": "medium",
                "required_tools": ["web_crawler"] if task_type_guess == "web_search" else ["python_execute"],
                "debug_info": debug_info
            }
            return result
            
        elif task_type == "generate_plan":
            goal = content.get("goal", "")
            result = {
                "title": f"'{goal[:30]}...' のためのモック計画",
                "description": "これはモックモードで生成された計画です。実際のAPIコールは行われていません。",
                "steps": [
                    {"id": 1, "name": "情報収集", "description": "関連情報を収集します"},
                    {"id": 2, "name": "分析", "description": "収集した情報を分析します"},
                    {"id": 3, "name": "実装", "description": "分析結果に基づいて実装します"},
                    {"id": 4, "name": "評価", "description": "実装結果を評価します"}
                ],
                "debug_info": debug_info
            }
            return result
            
        else:
            return {
                "message": f"未知のタスクタイプ '{task_type}' に対するモック結果です",
                "debug_info": debug_info
            }
            return {
                "fixed_code": f"# モックで修正されたコード\n# 元のエラー: {error_message}\n\n{code}\n# このコードはモックモードで修正されました",
                "reasoning_chain": [
                    {"thought": f"エラー '{error_message[:30]}...' を分析しています", "action": "エラーの原因を特定する"},
                    {"thought": "コードの問題箇所を特定しました", "action": "コードを修正する"}
                ],
                "mock": True
            }
            
        elif task_type == "analyze_problem":
            problem_description = content.get("problem_description", "")
            return {
                "understanding": f"問題 '{problem_description[:30]}...' の理解（モック）",
                "challenges": "モックで生成された課題リスト",
                "solution": "モックで生成された解決策",
                "next_steps": "モックで生成された次のステップ",
                "mock": True
            }
            
        elif task_type == "analyze_task":
            description = content.get("description", "")
            task_type_guess = "web_search"
            
            if "コード" in description or "プログラム" in description:
                task_type_guess = "code_generation"
            elif "分析" in description or "評価" in description:
                task_type_guess = "analysis"
                
            return {
                "task_type": task_type_guess,
                "complexity": "medium",
                "required_tools": ["web_crawler"] if task_type_guess == "web_search" else ["python_execute"],
                "mock": True
            }
            
        elif task_type == "generate_plan":
            goal = content.get("goal", "")
            return {
                "title": f"'{goal[:30]}...' のためのモック計画",
                "description": "これはモックモードで生成された計画です。実際のAPIコールは行われていません。",
                "steps": [
                    {"id": 1, "name": "情報収集", "description": "関連情報を収集します"},
                    {"id": 2, "name": "分析", "description": "収集した情報を分析します"},
                    {"id": 3, "name": "実装", "description": "分析結果に基づいて実装します"},
                    {"id": 4, "name": "評価", "description": "実装結果を評価します"}
                ],
                "mock": True
            }
            
        else:
            return {
                "message": f"未知のタスクタイプ '{task_type}' に対するモック結果です",
                "mock": True
            }
