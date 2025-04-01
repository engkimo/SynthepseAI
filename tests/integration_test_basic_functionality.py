import unittest
import os
import sys
import tempfile
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.auto_plan_agent import AutoPlanAgent
from core.task_database import TaskDatabase, TaskStatus
from core.tools.planning_tool import PlanningTool
from core.tools.file_tool import FileTool
from core.planning_flow import PlanningFlow
from core.rome_model_editor import ROMEModelEditor
from core.coat_reasoner import COATReasoner
from core.rgcn_processor import RGCNProcessor

class TestBasicFunctionality(unittest.TestCase):
    """基本機能が新コンポーネント追加後も正常に動作するかのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.skipTest("OPENAI_API_KEY environment variable not set")
            
        self.test_workspace = tempfile.mkdtemp()
        
        self.rome_editor = ROMEModelEditor()
        self.llm = LLM(
            api_key=api_key,
            model="gpt-3.5-turbo",
            rome_model_editor=self.rome_editor
        )
        
        self.coat_reasoner = COATReasoner(self.llm)
        
        self.rgcn_processor = RGCNProcessor()
        
        self.task_db = TaskDatabase(":memory:")
        
        self.planning_tool = PlanningTool(self.llm, self.task_db)
        self.file_tool = FileTool(self.test_workspace)
        
        self.agent = AutoPlanAgent(
            "TestAgent",
            "Test agent for basic functionality",
            self.llm,
            self.task_db,
            self.test_workspace,
            coat_reasoner=self.coat_reasoner
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
    
    def test_simple_task_execution(self):
        """シンプルなタスク実行のテスト"""
        class MockExecutor:
            def execute(self, command, **kwargs):
                class Result:
                    def __init__(self, success, result=None, error=None):
                        self.success = success
                        self.result = result
                        self.error = error
                
                if command == "create_plan":
                    return Result(True, {"plan_id": "test_plan_001", "steps": [
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
    
    def test_llm_with_rome(self):
        """ROMEを統合したLLMの基本機能テスト"""
        prompt = "What is Python?"
        response = self.llm.generate_text(prompt)
        
        self.assertIsNotNone(response)
        self.assertTrue(len(response) > 0)
    
    def test_agent_with_coat(self):
        """COATを統合したAgentの基本機能テスト"""
        task_id = self.task_db.add_task(
            plan_id="test_plan_002",
            description="Print a simple message",
            code="print('Hello, World!')",
            status=TaskStatus.PENDING
        )
        
        task = self.task_db.get_task(task_id)
        self.assertEqual(task.description, "Print a simple message")
        
        self.assertIsNotNone(self.agent.coat_reasoner)
        self.assertEqual(self.agent.coat_reasoner, self.coat_reasoner)

if __name__ == '__main__':
    unittest.main()
