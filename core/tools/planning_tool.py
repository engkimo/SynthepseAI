import os
import json
import re
import time
import traceback
from typing import List, Dict, Any, Optional, Union, Tuple

from core.script_templates import get_template_for_task
from core.tools.base_tool import BaseTool, ToolResult

class PlanningTool(BaseTool):
    """タスクの計画と実行を管理するツール"""
    
    def __init__(self, llm=None, task_db=None, python_execute_tool=None):
        """初期化"""
        super().__init__(
            name="planning",
            description="A tool for planning and managing the execution of complex tasks"
        )
        self.llm = llm
        self.task_db = task_db
        self.python_execute_tool = python_execute_tool
    
    def execute(self, action, params=None):
        """アクションを実行"""
        if action == "generate_plan":
            return self._handle_generate_plan(params)
        elif action == "generate_code":
            return self._handle_generate_code(params)
        elif action == "execute_task":
            return self._handle_execute_task(params)
        elif action == "get_task_status":
            return self._handle_get_task_status(params)
        elif action == "get_plan_status":
            return self._handle_get_plan_status(params)
        else:
            return ToolResult(
                success=False,
                message=f"Unknown action: {action}",
                data=None
            )
    
    def _handle_generate_plan(self, params):
        """プラン生成アクションを処理"""
        if not params or "goal" not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: goal",
                data=None
            )
        
        goal = params["goal"]
        try:
            plan = self.generate_plan(goal)
            return ToolResult(
                success=True,
                message=f"Plan generated for goal: {goal}",
                data={"plan_id": plan.id, "tasks": [t.to_dict() for t in plan.tasks]}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to generate plan: {str(e)}",
                data=None
            )
    
    def _handle_generate_code(self, params):
        """コード生成アクションを処理"""
        if not params or "task_id" not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: task_id",
                data=None
            )
        
        task_id = params["task_id"]
        task = self.task_db.get_task(task_id)
        
        if not task:
            return ToolResult(
                success=False,
                message=f"Task not found: {task_id}",
                data=None
            )
        
        try:
            code = self.generate_python_script(task)
            return ToolResult(
                success=True,
                message=f"Code generated for task: {task_id}",
                data={"code": code}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to generate code: {str(e)}",
                data=None
            )
    
    def _handle_execute_task(self, params):
        """タスク実行アクションを処理"""
        if not params or "task_id" not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: task_id",
                data=None
            )
        
        task_id = params["task_id"]
        task = self.task_db.get_task(task_id)
        
        if not task:
            return ToolResult(
                success=False,
                message=f"Task not found: {task_id}",
                data=None
            )
        
        if not self.python_execute_tool:
            return ToolResult(
                success=False,
                message="Python execute tool not available",
                data=None
            )
        
        try:
            code = self.generate_python_script(task)
            
            result = self.python_execute_tool.execute("run_python", {
                "code": code,
                "task_id": task_id,
                "plan_id": task.plan_id
            })
            
            if result.success:
                task.status = "completed"
                task.result = result.data.get("result", "Task completed")
            else:
                task.status = "failed"
                task.result = result.data.get("error", "Task failed")
            
            self.task_db.update_task(task)
            
            return result
        except Exception as e:
            task.status = "failed"
            task.result = f"Error: {str(e)}"
            self.task_db.update_task(task)
            
            return ToolResult(
                success=False,
                message=f"Failed to execute task: {str(e)}",
                data={"error": str(e)}
            )
    
    def _handle_get_task_status(self, params):
        """タスクステータス取得アクションを処理"""
        if not params or "task_id" not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: task_id",
                data=None
            )
        
        task_id = params["task_id"]
        task = self.task_db.get_task(task_id)
        
        if not task:
            return ToolResult(
                success=False,
                message=f"Task not found: {task_id}",
                data=None
            )
        
        return ToolResult(
            success=True,
            message=f"Task status: {task.status}",
            data=task.to_dict()
        )
    
    def _handle_get_plan_status(self, params):
        """プランステータス取得アクションを処理"""
        if not params or "plan_id" not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: plan_id",
                data=None
            )
        
        plan_id = params["plan_id"]
        plan = self.task_db.get_plan(plan_id)
        
        if not plan:
            return ToolResult(
                success=False,
                message=f"Plan not found: {plan_id}",
                data=None
            )
        
        tasks = self.task_db.get_tasks_for_plan(plan_id)
        
        return ToolResult(
            success=True,
            message=f"Plan status retrieved",
            data={
                "plan": plan.to_dict(),
                "tasks": [t.to_dict() for t in tasks]
            }
        )
    
    def generate_plan(self, goal):
        """目標に基づいてプランを生成"""
        thinking_insights = ""
        if hasattr(self.llm, 'agent') and hasattr(self.llm.agent, 'persistent_thinking_ai'):
            try:
                thinking_ai = self.llm.agent.persistent_thinking_ai
                recent_thoughts = thinking_ai.get_recent_thoughts(limit=5)
                
                if recent_thoughts:
                    thinking_insights = "Recent insights from persistent thinking:\n"
                    for thought in recent_thoughts:
                        thought_type = thought.get("type", "")
                        content = thought.get("content", {})
                        
                        if thought_type == "reflection":
                            thinking_insights += f"- Reflection: {content.get('thought', '')}\n"
                        elif thought_type == "knowledge_update":
                            thinking_insights += f"- Knowledge: {content.get('subject', '')} - {content.get('fact', '')}\n"
                        elif thought_type == "web_knowledge_update":
                            thinking_insights += f"- Web knowledge: {content.get('subject', '')} - {content.get('fact', '')}\n"
            except Exception as e:
                print(f"Error getting thinking insights: {str(e)}")

        prompt = f"""
        Overall Goal: {goal}
        
        {thinking_insights}
        
        Create a plan to achieve this goal. Break it down into smaller, manageable tasks.
        For each task, provide:
        1. A clear description of what needs to be done
        2. Any dependencies on other tasks
        
        Format your response as a JSON object with the following structure:
        {{
            "tasks": [
                {{
                    "description": "Task description",
                    "dependencies": []  // List of task indices that this task depends on
                }},
                // More tasks...
            ]
        }}
        
        Make sure your plan is comprehensive and covers all aspects of the goal.
        """
        
        try:
            plan_json = self.llm.generate_text(prompt)
            plan_json = _fix_json_syntax(plan_json)
            
            plan_data = json.loads(plan_json)
            
            plan = self.task_db.create_plan(goal)
            
            tasks = []
            for i, task_data in enumerate(plan_data.get("tasks", [])):
                description = task_data.get("description", f"Task {i+1}")
                dependencies = []
                
                for dep_idx in task_data.get("dependencies", []):
                    if dep_idx < i and dep_idx >= 0:
                        dependencies.append(tasks[dep_idx].id)
                
                task = self.task_db.create_task(
                    description=description,
                    plan_id=plan.id,
                    dependencies=dependencies
                )
                tasks.append(task)
            
            return plan
        except Exception as e:
            raise ValueError(f"Failed to parse plan: {str(e)}")
    
    def generate_python_script(self, task) -> str:
        """タスク用のPythonスクリプトを生成"""
        plan = self.task_db.get_plan(task.plan_id)
        goal = plan.goal if plan else "Accomplish the task"
        
        dependent_tasks = []
        for dep_id in task.dependencies:
            dep_task = self.task_db.get_task(dep_id)
            if dep_task:
                dependent_tasks.append({
                    "description": dep_task.description,
                    "status": dep_task.status.value,
                    "result": dep_task.result
                })
        
        template = get_template_for_task(task.description)
        
        persistent_thinking_knowledge = ""
        if hasattr(self.llm, 'agent') and hasattr(self.llm.agent, 'persistent_thinking_ai'):
            try:
                thinking_ai = self.llm.agent.persistent_thinking_ai
                if hasattr(thinking_ai, 'get_knowledge_for_script'):
                    knowledge = thinking_ai.get_knowledge_for_script(task.description)
                    if knowledge:
                        persistent_thinking_knowledge = f"""
"""
            except Exception as e:
                print(f"持続思考AIからの知識取得エラー: {str(e)}")
        
        if hasattr(self.llm, 'mock_mode') and self.llm.mock_mode:
            print(f"モックモード: タスク「{task.description}」用のスクリプトを生成します")
            
            task_info_code = f"""task_info = {{
    "task_id": "{task.id}",
    "description": "{task.description}",
    "plan_id": "{task.plan_id}",
}}
"""
            
            mock_main_code = self.llm.generate_code(f"タスク: {task.description}")
            
            missing_modules, mock_main_code = self._check_imports(mock_main_code)
            
            import re
            import_pattern = r'import\s+[\w.]+|from\s+[\w.]+\s+import\s+[\w.,\s]+'
            imports = re.findall(import_pattern, mock_main_code)
            
            main_code_cleaned = re.sub(import_pattern, '', mock_main_code).strip()
            
            imports_text = "\n".join(imports) if imports else "# No additional imports"
            
            main_code_lines = main_code_cleaned.split('\n')
            indented_main_code = []
            for line in main_code_lines:
                if line.strip():  # 空行でない場合
                    if not line.startswith('    '):  # すでにインデントされていない場合
                        indented_main_code.append('        ' + line)  # 8スペースのインデント（try内のコード用）
                    else:
                        indented_main_code.append('    ' + line)
                else:
                    indented_main_code.append(line)  # 空行はそのまま
            
            format_dict = {
                "imports": imports_text,
                "main_code": '\n'.join(indented_main_code),
            }
            
            try:
                if "{imports}" in template and "{main_code}" in template:
                    from string import Template
                    safe_template = template.replace("{imports}", "___IMPORTS___").replace("{main_code}", "___MAIN_CODE___")
                    t = Template(safe_template)
                    full_code = task_info_code + t.safe_substitute({}).replace("___IMPORTS___", format_dict["imports"]).replace("___MAIN_CODE___", format_dict["main_code"])
                else:
                    print("Warning: Template missing required placeholders. Using basic template.")
                    basic_template = r'''
import os
import json
import time
import re
import datetime
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple
{0}

def main():
    try:
{1}

    except Exception as e:
        print(f"Error: {{str(e)}}")
        traceback.print_exc()
        return str(e)
    
    return "Task completed successfully"

if __name__ == "__main__":
    result = main()
'''.format(format_dict["imports"], format_dict["main_code"])
                    full_code = task_info_code + basic_template
                
                missing_modules, full_code = self._check_imports(full_code)
                return full_code
            except Exception as e:
                print(f"Error formatting template: {str(e)}")
                return task_info_code + mock_main_code
        
        thinking_insights = ""
        if hasattr(self.llm, 'agent') and hasattr(self.llm.agent, 'persistent_thinking_ai'):
            try:
                thinking_ai = self.llm.agent.persistent_thinking_ai
                recent_thoughts = thinking_ai.get_recent_thoughts(limit=5)
                
                if recent_thoughts:
                    thinking_insights = "Recent insights from persistent thinking:\n"
                    for thought in recent_thoughts:
                        thought_type = thought.get("type", "")
                        content = thought.get("content", {})
                        
                        if thought_type == "reflection":
                            thinking_insights += f"- Reflection: {content.get('thought', '')}\n"
                        elif thought_type == "knowledge_update":
                            thinking_insights += f"- Knowledge: {content.get('subject', '')} - {content.get('fact', '')}\n"
                        elif thought_type == "web_knowledge_update":
                            thinking_insights += f"- Web knowledge: {content.get('subject', '')} - {content.get('fact', '')}\n"
            except Exception as e:
                print(f"Error getting thinking insights: {str(e)}")
        
        dependencies_info = ""
        if dependent_tasks:
            dependencies_info = "Dependencies:\n"
            for i, dep in enumerate(dependent_tasks):
                dependencies_info += f"{i+1}. {dep['description']} - Status: {dep['status']}\n"
                if dep['result']:
                    dependencies_info += f"   Result: {dep['result']}\n"
        
        prompt = f"""
        Overall Goal: {goal}
        
        Task: {task.description}
        
        {dependencies_info}
        
        {thinking_insights}
        
        {persistent_thinking_knowledge}
        
        Write a Python script to accomplish this task. The script should:
        1. Be well-structured and follow best practices
        2. Include appropriate error handling
        3. Return a result that can be used by dependent tasks
        
        Your code should be complete and ready to execute.
        """
        
        main_code = self.llm.generate_code(prompt)
        
        import re
        import_pattern = r'import\s+[\w.]+|from\s+[\w.]+\s+import\s+[\w.,\s]+'
        imports = re.findall(import_pattern, main_code)
        
        python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                            "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
        
        processed_imports = []
        type_hints_to_import = set()
        
        for imp in imports:
            if any(f"import {hint}" == imp.strip() for hint in python_type_hints):
                hint = imp.strip().replace("import ", "")
                type_hints_to_import.add(hint)
                print(f"⚠️ '{hint}'はPythonの型ヒントです。'from typing import {hint}'に変換します。")
            else:
                processed_imports.append(imp)
        
        if type_hints_to_import:
            processed_imports.append(f"from typing import {', '.join(sorted(type_hints_to_import))}")
        
        imports_text = "\n".join(processed_imports) if processed_imports else "# No additional imports"
        
        main_code_cleaned = re.sub(import_pattern, '', main_code).strip()
        
        task_info_code = f"""task_info = {{
    "task_id": "{task.id}",
    "description": "{task.description}",
    "plan_id": "{task.plan_id}",
}}
"""
        
        format_dict = {
            "imports": imports_text,
            "main_code": main_code_cleaned,
        }
        
        try:
            if "{imports}" in template and "{main_code}" in template:
                from string import Template
                safe_template = template.replace("{imports}", "___IMPORTS___").replace("{main_code}", "___MAIN_CODE___")
                t = Template(safe_template)
                full_code = task_info_code + t.safe_substitute({}).replace("___IMPORTS___", format_dict["imports"]).replace("___MAIN_CODE___", format_dict["main_code"])
            else:
                print("Warning: Template missing required placeholders. Using basic template.")
                basic_template = r'''
import os
import json
import time
import re
import datetime
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple
{0}

def main():
    try:
{1}

    except Exception as e:
        print(f"Error: {{str(e)}}")
        traceback.print_exc()
        return str(e)
    
    return "Task completed successfully"

if __name__ == "__main__":
    result = main()
'''.format(format_dict["imports"], format_dict["main_code"])
                full_code = task_info_code + basic_template
            
            missing_modules, full_code = self._check_imports(full_code)
            return full_code
        except Exception as e:
            print(f"Error formatting template: {str(e)}")
            return task_info_code + imports_text + "\n\n" + main_code_cleaned
    
    def _is_stdlib_module(self, module_name: str):
        """モジュールが標準ライブラリかどうかを判定"""
        import sys
        import importlib.util
        
        stdlib_modules = {
            "os", "sys", "re", "json", "time", "datetime", "math", "random", 
            "collections", "itertools", "functools", "typing", "pathlib", "io",
            "traceback", "logging", "argparse", "unittest", "string", "csv",
            "hashlib", "base64", "uuid", "copy", "shutil", "tempfile", "glob",
            "pickle", "sqlite3", "xml", "html", "urllib", "http", "socket",
            "email", "mimetypes", "zipfile", "tarfile", "gzip", "bz2", "lzma",
            "threading", "multiprocessing", "concurrent", "subprocess", "asyncio",
            "contextlib", "warnings", "enum", "dataclasses", "statistics", "decimal",
            "fractions", "numbers", "cmath", "array", "struct", "codecs", "unicodedata",
            "calendar", "locale", "gettext", "cmd", "configparser", "platform", "gc",
            "inspect", "ast", "dis", "tokenize", "keyword", "textwrap", "difflib",
            "heapq", "bisect", "weakref", "types", "abc", "builtins", "operator",
            "importlib", "pkgutil", "modulefinder", "runpy", "pdb", "doctest",
            "pprint", "reprlib", "enum", "venv", "sysconfig", "site", "signal",
            "atexit", "stat", "fileinput", "fnmatch", "linecache", "rlcompleter",
            "code", "codeop", "timeit", "trace", "profile", "cProfile", "pstats",
            "tabnanny", "compileall", "py_compile", "zipapp", "faulthandler",
            "resource", "posix", "pwd", "grp", "termios", "tty", "pty", "fcntl",
            "pipes", "syslog", "aifc", "audioop", "chunk", "colorsys", "imghdr",
            "sndhdr", "ossaudiodev", "getopt", "optparse", "readline", "nis",
            "curses", "turtle", "smtplib", "poplib", "imaplib", "nntplib", "smtpd",
            "telnetlib", "ftplib", "uu", "xdrlib", "netrc", "cgi", "cgitb",
            "wsgiref", "webbrowser", "uuid", "ipaddress", "hmac", "secrets",
            "ssl", "selectors", "parser", "symbol", "token", "symtable", "zoneinfo"
        }
        
        if module_name in stdlib_modules:
            return True
        
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return False
            
            for path in sys.path:
                if path.endswith(("site-packages", "dist-packages")):
                    continue  # サードパーティのパスはスキップ
                
                if spec.origin and spec.origin.startswith(path):
                    return True
            
            return False
        except (ImportError, AttributeError, ValueError):
            return False
    
    def _check_imports(self, code: str) -> tuple:
        """Detect missing modules from import statements in code and fix direct type hint imports.
        
        Args:
            code: The Python code to check
            
        Returns:
            A tuple of (missing_modules, fixed_code)
        """
        import re
        
        python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                            "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
        
        direct_imports_to_fix = []
        for hint in python_type_hints:
            if re.search(r'import\s+' + hint + r'\s*$', code, re.MULTILINE):
                direct_imports_to_fix.append(hint)
                code = re.sub(r'import\s+' + hint + r'\s*($|\n)', '', code)
                print(f"Warning: '{hint}' is a Python type hint. Converting to 'from typing import {hint}'.")
        
        if direct_imports_to_fix:
            typing_import_match = re.search(r'from\s+typing\s+import\s+([^\n]+)', code)
            if typing_import_match:
                existing_imports = typing_import_match.group(1)
                existing_hints = [hint.strip() for hint in existing_imports.split(',')]
                
                for hint in direct_imports_to_fix:
                    if hint not in existing_hints:
                        existing_hints.append(hint)
                
                new_typing_import = f"from typing import {', '.join(sorted(existing_hints))}"
                code = re.sub(r'from\s+typing\s+import\s+([^\n]+)', new_typing_import, code)
            else:
                new_typing_import = f"from typing import {', '.join(sorted(direct_imports_to_fix))}"
                
                first_import_match = re.search(r'^(import|from)\s+', code, re.MULTILINE)
                if first_import_match:
                    pos = first_import_match.start()
                    code = code[:pos] + new_typing_import + "\n" + code[pos:]
                else:
                    code = new_typing_import + "\n\n" + code
        
        import_pattern = r'(?:from|import)\s+([\w.]+)'
        imports = re.findall(import_pattern, code)
        
        missing = []
        for imp in imports:
            module_name = imp.split('.')[0]
            
            if self._is_stdlib_module(module_name):
                continue
                
            if module_name in python_type_hints or module_name == 'typing':
                continue
            
            try:
                __import__(module_name)
            except ImportError:
                if module_name not in missing:
                    missing.append(module_name)
        
        return missing, code

def _fix_json_syntax(json_str):
    """JSONの構文を修正"""
    json_str = re.sub(r'```json', '', json_str)
    json_str = re.sub(r'```', '', json_str)
    
    json_str = json_str.strip()
    
    return json_str
