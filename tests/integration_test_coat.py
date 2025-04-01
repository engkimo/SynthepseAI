import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.coat_reasoner import COATReasoner
from core.auto_plan_agent import AutoPlanAgent
from core.task_database import TaskDatabase, Task, TaskStatus

class TestCOATIntegration(unittest.TestCase):
    """COATの自己反省型推論機能の統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.skipTest("OPENAI_API_KEY environment variable not set")
            
        self.llm = LLM(api_key=api_key, model="gpt-3.5-turbo")
        
        self.coat_reasoner = COATReasoner(self.llm)
        
        self.task_db = TaskDatabase(":memory:")
        
        self.agent = AutoPlanAgent(
            "TestAgent",
            "Test agent for COAT integration",
            self.llm,
            self.task_db,
            "./test_workspace",
            coat_reasoner=self.coat_reasoner
        )
    
    def test_coat_reasoning_chain_generation(self):
        """COAT推論チェーン生成のテスト"""
        task_description = "リストの最初の要素を取得する関数を実装する"
        current_state = "現在のコード:\n```python\ndef get_first_element(items):\n    return items[0]\n```"
        error_message = "IndexError: list index out of range"
        
        coat_chain = self.coat_reasoner.generate_action_thought_chain(
            task_description=task_description,
            current_state=current_state,
            error_message=error_message
        )
        
        self.assertIn("coat_chain", coat_chain)
        self.assertIn("final_solution", coat_chain)
        self.assertTrue(len(coat_chain["coat_chain"]) >= 1)
        
        for step in coat_chain["coat_chain"]:
            self.assertIn("thought", step)
            self.assertIn("action", step)
            self.assertIn("prediction", step)
    
    def test_coat_code_repair(self):
        """COATによるコード修正のテスト"""
        buggy_code = """
def process_list(items):
    return items[0]  # インデックスエラーの可能性あり
"""
        error_message = "IndexError: list index out of range"
        
        fixed_code, coat_chain = self.coat_reasoner.apply_coat_reasoning(
            code=buggy_code,
            error_message=error_message
        )
        
        self.assertIn("if", fixed_code.lower())
        self.assertIn("len", fixed_code.lower())
        
        self.assertTrue(len(coat_chain) >= 1)
    
    def test_auto_plan_agent_integration(self):
        """AutoPlanAgentとの統合テスト"""
        plan_id = "test_plan_001"
        task_id = self.task_db.add_task(
            plan_id=plan_id,
            description="リストの最初の要素を取得する",
            code="""
def get_first_element(items):
    return items[0]  # インデックスエラーの可能性あり

result = get_first_element([])
print(f"Result: {result}")
""",
            status=TaskStatus.FAILED,
            error="IndexError: list index out of range"
        )
        
        class MockExecutor:
            def execute(self, command, task_id):
                class Result:
                    def __init__(self, success, result=None, error=None):
                        self.success = success
                        self.result = result
                        self.error = error
                return Result(True, "Test passed")
        
        self.agent.project_executor = MockExecutor()
        
        result = self.agent.repair_failed_task(task_id)
        
        self.assertTrue(result)
        
        repaired_task = self.task_db.get_task(task_id)
        self.assertEqual(repaired_task.status, TaskStatus.COMPLETED)
        
        self.assertIn("if", repaired_task.code.lower())
        self.assertIn("len", repaired_task.code.lower())

if __name__ == '__main__':
    unittest.main()
