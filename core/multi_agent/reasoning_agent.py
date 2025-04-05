from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid
import traceback

from .agent_base import MultiAgentBase, AgentRole, AgentMessage

class ReasoningAgent(MultiAgentBase):
    """
    推論を担当するエージェント
    
    自己反省型推論（COAT）フレームワークを使用して、
    問題解決のための推論チェーンを生成する
    """
    
    def __init__(
        self,
        agent_id: str = "reasoning_agent",
        name: str = "推論エージェント",
        description: str = "自己反省型推論を行い、問題解決のための推論チェーンを生成する",
        llm=None,
        mock_mode: bool = False
    ):
        """
        推論エージェントの初期化
        
        Args:
            agent_id: エージェントID
            name: エージェント名
            description: エージェントの説明
            llm: 使用するLLMインスタンス
            mock_mode: モックモードで動作するかどうか
        """
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.MAIN_REASONING,
            name=name,
            description=description,
            llm=llm
        )
        
        self.active_tasks = {}  # タスクID -> タスク情報
        self.reasoning_history = []  # 推論履歴
        self.task_processing_errors = {}  # タスク処理中のエラー
        self.mock_mode = mock_mode
        
        if self.mock_mode:
            print(f"推論エージェント '{agent_id}' はモックモードで動作中です")
    
    def generate_reasoning_chain(self, task_description: str) -> Dict[str, Any]:
        """
        タスクに対する推論チェーンを生成
        
        Args:
            task_description: タスクの説明
            
        Returns:
            推論チェーンと解決策を含む辞書
        """
        if self.mock_mode:
            return self._generate_mock_result("reasoning_chain", {"task_description": task_description})
            
        # 実際のLLMを使用した推論チェーン生成
        try:
            # LLMを使用して推論チェーンを生成
            prompt = f"以下のタスクに対する推論チェーンを生成してください:\n{task_description}"
            
            response = self.llm.generate(prompt)
            
            # 応答を解析して推論チェーンを構築
            # 実際の実装ではより複雑な処理が必要
            
            return {
                "chain": [
                    {"thought": "タスクを分析します", "action": "情報を収集する"},
                    {"thought": "収集した情報を整理します", "action": "関連性を評価する"},
                    {"thought": "解決策を検討します", "action": "最適な解決策を選択する"}
                ],
                "solution": f"タスク '{task_description[:50]}...' に対する解決策です。"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def fix_code_with_reasoning(self, code: str, error_message: str) -> Dict[str, Any]:
        """
        エラーのあるコードを修正
        
        Args:
            code: 修正するコード
            error_message: エラーメッセージ
            
        Returns:
            修正されたコードと推論チェーン
        """
        if self.mock_mode:
            return self._generate_mock_result("fix_code", {"code": code, "error_message": error_message})
            
        # 実際のLLMを使用したコード修正
        try:
            prompt = f"以下のコードを修正してください。エラー: {error_message}\n\nコード:\n{code}"
            
            response = self.llm.generate(prompt)
            
            # 応答を解析して修正されたコードを抽出
            # 実際の実装ではより複雑な処理が必要
            
            return {
                "fixed_code": f"# 修正されたコード\n{code}\n# エラーを修正しました",
                "reasoning_chain": [
                    {"thought": "エラーを分析します", "action": "問題箇所を特定する"},
                    {"thought": "修正方法を検討します", "action": "コードを修正する"}
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_problem(self, problem_description: str) -> Dict[str, Any]:
        """
        問題を分析
        
        Args:
            problem_description: 問題の説明
            
        Returns:
            問題の理解、課題、解決策、次のステップを含む辞書
        """
        if self.mock_mode:
            return self._generate_mock_result("analyze_problem", {"problem_description": problem_description})
            
        # 実際のLLMを使用した問題分析
        try:
            prompt = f"以下の問題を分析してください:\n{problem_description}"
            
            response = self.llm.generate(prompt)
            
            # 応答を解析して問題分析結果を構築
            # 実際の実装ではより複雑な処理が必要
            
            return {
                "understanding": f"問題 '{problem_description[:50]}...' の理解",
                "challenges": "課題リスト",
                "solution": "解決策",
                "next_steps": "次のステップ"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def generate_plan(self, goal: str) -> Dict[str, Any]:
        """
        目標に対する計画を生成
        
        Args:
            goal: 達成したい目標
            
        Returns:
            計画を含む辞書
        """
        if self.mock_mode:
            return self._generate_mock_result("generate_plan", {"goal": goal})
            
        # 実際のLLMを使用した計画生成
        try:
            prompt = f"以下の目標を達成するための計画を生成してください:\n{goal}"
            
            response = self.llm.generate(prompt)
            
            # 応答を解析して計画を構築
            # 実際の実装ではより複雑な処理が必要
            
            return {
                "title": f"'{goal[:50]}...' のための計画",
                "description": "計画の説明",
                "steps": [
                    {"id": 1, "name": "情報収集", "description": "関連情報を収集します"},
                    {"id": 2, "name": "分析", "description": "収集した情報を分析します"},
                    {"id": 3, "name": "実装", "description": "分析結果に基づいて実装します"},
                    {"id": 4, "name": "評価", "description": "実装結果を評価します"}
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _process_single_message(self, message: AgentMessage) -> List[AgentMessage]:
        """
        単一のメッセージを処理
        
        Args:
            message: 処理するメッセージ
            
        Returns:
            処理結果として生成されたメッセージのリスト
        """
        responses = []
        
        print(f"推論エージェント: メッセージを処理します: タイプ={message.message_type}, 送信者={message.sender_id}")
        
        if message.message_type == "task":
            metadata = message.metadata or {}
            task_id = metadata.get("task_id")
            task_type = metadata.get("task_type")
            is_retry = metadata.get("retry", False)
            retry_count = metadata.get("retry_count", 0)
            
            # 詳細なデバッグ情報を表示
            if is_retry:
                print(f"推論エージェント: タスク '{task_id}' (タイプ: {task_type}) の再処理を開始します (再試行回数: {retry_count})")
            else:
                print(f"推論エージェント: タスク '{task_id}' (タイプ: {task_type}) の処理を開始します")
            
            # タスクが既に処理中の場合は状態を確認
            if task_id in self.active_tasks:
                current_status = self.active_tasks[task_id].get("status")
                start_time = self.active_tasks[task_id].get("start_time", time.time())
                elapsed = time.time() - start_time
                
                print(f"推論エージェント: タスク '{task_id}' は既に処理中です (状態: {current_status}, 経過時間: {elapsed:.1f}秒)")
                
                # 既に完了している場合は結果を再送信
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
                
                # 長時間処理中の場合は強制的に完了させる
                if current_status == "processing" and elapsed > 10.0:
                    print(f"推論エージェント: タスク '{task_id}' は10秒以上処理中のままです。強制的に完了させます。")
                    
                    # モック結果を生成して強制的に完了
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
            
            # 新しいタスクとして処理を開始
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
            
            # 処理ステップを更新する関数
            def update_step(step_name):
                if task_id in self.active_tasks:
                    self.active_tasks[task_id]["step"] = step_name
                    self.active_tasks[task_id]["last_update"] = time.time()
                    print(f"推論エージェント: タスク '{task_id}' の処理ステップを '{step_name}' に更新しました")
            
            try:
                update_step("starting")
                
                if self.mock_mode:
                    print(f"推論エージェント: モックモードでタスク '{task_id}' を処理します")
                    
                    # モック処理時間を変動させる（デバッグ用）
                    processing_time = 0.5 + (hash(task_id) % 5) * 0.1  # 0.5〜0.9秒のランダムな処理時間
                    print(f"推論エージェント: モック処理時間 {processing_time:.1f}秒をシミュレート")
                    
                    # 処理ステップを更新しながら進行
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
                    
                    coordinator_response = self.send_message(
                        receiver_id="coordinator",
                        content=mock_result,
                        message_type="task_result",
                        metadata={"task_id": task_id, "agent_id": self.agent_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' のモック結果をコーディネーターに直接送信しました (処理時間: {processing_time:.1f}秒)")
                    
                    response = self.send_message(
                        receiver_id=message.sender_id,
                        content=mock_result,
                        message_type="task_result",
                        metadata={"task_id": task_id}
                    )
                    print(f"推論エージェント: タスク '{task_id}' のモック結果を要求者 '{message.sender_id}' に送信しました (処理時間: {processing_time:.1f}秒)")
                    responses.append(response)
                    responses.append(coordinator_response)
                    return responses
                
                if task_type == "reasoning_chain":
                    update_step("generating_reasoning_chain")
                    task_description = message.content.get("task_description", "")
                    result = self.generate_reasoning_chain(task_description)
                    
                elif task_type == "fix_code":
                    update_step("fixing_code")
                    code = message.content.get("code", "")
                    error_message = message.content.get("error_message", "")
                    result = self.fix_code_with_reasoning(code, error_message)
                    
                elif task_type == "analyze_problem":
                    update_step("analyzing_problem")
                    problem_description = message.content.get("problem_description", "")
                    result = self.analyze_problem(problem_description)
                    
                elif task_type == "analyze_task":
                    update_step("analyzing_task")
                    description = message.content.get("description", "")
                    
                    # タスクの種類を推測
                    task_type_guess = "web_search"
                    if "コード" in description or "プログラム" in description:
                        task_type_guess = "code_generation"
                    elif "分析" in description or "評価" in description:
                        task_type_guess = "analysis"
                        
                    result = {
                        "task_type": task_type_guess,
                        "complexity": "medium",
                        "required_tools": ["web_crawler"] if task_type_guess == "web_search" else ["python_execute"]
                    }
                    
                elif task_type == "generate_plan":
                    update_step("generating_plan")
                    goal = message.content.get("goal", "")
                    result = self.generate_plan(goal)
                    
                else:
                    update_step("unknown_task_type")
                    result = {
                        "error": f"未知のタスクタイプ: {task_type}",
                        "message": "このタスクタイプは推論エージェントでは処理できません。"
                    }
                
                update_step("completing")
                
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
                print(f"推論エージェント: タスク '{task_id}' の結果を送信しました: 受信者={message.sender_id}")
                print(f"推論エージェント: 結果の概要: {str(result)[:100]}...")
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
                
                coordinator_response = self.send_message(
                    receiver_id="coordinator",
                    content=error_response,
                    message_type="task_result",
                    metadata={"task_id": task_id, "agent_id": self.agent_id, "status": "error"}
                )
                print(f"推論エージェント: タスク '{task_id}' のエラー応答をコーディネーターに直接送信しました")
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=error_response,
                    message_type="task_result",
                    metadata={"task_id": task_id, "status": "error"}
                )
                print(f"推論エージェント: タスク '{task_id}' のエラー応答を要求者 '{message.sender_id}' に送信しました")
                responses.append(response)
                responses.append(coordinator_response)
        
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
        
        # 共通のデバッグ情報を追加
        debug_info = {
            "mock": True,
            "generated_at": time.time(),
            "task_type": task_type,
            "content_keys": list(content.keys()) if isinstance(content, dict) else "not_a_dict"
        }
        
        # 各タスクタイプに応じた結果を生成
        if task_type == "reasoning_chain":
            task_description = content.get("task_description", "")
            return {
                "chain": [
                    {"thought": f"タスク '{task_description[:30]}...' について考えています", "action": "情報を分析する"},
                    {"thought": "関連する概念を整理します", "action": "概念を構造化する"},
                    {"thought": "解決策を検討します", "action": "最適な解決策を選択する"}
                ],
                "solution": f"タスク '{task_description[:30]}...' に対するモック解決策です。これは実際のAPIコールなしで生成されています。",
                "debug_info": debug_info
            }
        
        elif task_type == "fix_code":
            code = content.get("code", "")
            error_message = content.get("error_message", "")
            return {
                "fixed_code": f"# モックで修正されたコード\n# 元のエラー: {error_message}\n\n{code}\n# このコードはモックモードで修正されました",
                "reasoning_chain": [
                    {"thought": f"エラー '{error_message[:30]}...' を分析しています", "action": "エラーの原因を特定する"},
                    {"thought": "コードの問題箇所を特定しました", "action": "コードを修正する"}
                ],
                "debug_info": debug_info
            }
        
        elif task_type == "analyze_problem":
            problem_description = content.get("problem_description", "")
            return {
                "understanding": f"問題 '{problem_description[:30]}...' の理解（モック）",
                "challenges": "モックで生成された課題リスト",
                "solution": "モックで生成された解決策",
                "next_steps": "モックで生成された次のステップ",
                "debug_info": debug_info
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
                "debug_info": debug_info
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
                "debug_info": debug_info
            }
        
        # デフォルトの結果
        else:
            return {
                "message": f"未知のタスクタイプ '{task_type}' に対するモック結果です",
                "debug_info": debug_info
            }
