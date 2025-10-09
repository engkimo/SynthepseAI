# core/tools/python_project_execute.py
import os
import sys
import subprocess
import importlib
import re
from typing import Dict, Any, List, Tuple, Optional

from .base_tool import BaseTool, ToolResult
from ..project_environment import ProjectEnvironment
from ..task_database import TaskDatabase, Task, TaskStatus
from ..script_templates import get_template_for_task

class PythonProjectExecuteTool(BaseTool):
    """
    プロジェクト環境を使用してPythonコードを実行するツール
    """
    def __init__(self, workspace_dir: str, task_db: TaskDatabase):
        super().__init__(
            name="python_project_execute",
            description="Execute Python code in a project-specific environment with automatic dependency resolution"
        )
        self.workspace_dir = workspace_dir
        self.task_db = task_db
        self.parameters = {
            "command": {
                "type": "string",
                "enum": ["execute_code", "execute_task", "install_package", "check_package"]
            },
            "code": {"type": "string"},
            "task_id": {"type": "string"},
            "package": {"type": "string"},
            "plan_id": {"type": "string"}
        }
        
        # プロジェクト環境のキャッシュ
        self.environments = {}

    def _sanitize_generated_code(self, code: str) -> str:
        """
        生成コードの最低限の健全化を行う。
        - 不正な疑似モジュール（*_mod）を import している行を除去
        - LLMが生成した壊れた改行インポート（例: "import\n    np_mod"）を修正
        - テンプレ由来のメタ断片（"task_id": 等の裸キー行）を除去
        - 明らかに無効/未知の単語インポート（例: `import to`, `import duplicates`）を除去
        """
        import re
        allowed_modules = {
            # stdlib/common
            'os','sys','json','time','re','datetime','traceback','typing','glob','pathlib','logging','warnings','itertools','collections','subprocess','math','random',
            # data/plot
            'pandas','numpy','matplotlib','seaborn','pyarrow','fastparquet',
            # io/web
            'requests','bs4','pandas_datareader','yfinance'
        }
        # 1) 壊れたインポートの単純修正
        code = re.sub(r"import\s*\n\s+([A-Za-z_]\w*_mod)\b", r"import \1", code)
        cleaned = []
        for line in code.splitlines():
            if re.match(r"^\s*import\s+[A-Za-z_]\w*_mod(\s+as\s+\w+)?\s*$", line):
                # *_mod の直接importは破棄（後段の_safe_importを利用）
                continue
            if re.match(r"^\s*from\s+[A-Za-z_]\w*_mod\s+import\b.*$", line):
                # *_mod からの import も破棄
                continue
            # 2) 裸のメタキー行（JSON断片）を除去
            if re.match(r"^\s*\"(task_id|description|plan_id)\"\s*:\s*", line):
                continue
            # 3) 無効または未知モジュールの単語インポートを除去
            m = re.match(r"^\s*import\s+([A-Za-z_][\w.]*)\s*$", line)
            if m:
                root = m.group(1).split('.')[0]
                if root not in allowed_modules:
                    continue
            m2 = re.match(r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\b", line)
            if m2:
                root = m2.group(1).split('.')[0]
                if root not in allowed_modules:
                    continue
            cleaned.append(line)
        return "\n".join(cleaned)

    def _apply_template(self, template: str, imports: str, main_code: str, extra: dict | None = None) -> str:
        """{imports}, {main_code} と任意の追加プレースホルダを波括弧置換で安全に適用"""
        code = template.replace("{imports}", imports)
        code = code.replace("{main_code}", main_code)
        if extra:
            for k, v in extra.items():
                code = code.replace(f"{{{k}}}", str(v))
        return code
    
    def execute(self, command: str, **kwargs) -> ToolResult:
        """ツールコマンドを実行"""
        command_handlers = {
            "execute_code": self._handle_execute_code,
            "execute_task": self._handle_execute_task,
            "install_package": self._handle_install_package,
            "check_package": self._handle_check_package
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return ToolResult(False, None, f"Unknown command: {command}")
        
        try:
            return handler(**kwargs)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return ToolResult(False, None, f"{str(e)}\n{error_details}")
    
    def _get_environment(self, plan_id: str = None) -> ProjectEnvironment:
        """プロジェクト環境を取得（キャッシュがあればそれを使用）"""
        key = plan_id or "default"
        
        if key not in self.environments:
            self.environments[key] = ProjectEnvironment(self.workspace_dir, plan_id)
            
        return self.environments[key]
    
    def _handle_execute_code(self, code: str, plan_id: str = None, **kwargs) -> ToolResult:
        """コードを実行"""
        env = self._get_environment(plan_id)
        
        # コードから必要なパッケージを検出
        dependencies = self._detect_dependencies(code)
        
        # 実行（自動依存関係解決あり）
        success, result, error = env.execute_with_auto_dependency_resolution(code)
        
        if success:
            return ToolResult(True, result)
        else:
            return ToolResult(False, None, error)
    
    def _handle_execute_task(self, task_id: str, **kwargs) -> ToolResult:
        """タスクIDを指定してタスクを実行"""
        # タスクを取得
        task = self.task_db.get_task(task_id)
        if not task:
            return ToolResult(False, None, f"Task with ID {task_id} not found")
        
        # タスクのコードがなければエラー
        if not task.code:
            print(f"Task {task_id} has no code to execute")
            return ToolResult(False, None, f"Task {task_id} has no code to execute")
        
        # タスクのステータスを更新
        self.task_db.update_task(task_id, TaskStatus.RUNNING)
        
        # プロジェクト環境を取得
        env = self._get_environment(task.plan_id)
        
        # スクリプト名を作成（タスクIDを使用）
        script_name = f"task_{task_id}.py"
        
        # タスク情報を環境変数として設定するコード（インデントなし）
        task_info_code = r"""task_info = {
    "task_id": "$task_id",
    "description": "$description",
    "plan_id": "$plan_id"
}
"""
        from string import Template
        task_info_template = Template(task_info_code)
        task_info_code = task_info_template.safe_substitute({
            "task_id": task.id,
            "description": task.description,
            "plan_id": task.plan_id if task.plan_id else ""
        })
        
        try:
            required_libraries = self._detect_dependencies(task.code)
            imports_str = "\n".join([f"import {lib}" for lib in required_libraries])
            
            recommended_packages = []
            try:
                from core.enhanced_persistent_thinking_ai import EnhancedPersistentThinkingAI
                if 'persistent_thinking' in globals() and isinstance(globals()['persistent_thinking'], EnhancedPersistentThinkingAI):
                    knowledge = globals()['persistent_thinking'].get_knowledge_for_script(task.description)
                    if knowledge and "recommended_packages" in knowledge:
                        recommended_packages = knowledge["recommended_packages"]
                        print(f"AIが推奨するパッケージ: {', '.join([p['name'] for p in recommended_packages])}")
            except Exception as e:
                print(f"パッケージ推奨取得エラー: {str(e)}")
            
            template = get_template_for_task(task.description, required_libraries, recommended_packages)
            
            task_specific_code = task.code
            
            template_markers = [
                "task_info =", "KNOWLEDGE_DB_PATH =", "THINKING_LOG_PATH =",
                "def load_knowledge_db", "def save_knowledge_db", "def log_thought",
                "def update_knowledge", "def add_insight", "def add_hypothesis",
                "def verify_hypothesis", "def add_conclusion", "def integrate_task_results",
                "def request_multi_agent_discussion", "def prepare_task", "def run_task", "def main"
            ]
            
            clean_lines = []
            for line in task_specific_code.split("\n"):
                if not any(marker in line for marker in template_markers):
                    clean_lines.append(line)
            
            indented_code = "\n".join(["        " + line for line in clean_lines])
            
            if "result" not in task_specific_code and not any(line.strip().startswith("return ") for line in clean_lines):
                if task.description.lower().startswith(("calculate", "compute", "find", "analyze")):
                    indented_code += "\n        return result"
            
            if "{imports}" not in template or "{main_code}" not in template:
                print("Warning: Template missing required placeholders. Using basic template.")
                template = r"""
{imports}
import typing  # 型アノテーション用
import time  # 時間計測用
import traceback  # エラートレース用
import os  # ファイル操作用
import json  # JSON処理用
import datetime  # 日付処理用

task_info = {{
    "task_id": "{task_id}",
    "description": "{description}",
    "plan_id": "{plan_id}"
}}

def run_task():
    \"\"\"
    タスクを実行して結果を返す関数
    \"\"\"
    try:
        result = None
{main_code}
        if result is None:
            result = "Task completed successfully"
        return result
    except Exception as e:
        print(f"Error: {{{{str(e)}}}}")
        return {{"error": str(e), "traceback": traceback.format_exc()}}

def main():
    try:
        print("タスクを実行中...")
        task_result = run_task()
        print("タスク実行完了")
        return task_result
    except Exception as e:
        print(f"Error: {{{{str(e)}}}}")
        return str(e)
    
if __name__ == "__main__":
    result = main()
"""
            
            task_info_var = f"""
task_info = {{
    "task_id": "{task.id}",
    "description": "{task.description}",
    "plan_id": "{task.plan_id}"
}}
"""
            
            safe_template = template.replace("{str(e)}", "___STR_E___")
            
            import re
            positional_fields = re.findall(r'\{(\d+)\}', safe_template)
            for field in positional_fields:
                safe_template = safe_template.replace(f"{{{field}}}", f"___POS_{field}___")
            
            try:
                format_dict = {
                    "imports": imports_str,
                    "main_code": indented_code,
                    "task_id": task.id,
                    "description": task.description,
                    "plan_id": task.plan_id if task.plan_id else ""
                }
                
                # {imports}/{main_code}/{task_id}/{description}/{plan_id} を置換
                raw_code = self._apply_template(
                    safe_template,
                    imports_str,
                    indented_code,
                    {"task_id": task.id, "description": task.description, "plan_id": task.plan_id or ""}
                )

                for field in positional_fields:
                    raw_code = raw_code.replace(f"___POS_{field}___", f"{{{field}}}")
                
                raw_code = raw_code.replace("___STR_E___", "{str(e)}")
            except Exception as e:
                print(f"テンプレート処理エラー: {str(e)}")
                raw_code = f"""
{imports_str}
import typing  # 型アノテーション用
import time  # 時間計測用
import traceback  # エラートレース用
import os  # ファイル操作用
import json  # JSON処理用
import datetime  # 日付処理用

task_info = {{
    "task_id": "{task.id}",
    "description": "{task.description}",
    "plan_id": "{task.plan_id if task.plan_id else ""}"
}}

KNOWLEDGE_DB_PATH = "./workspace/persistent_thinking/knowledge_db.json"
THINKING_LOG_PATH = "./workspace/persistent_thinking/thinking_log.jsonl"

task_description = task_info.get("description", "Unknown task")
insights = []
hypotheses = []
conclusions = []

def load_knowledge_db():
    try:
        if os.path.exists(KNOWLEDGE_DB_PATH):
            with open(KNOWLEDGE_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {{}}
    except Exception as e:
        print(f"知識データベース読み込みエラー: {{str(e)}}")
        return {{}}

def save_knowledge_db(knowledge_db):
    try:
        os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
        with open(KNOWLEDGE_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(knowledge_db, fp=f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"知識データベース保存エラー: {{str(e)}}")
        return False

def log_thought(thought_type, content):
    try:
        os.makedirs(os.path.dirname(THINKING_LOG_PATH), exist_ok=True)
        log_entry = {{"timestamp": time.time(), "type": thought_type, "content": content}}
        with open(THINKING_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\\n")
        return True
    except Exception as e:
        print(f"思考ログ記録エラー: {{str(e)}}")
        return False

def run_task():
    # タスクを実行して結果を返す関数
    try:
        result = None
{indented_code}
        if result is None:
            result = "Task completed successfully"
        return result
    except Exception as e:
        print(f"タスク実行エラー: {{str(e)}}")
        return {{"error": str(e), "traceback": traceback.format_exc()}}

def integrate_task_results(task_result, confidence=0.8):
    global task_description
    if not task_result:
        return False
    try:
        knowledge_items = []
        if isinstance(task_result, dict):
            for key, value in task_result.items():
                if isinstance(value, (str, int, float, bool)):
                    subject = f"{{task_description[:30]}} - {{key}}"
                    fact = str(value)
                    knowledge_items.append({{"subject": subject, "fact": fact, "confidence": confidence}})
        elif isinstance(task_result, str):
            lines = task_result.split("\\n")
            for line in lines:
                if ":" in line and len(line) > 10:
                    parts = line.split(":", 1)
                    subject = f"{{task_description[:30]}} - {{parts[0].strip()}}"
                    fact = parts[1].strip()
                    knowledge_items.append({{"subject": subject, "fact": fact, "confidence": confidence}})
        for item in knowledge_items:
            update_knowledge(item["subject"], item["fact"], item["confidence"], "task_result_integration")
        log_thought("task_result_integration", {{"task": task_description, "extracted_knowledge_count": len(knowledge_items)}})
        return True
    except Exception as e:
        print(f"タスク結果統合エラー: {{str(e)}}")
        return False

def main():
    try:
        print("タスクを実行中...")
        task_result = run_task()
        print("タスク実行完了")
        if task_result is not None:
            print("タスク結果を知識ベースに統合中...")
            integrate_success = integrate_task_results(task_result)
            if integrate_success:
                print("知識ベースへの統合に成功しました")
        return task_result
    except Exception as e:
        print(f"Error: {{str(e)}}")
        return str(e)
    
if __name__ == "__main__":
    result = main()
"""
            
            try:
                from core.tools.script_linter import ScriptLinter
                
                linter = ScriptLinter(use_black=True, use_isort=True, use_flake8=False, use_mypy=False)
                formatted_code, warnings = linter.lint_and_format(raw_code)
                
                if warnings:
                    for warning in warnings:
                        print(f"Linter warning during code generation: {warning}")
            except ImportError:
                try:
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from tools.script_linter import ScriptLinter
                    
                    linter = ScriptLinter(use_black=True, use_isort=True, use_flake8=False, use_mypy=False)
                    formatted_code, warnings = linter.lint_and_format(raw_code)
                    
                    if warnings:
                        for warning in warnings:
                            print(f"Linter warning during code generation: {warning}")
                except ImportError:
                    print("ScriptLinter not available during code generation, using raw code")
                    formatted_code = raw_code
                except Exception as e:
                    print(f"Error using ScriptLinter during code generation: {str(e)}")
                    formatted_code = raw_code
            except Exception as e:
                print(f"Error using ScriptLinter during code generation: {str(e)}")
                formatted_code = raw_code
        except KeyError as e:
            print(f"Template formatting error: {str(e)}. Using basic template.")
            fallback_template = r"""
$imports
import typing  # 型アノテーション用
import time  # 時間計測用
import traceback  # エラートレース用
import os  # ファイル操作用
import json  # JSON処理用
import datetime  # 日付処理用

task_info = {
    "task_id": "$task_id",
    "description": "$description",
    "plan_id": "$plan_id"
}

def run_task():
    # タスクを実行して結果を返す関数
    try:
        result = None
$main_code
        if result is None:
            result = "Task completed successfully"
        return result
    except Exception as e:
        print(f"タスク実行エラー: {str(e)}")
        return {"error": str(e), "traceback": traceback.format_exc()}

def main():
    try:
        print("タスクを実行中...")
        task_result = run_task()
        print("タスク実行完了")
        return task_result
    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e)
    
if __name__ == "__main__":
    result = main()
"""
            from string import Template
            fallback_t = Template(fallback_template)
            formatted_code = fallback_t.safe_substitute({
                "imports": imports_str,
                "main_code": indented_code,
                "task_id": task.id,
                "description": task.description,
                "plan_id": task.plan_id if task.plan_id else ""
            })
        
        # コードの先頭にタスク情報を追加 - task_info_code は不要（テンプレートに含まれている）
        # 保存前に最低限のサニタイズを実施
        full_code = self._sanitize_generated_code(formatted_code)
        
        # スクリプトを保存（自動フォーマット処理が適用される）
        print(f"Formatting and saving task script: {script_name}")
        script_path = env.save_script(script_name, full_code)
        
        # 直接Pythonを使用してスクリプトを実行するバックアップ方法
        def run_with_system_python():
            try:
                # スクリプト内容をメモリに読み込む
                with open(script_path, 'r') as f:
                    script_content = f.read()
                
                # スクリプトを一時ファイルとして現在のディレクトリに保存
                temp_script = os.path.join(os.getcwd(), f"temp_task_{task_id}.py")
                with open(temp_script, 'w') as f:
                    f.write(script_content)
                
                # システムのPythonで実行
                result = subprocess.run(
                    [sys.executable, temp_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=env.project_dir
                )
                
                # 一時ファイルを削除
                os.unlink(temp_script)
                
                return result.returncode == 0, result.stdout, result.stderr
            except Exception as e:
                return False, "", str(e)
        
        try:
            # 最大3回まで試行（依存関係の自動解決のため）
            max_attempts = 3
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                
                # スクリプトを実行
                success, stdout, stderr = env.execute_script(script_path)
                
                # 成功した場合
                if success:
                    # タスクのステータスを更新
                    self.task_db.update_task(task_id, TaskStatus.COMPLETED, stdout)
                    return ToolResult(True, stdout)
                
                # 実行に失敗し、"No such file or directory"エラーが含まれる場合は
                # システムPythonを使って直接実行するバックアップ方法を試す
                if "No such file or directory" in stderr and attempt == 1:
                    print(f"Trying backup execution method for task {task_id}")
                    success, stdout, stderr = run_with_system_python()
                    
                    if success:
                        # タスクのステータスを更新
                        self.task_db.update_task(task_id, TaskStatus.COMPLETED, stdout)
                        return ToolResult(True, stdout)
                
                # 依存パッケージの問題かチェック
                missing_packages = env.extract_missing_packages(stderr)
                
                # 不足パッケージがなければ他のエラー
                if not missing_packages:
                    if attempt == max_attempts:
                        # タスクのステータスを更新
                        self.task_db.update_task(task_id, TaskStatus.FAILED, stderr)
                        return ToolResult(False, None, stderr)
                    continue
                
                print(f"Detected missing packages: {', '.join(missing_packages)}")
                
                # パッケージをインストール
                all_installed = env.install_requirements(missing_packages)
                
                # すべてのパッケージをインストールできなかった場合
                if not all_installed:
                    print("Could not install all required packages")
                    if attempt == max_attempts:
                        # タスクのステータスを更新
                        self.task_db.update_task(
                            task_id, 
                            TaskStatus.FAILED, 
                            f"Failed to install required packages: {', '.join(missing_packages)}"
                        )
                        return ToolResult(False, None, f"Failed to install required packages: {', '.join(missing_packages)}")
            
            # 最大試行回数に達した場合
            self.task_db.update_task(task_id, TaskStatus.FAILED, "Max attempts reached without success")
            return ToolResult(False, None, "Max attempts reached without success")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            # タスクのステータスを更新
            self.task_db.update_task(task_id, TaskStatus.FAILED, str(e))
            return ToolResult(False, None, f"{str(e)}\n{error_details}")
    
    def _check_package_exists_on_pypi(self, package_name: str) -> bool:
        """PyPIにパッケージが存在するかチェック"""
        try:
            import requests
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"PyPI確認エラー: {str(e)}")
            return True
            
    def _get_package_alternatives(self, package_name: str) -> List[str]:
        """存在しないパッケージの代替候補を提案"""
        # 特殊なマッピング
        alternatives = {
            "Yahoo": ["yfinance"],
            "Pandas": ["pandas"],
            "Numpy": ["numpy"],
            "Matplotlib": ["matplotlib"],
            "Scikit": ["scikit-learn"],
            "Tensorflow": ["tensorflow"],
            "Pytorch": ["torch"],
            "BeautifulSoup": ["beautifulsoup4"],
            "Requests": ["requests"],
        }
        
        return alternatives.get(package_name, [])
    
    def _handle_install_package(self, package: str, plan_id: str = None, **kwargs) -> ToolResult:
        """パッケージをインストール"""
        env = self._get_environment(plan_id)
        
        if not self._check_package_exists_on_pypi(package):
            alternatives = self._get_package_alternatives(package)
            
            if alternatives:
                alt_message = f"パッケージ '{package}' はPyPIに存在しません。代わりに {', '.join(alternatives)} を試します。"
                print(alt_message)
                
                # 代替パッケージをインストール
                for alt in alternatives:
                    if self._check_package_exists_on_pypi(alt):
                        success = env.install_package(alt)
                        if success:
                            return ToolResult(True, f"代替パッケージ {alt} をインストールしました（元のパッケージ {package} は存在しません）")
            
            return ToolResult(False, None, f"パッケージ '{package}' はPyPIに存在せず、適切な代替も見つかりませんでした")
        
        # パッケージをインストール
        success = env.install_package(package)
        
        if success:
            return ToolResult(True, f"Successfully installed {package}")
        else:
            return ToolResult(False, None, f"Failed to install {package}")
    
    def _handle_check_package(self, package: str, plan_id: str = None, **kwargs) -> ToolResult:
        """パッケージがインストール済みかチェック"""
        env = self._get_environment(plan_id)
        
        # パッケージがインストール済みかチェック
        installed = env.is_package_installed(package)
        
        return ToolResult(True, {"installed": installed})
    
    def _detect_dependencies(self, code: str) -> List[str]:
        """コードから必要なパッケージを検出"""
        # importステートメントを検出するパターン
        import_pattern = r'(?:from|import)\s+([\w.]+)'
        imports = re.findall(import_pattern, code)
        
        # モジュール名を正規化（サブモジュールからルートモジュールへ）
        modules = set()
        for imp in imports:
            # ドットで分割して最初の部分を取得（ルートモジュール）
            root_module = imp.split('.')[0]
            modules.add(root_module)
        
        # 必要なパッケージのリスト
        required_packages = []
        for module in modules:
            # 標準ライブラリのモジュールは除外
            if self._is_stdlib_module(module):
                continue
                
            # 特殊なマッピング（bs4 -> beautifulsoup4など）
            if module == "bs4":
                required_packages.append("beautifulsoup4")
            elif module == "Yahoo":
                if "yfinance" not in required_packages:
                    required_packages.append("yfinance")
            else:
                required_packages.append(module)
        
        return required_packages
    
    def _is_stdlib_module(self, module_name: str) -> bool:
        """モジュールが標準ライブラリの一部かどうかを判定"""
        # 一般的な標準ライブラリ
        stdlib_modules = {
            "os", "sys", "math", "random", "datetime", "time", "json", 
            "csv", "re", "collections", "itertools", "functools", "io",
            "pathlib", "shutil", "glob", "argparse", "logging", "unittest",
            "threading", "multiprocessing", "subprocess", "socket", "email",
            "smtplib", "urllib", "http", "xml", "html", "tkinter", "sqlite3",
            "hashlib", "uuid", "tempfile", "copy", "traceback", "gc", "inspect"
        }
        
        return module_name in stdlib_modules
