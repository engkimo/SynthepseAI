import os
import sys
import unittest
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.task_database import TaskDatabase, TaskStatus
from core.tools.planning_tool import PlanningTool
from core.tools.file_tool import FileTool
from core.auto_plan_agent import AutoPlanAgent
from core.planning_flow import PlanningFlow

class RegressionTestBasicTasks(unittest.TestCase):
    """新コンポーネント追加後の基本機能の回帰テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.skipTest("OPENAI_API_KEY environment variable not set")
            
        self.test_workspace = tempfile.mkdtemp()
        
        self.llm = LLM(
            api_key=api_key,
            model="gpt-3.5-turbo"
        )
        
        self.task_db = TaskDatabase(":memory:")
        
        self.planning_tool = PlanningTool(self.llm, self.task_db)
        self.file_tool = FileTool(self.test_workspace)
        
        self.agent = AutoPlanAgent(
            "TestAgent",
            "Test agent for regression testing",
            self.llm,
            self.task_db,
            self.test_workspace
        )
        self.agent.set_planner(self.planning_tool)
        self.agent.available_tools.add_tool(self.file_tool)
        
        self.flow = PlanningFlow(self.llm, self.task_db)
        self.flow.add_agent("auto_plan", self.agent)
        self.flow.set_planning_tool(self.planning_tool)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.test_workspace, ignore_errors=True)
    
    def test_basic_text_generation(self):
        """基本的なテキスト生成機能のテスト"""
        prompt = "What is Python?"
        response = self.llm.generate_text(prompt)
        
        self.assertIsNotNone(response)
        self.assertTrue(len(response) > 0)
        self.assertIn("Python", response)
    
    def test_task_database(self):
        """タスクデータベースの基本機能テスト"""
        plan_id = "test_plan_001"
        task_id = self.task_db.add_task(
            plan_id=plan_id,
            description="Print a simple message",
            code="print('Hello, World!')",
            status=TaskStatus.PENDING
        )
        
        task = self.task_db.get_task(task_id)
        self.assertEqual(task.description, "Print a simple message")
        self.assertEqual(task.status, TaskStatus.PENDING)
        
        self.task_db.update_task_status(task_id, TaskStatus.COMPLETED)
        
        updated_task = self.task_db.get_task(task_id)
        self.assertEqual(updated_task.status, TaskStatus.COMPLETED)
        
        plan_tasks = self.task_db.get_tasks_for_plan(plan_id)
        self.assertEqual(len(plan_tasks), 1)
        self.assertEqual(plan_tasks[0].id, task_id)
    
    def test_planning_tool(self):
        """プランニングツールの基本機能テスト"""
        class MockExecutor:
            def execute(self, command, **kwargs):
                class Result:
                    def __init__(self, success, result=None, error=None):
                        self.success = success
                        self.result = result
                        self.error = error
                
                if command == "create_plan":
                    return Result(True, {"plan_id": "test_plan_002", "steps": [
                        {"step_id": "step1", "description": "Create a simple text file"}
                    ]})
                elif command == "get_plan":
                    return Result(True, {"plan_id": "test_plan_002", "steps": [
                        {"step_id": "step1", "description": "Create a simple text file", "status": "pending"}
                    ]})
                else:
                    return Result(False, None, f"Unknown command: {command}")
        
        self.planning_tool.executor = MockExecutor()
        
        result = self.planning_tool.execute(
            command="create_plan",
            goal="Create a simple text file"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.result["plan_id"], "test_plan_002")
        
        result = self.planning_tool.execute(
            command="get_plan",
            plan_id="test_plan_002"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.result["plan_id"], "test_plan_002")
        self.assertEqual(len(result.result["steps"]), 1)
    
    def test_file_tool(self):
        """ファイルツールの基本機能テスト"""
        file_path = os.path.join(self.test_workspace, "test.txt")
        content = "Hello, World!"
        
        result = self.file_tool.execute(
            command="write_file",
            path="test.txt",
            content=content
        )
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(file_path))
        
        with open(file_path, "r") as f:
            file_content = f.read()
        self.assertEqual(file_content, content)
        
        result = self.file_tool.execute(
            command="read_file",
            path="test.txt"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.result, content)
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        result = self.file_tool.execute(
            command="read_file",
            path="non_existent.txt"
        )
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
        self.assertIn("not found", result.error.lower())
        
        result = self.file_tool.execute(
            command="invalid_command",
            path="test.txt"
        )
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
        self.assertIn("unknown command", result.error.lower())
    
    def test_auto_plan_agent(self):
        """AutoPlanAgentの基本機能テスト"""
        class MockExecutor:
            def execute(self, command, **kwargs):
                class Result:
                    def __init__(self, success, result=None, error=None):
                        self.success = success
                        self.result = result
                        self.error = error
                
                if command == "execute_code":
                    return Result(True, "Code executed successfully")
                else:
                    return Result(True, f"Command {command} executed")
        
        self.agent.project_executor = MockExecutor()
        
        task_id = self.task_db.add_task(
            plan_id="test_plan_003",
            description="Print a simple message",
            code="print('Hello, World!')",
            status=TaskStatus.PENDING
        )
        
        result = self.agent.execute_task(task_id)
        
        self.assertTrue(result)
        
        task = self.task_db.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
    
    def test_planning_flow(self):
        """PlanningFlowの基本機能テスト"""
        class MockExecutor:
            def execute(self, command, **kwargs):
                class Result:
                    def __init__(self, success, result=None, error=None):
                        self.success = success
                        self.result = result
                        self.error = error
                
                if command == "create_plan":
                    return Result(True, {"plan_id": "test_plan_004", "steps": [
                        {"step_id": "step1", "description": "Create a simple text file"}
                    ]})
                elif command == "get_step":
                    return Result(True, {
                        "step_id": "step1",
                        "description": "Create a simple text file",
                        "status": "pending"
                    })
                elif command == "execute_step":
                    with open(os.path.join(self.test_workspace, "test.txt"), "w") as f:
                        f.write("Hello, World!")
                    return Result(True, "Step executed successfully")
                elif command == "mark_step_completed":
                    return Result(True, "Step marked as completed")
                else:
                    return Result(False, None, f"Unknown command: {command}")
        
        self.agent.project_executor = MockExecutor()
        self.planning_tool.executor = MockExecutor()
        
        goal = "Create a simple text file"
        
        try:
            result = self.flow.execute(goal)
            
            self.assertIsNotNone(result)
            
            file_path = os.path.join(self.test_workspace, "test.txt")
            self.assertTrue(os.path.exists(file_path))
            
            with open(file_path, "r") as f:
                content = f.read()
            self.assertEqual(content, "Hello, World!")
            
        except Exception as e:
            self.fail(f"Flow execution failed with error: {str(e)}")

if __name__ == '__main__':
    unittest.main()
