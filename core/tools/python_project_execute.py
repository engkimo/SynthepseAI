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
        task_info_code = f"""task_info = {{
    "task_id": "{task.id}",
    "description": "{task.description}",
    "plan_id": "{task.plan_id}"
}}
"""
        
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
            
            indented_code = "\n".join(["        " + line for line in task.code.split("\n")])
            
            if "result" not in task.code and not any(line.strip().startswith("return ") for line in task.code.split("\n")):
                if task.description.lower().startswith(("calculate", "compute", "find", "analyze")):
                    indented_code += "\n        return result"
            
            if "{imports}" not in template or "{main_code}" not in template:
                print("Warning: Template missing required placeholders. Using basic template.")
                template = """
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
                raw_code = safe_template.replace("{imports}", imports_str)
                raw_code = raw_code.replace("{main_code}", indented_code)
                raw_code = raw_code.replace("{task_id}", task.id)
                raw_code = raw_code.replace("{description}", task.description)
                raw_code = raw_code.replace("{plan_id}", task.plan_id if task.plan_id else "")
                
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

def run_task():
    \"\"\"
    タスクを実行して結果を返す関数
    \"\"\"
    try:
        result = None
{indented_code}
        if result is None:
            result = "Task completed successfully"
        return result
    except Exception as e:
        print(f"タスク実行エラー: {{str(e)}}")
        return {{"error": str(e), "traceback": traceback.format_exc()}}

def main():
    try:
        print("タスクを実行中...")
        task_result = run_task()
        print("タスク実行完了")
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
            formatted_code = f"""
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

def run_task():
    \"\"\"
    タスクを実行して結果を返す関数
    \"\"\"
    try:
        result = None
{indented_code}
        if result is None:
            result = "Task completed successfully"
        return result
    except Exception as e:
        print(f"タスク実行エラー: {{{{str(e)}}}}")
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
        
        # コードの先頭にタスク情報を追加 - task_info_code は不要（テンプレートに含まれている）
        full_code = formatted_code
        
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
