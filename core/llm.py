from typing import Dict, List, Any, Optional
import json
import os
try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except Exception:
    # tenacity未導入環境用のフォールバック（リトライ無し）
    def retry(*args, **kwargs):
        def wrapper(fn):
            return fn
        return wrapper
    def stop_after_attempt(*args, **kwargs):
        return None
    def wait_exponential(*args, **kwargs):
        return None
try:
    import requests  # type: ignore
    _REQUESTS_AVAILABLE = True
    _REQUESTS_EXC = (requests.RequestException,)
except Exception:
    requests = None  # type: ignore
    _REQUESTS_AVAILABLE = False
    class _DummyRequestsException(Exception):
        pass
    _REQUESTS_EXC = (_DummyRequestsException,)

# openai SDK が未インストール環境でも動作するように安全にインポート
try:
    import openai  # type: ignore
    from openai import OpenAI  # type: ignore
    _OPENAI_AVAILABLE = True
except Exception:
    openai = None  # type: ignore
    OpenAI = None  # type: ignore
    _OPENAI_AVAILABLE = False

class LLM:
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "gpt-5", 
                 temperature: float = 0.7,
                 provider: str = "openai"):
        self.model = model
        self.temperature = temperature
        self.provider = provider
        
        # Initialize the OpenAI client
        if api_key:
            openai_api_key = api_key
        else:
            # Try to get the API key from environment variables
            if provider == "openai":
                openai_api_key = os.environ.get("OPENAI_API_KEY")
            elif provider == "openrouter":
                openai_api_key = os.environ.get("OPENROUTER_API_KEY")
            else:
                openai_api_key = os.environ.get("OPENAI_API_KEY")
            
        self.mock_mode = False
        if not openai_api_key:
            print("LLMはモックモードで動作中です。実際のAPIコールは行われません。")
            self.mock_mode = True
            openai_api_key = "sk-mock-key"
        
        if provider == "openai":
            if _OPENAI_AVAILABLE:
                self.client = OpenAI(api_key=openai_api_key)  # type: ignore
            else:
                # SDKがない場合もモックモードで継続
                print("openai SDKが見つかりません。モックモードで動作します。")
                self.mock_mode = True
                self.client = None  # type: ignore
        else:
            self.api_key = openai_api_key

    def _is_gpt5_model(self) -> bool:
        try:
            return isinstance(self.model, str) and self.model.lower().startswith("gpt-5")
        except Exception:
            return False

    def _openai_chat(self, messages):
        """OpenAI Chat API call with model-specific parameter handling."""
        params = {
            "model": self.model,
            "messages": messages,
        }
        # Some models (e.g., gpt-5) only allow default temperature (1)
        if not self._is_gpt5_model():
            params["temperature"] = self.temperature
        else:
            params["temperature"] = 1
        return self.client.chat.completions.create(**params)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt"""
        # Handle prompt formats (string or list of message objects)
        messages = []
        
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            messages = prompt
        
        if self.mock_mode:
            if "タスク" in str(prompt) and "実行" in str(prompt):
                return "タスク実行の計画を立てています。関連する知識を検索し、最適な実行方法を決定します。"
            elif "検索" in str(prompt) or "調査" in str(prompt):
                return "検索クエリを生成し、関連情報を収集しています。複数の情報源から信頼性の高いデータを抽出します。"
            elif "分析" in str(prompt) or "評価" in str(prompt):
                return "データを分析し、パターンを特定しています。重要な洞察を抽出し、結論を導き出します。"
            else:
                return "これはモックモードのレスポンスです。実際のAPIコールは行われていません。"
            
        try:
            if self.mock_mode or (hasattr(self, 'client') and self.client.api_key in ["sk-mock-key", "dummy_key_for_testing"]):
                print("無効なAPIキーが検出されました。モックレスポンスを返します。")
                return "APIキーが無効なため、モックレスポンスを返します。有効なAPIキーを設定してください。"
            
            if self.provider == "openai":
                response = self._openai_chat(messages)
                return response.choices[0].message.content
            elif self.provider == "openrouter":
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://synthepseai.com",  # Replace with your site URL
                    "X-Title": "SynthepseAI"  # Replace with your app name
                }
                
                data = {
                    "model": self.model,  # e.g., "anthropic/claude-3-7-sonnet"
                    "messages": messages,
                    "temperature": self.temperature
                }
                
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code != 200:
                    raise ValueError(f"OpenRouter API returned error: {response.text}")
                    
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            # openai SDK があればエラー種別を判断
            if _OPENAI_AVAILABLE and isinstance(e, getattr(openai, 'AuthenticationError', Exception)):
                print(f"認証エラー: {str(e)}")
                self.mock_mode = True
                return "APIキー認証エラーが発生しました。モックモードに切り替えます。"
            
            # ネットワーク/接続系
            if isinstance(e, _REQUESTS_EXC + (ConnectionError, TimeoutError)) or (
                _OPENAI_AVAILABLE and isinstance(e, getattr(openai, 'APIConnectionError', Exception))
            ):
                print(f"接続エラー: {str(e)} — モックモードへ切替")
                self.mock_mode = True
                return "ネットワークまたは接続エラーのため、モックモードに切り替えました。"
            
            # その他の一般例外
            print(f"Error generating text: {str(e)} — モックモードへ切替")
            self.mock_mode = True
            return "API呼び出し中にエラーが発生したため、モックモードに切り替えました。"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_code(self, description: str) -> str:
        """Generate code from a description"""
        prompt = f"""
        Write Python code for the following task:
        
        {description}
        
        Only provide the code, no explanations or markdown.
        """
        
        if self.mock_mode:
            return """
import os
import json
import time
import random
import datetime

task_description = task_info.get("description", "Unknown task")

try:
    related_knowledge = get_related_knowledge([word for word in task_description.split() if len(word) > 3], 3)
    if related_knowledge:
        log_thought("task_start", {
            "task": task_description,
            "related_knowledge_found": len(related_knowledge)
        })
        
        for knowledge in related_knowledge:
            print(f"関連知識: {knowledge['subject']} - {knowledge['fact']}")
    else:
        log_thought("task_start", {
            "task": task_description,
            "related_knowledge_found": 0
        })
        print("このタスクに関連する既存の知識は見つかりませんでした。")
except Exception as e:
    print(f"知識ベース検索エラー: {str(e)}")
    log_thought("knowledge_search_error", {
        "task": task_description,
        "error": str(e)
    })

try:
    print(f"タスク「{task_description}」を実行中...")
    
    if "ライブラリをインポート" in task_description:
        libraries = [
            "os", "sys", "json", "datetime", "time", "random", 
            "numpy", "pandas", "matplotlib", "requests", 
            "beautifulsoup4", "scikit-learn"
        ]
        result = ", ".join(libraries)
        update_knowledge("必要なライブラリ", result, 0.9)
        
    elif "分析" in task_description or "解析" in task_description:
        analysis_results = {
            "データポイント数": random.randint(100, 1000),
            "平均値": round(random.uniform(10, 100), 2),
            "中央値": round(random.uniform(10, 100), 2),
            "標準偏差": round(random.uniform(1, 10), 2),
            "最小値": round(random.uniform(0, 50), 2),
            "最大値": round(random.uniform(50, 150), 2),
            "異常値の数": random.randint(0, 10)
        }
        result = f"データ分析結果: {json.dumps(analysis_results, ensure_ascii=False, indent=2)}"
        update_knowledge("データ分析結果", str(analysis_results), 0.8)
        
    elif "検索" in task_description or "調査" in task_description:
        search_results = {
            "検索クエリ": task_description,
            "ヒット数": random.randint(10, 100),
            "関連度の高い情報": [
                f"情報源1: {datetime.datetime.now().strftime('%Y-%m-%d')}の最新データによると...",
                f"情報源2: 専門家の見解によれば...",
                f"情報源3: 過去の類似事例では..."
            ]
        }
        result = f"検索結果: {json.dumps(search_results, ensure_ascii=False, indent=2)}"
        update_knowledge("検索結果", str(search_results), 0.7)
        
    elif "予測" in task_description or "予想" in task_description:
        prediction_results = {
            "予測対象": task_description,
            "予測値": round(random.uniform(0, 100), 2),
            "信頼区間": [round(random.uniform(0, 50), 2), round(random.uniform(50, 100), 2)],
            "精度": round(random.uniform(0.7, 0.95), 2),
            "使用モデル": random.choice(["線形回帰", "ランダムフォレスト", "ニューラルネットワーク"])
        }
        result = f"予測結果: {json.dumps(prediction_results, ensure_ascii=False, indent=2)}"
        update_knowledge("予測モデル結果", str(prediction_results), 0.75)
        
    elif "まとめ" in task_description or "結果" in task_description:
        all_knowledge = load_knowledge_db()
        summary = "タスク実行の結果まとめ:\\n"
        for subject, data in all_knowledge.items():
            if data.get("confidence", 0) > 0.7:
                summary += f"- {subject}: {data.get('fact', '')}\\n"
        result = summary
        update_knowledge("タスク実行まとめ", summary, 0.9)
        
    else:
        result = f"タスク「{task_description}」が正常に完了しました。"
    
    log_thought("task_execution", {
        "task": task_description,
        "status": "success",
        "result": result
    })
    
    update_knowledge(
        f"タスク実行: {task_description}",
        f"結果: {result}",
        0.8
    )
    
    return result
    
except Exception as e:
    error_message = str(e)
    
    log_thought("task_error", {
        "task": task_description,
        "error": error_message
    })
    
    update_knowledge(
        f"エラーパターン: {type(e).__name__}",
        f"タスク「{task_description}」で発生: {error_message}",
        0.7
    )
    
    return f"エラー: {error_message}"
            """.strip()
            
        try:
            response = self._openai_chat([{"role": "user", "content": prompt}])
            
            code = response.choices[0].message.content
            
            # Remove markdown code blocks if they exist
            code = code.replace("```python", "").replace("```", "").strip()
            
            return code
        except Exception as e:
            print(f"Error generating code: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def analyze_error(self, error: str, code: str) -> str:
        """Analyze an error and suggest a fix"""
        prompt = f"""
        The following Python code has encountered an error:
        
        ```python
        {code}
        ```
        
        The error is:
        ```
        {error}
        ```
        
        Please analyze the error and provide a fixed version of the code.
        Pay special attention to:
        1. Missing dependencies (handle import errors gracefully)
        2. Proper exception handling
        3. File operations (use 'with' statements)
        4. Missing variable definitions
        5. Potential environment-specific issues
        
        Only provide the fixed code, no explanations or markdown.
        """
        
        if self.mock_mode:
            return f"""
try:
    {code.strip()}
except Exception as e:
    print(f"エラーが発生しました: {{str(e)}}")
    print("モックモードでは詳細な修正は提供されません。")
            """.strip()
            
        try:
            response = self._openai_chat([{"role": "user", "content": prompt}])
            
            fixed_code = response.choices[0].message.content
            
            # Remove markdown code blocks if they exist
            fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
            
            return fixed_code
        except Exception as e:
            print(f"Error analyzing error: {str(e)}")
            raise
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def edit_knowledge(self, subject: str, target_fact: str, original_fact: Optional[str] = None) -> bool:
        """
        モデルの知識を編集するためのインターフェース
        
        Args:
            subject: 編集対象の主題
            target_fact: 新しい事実
            original_fact: 元の事実（オプション）
            
        Returns:
            編集が成功したかどうか
        """
        if self.mock_mode:
            print(f"モックモード: 知識編集をシミュレート - 主題: {subject}")
            return True
            
        try:
            prompt = f"""
            以下の知識を学習してください：
            
            主題: {subject}
            新しい事実: {target_fact}
            """
            
            if original_fact:
                prompt += f"""
                以前の事実: {original_fact}
                
                以前の事実を新しい事実に置き換えてください。
                """
            
            response = self._openai_chat([
                {"role": "system", "content": "あなたは新しい知識を学習できるアシスタントです。"},
                {"role": "user", "content": prompt}
            ])
            
            confirmation = response.choices[0].message.content
            success = "理解" in confirmation or "学習" in confirmation or "更新" in confirmation
            
            return success
        except Exception as e:
            print(f"知識編集エラー: {str(e)}")
            return False
