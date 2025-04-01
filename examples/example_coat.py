import os
import sys
import tempfile
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.coat_reasoner import COATReasoner
from core.auto_plan_agent import AutoPlanAgent
from core.task_database import TaskDatabase, Task, TaskStatus

load_dotenv()

def demonstrate_coat_self_correction():
    """
    COATを使用した自己反省型推論機能のデモンストレーション
    
    このデモでは、COATを使用してコードのエラーを自己修正する能力を検証します。
    1. エラーを含むコードを作成
    2. COATリーズナーを使用してエラーを分析
    3. 修正案を生成
    4. 修正の効果を検証
    """
    print("=== COAT Self-Correction Demonstration ===")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    llm = LLM(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    )
    
    coat_reasoner = COATReasoner(llm)
    
    print("\n--- Test 1: Fixing Index Error ---")
    
    buggy_code1 = """
def get_first_element(items):
    return items[0]  # インデックスエラーの可能性あり

result = get_first_element([])
print(f"Result: {result}")
"""
    
    print("Original code with error:")
    print(buggy_code1)
    
    error_message1 = "IndexError: list index out of range"
    print(f"\nError message: {error_message1}")
    
    print("\nApplying COAT reasoning...")
    fixed_code1, coat_chain1 = coat_reasoner.apply_coat_reasoning(
        code=buggy_code1,
        error_message=error_message1
    )
    
    print("\nFixed code:")
    print(fixed_code1)
    
    print("\nCOAT reasoning chain:")
    for i, step in enumerate(coat_chain1):
        print(f"Step {i+1}:")
        print(f"  Thought: {step['thought']}")
        print(f"  Action: {step['action']}")
        print(f"  Prediction: {step['prediction']}")
    
    if "if" in fixed_code1.lower() and "len" in fixed_code1.lower():
        print("\n✅ Code successfully fixed with proper checks!")
    else:
        print("\n❌ Code fix incomplete or incorrect")
    
    print("\n\n--- Test 2: Fixing Type Error ---")
    
    buggy_code2 = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)  # ゼロ除算の可能性あり

result = calculate_average([])
print(f"Average: {result}")
"""
    
    print("Original code with error:")
    print(buggy_code2)
    
    error_message2 = "ZeroDivisionError: division by zero"
    print(f"\nError message: {error_message2}")
    
    print("\nApplying COAT reasoning...")
    fixed_code2, coat_chain2 = coat_reasoner.apply_coat_reasoning(
        code=buggy_code2,
        error_message=error_message2
    )
    
    print("\nFixed code:")
    print(fixed_code2)
    
    print("\nCOAT reasoning chain:")
    for i, step in enumerate(coat_chain2):
        print(f"Step {i+1}:")
        print(f"  Thought: {step['thought']}")
        print(f"  Action: {step['action']}")
        print(f"  Prediction: {step['prediction']}")
    
    if "if" in fixed_code2.lower() and "len" in fixed_code2.lower() and "return" in fixed_code2.lower():
        print("\n✅ Code successfully fixed with proper checks!")
    else:
        print("\n❌ Code fix incomplete or incorrect")
    
    print("\n\n--- Test 3: Integration with AutoPlanAgent ---")
    
    workspace_dir = tempfile.mkdtemp()
    print(f"Created temporary workspace: {workspace_dir}")
    
    task_db = TaskDatabase(":memory:")
    
    agent = AutoPlanAgent(
        "TestAgent",
        "Test agent for COAT integration",
        llm,
        task_db,
        workspace_dir,
        coat_reasoner=coat_reasoner
    )
    
    plan_id = "test_plan_001"
    task_id = task_db.add_task(
        plan_id=plan_id,
        description="リストの最初の要素を取得する",
        code=buggy_code1,
        status=TaskStatus.FAILED,
        error=error_message1
    )
    
    print(f"Created task with ID: {task_id}")
    
    class MockExecutor:
        def execute(self, command, task_id):
            class Result:
                def __init__(self, success, result=None, error=None):
                    self.success = success
                    self.result = result
                    self.error = error
            return Result(True, "Test passed")
    
    agent.project_executor = MockExecutor()
    
    print("\nAttempting to repair failed task...")
    result = agent.repair_failed_task(task_id)
    
    print(f"Repair result: {result}")
    
    repaired_task = task_db.get_task(task_id)
    print(f"\nTask status after repair: {repaired_task.status}")
    
    print("\nRepaired code:")
    print(repaired_task.code)
    
    if repaired_task.status == TaskStatus.COMPLETED and "if" in repaired_task.code.lower():
        print("\n✅ Task successfully repaired by AutoPlanAgent using COAT!")
    else:
        print("\n❌ Task repair failed or incomplete")
    
    import shutil
    shutil.rmtree(workspace_dir, ignore_errors=True)
    print(f"\nRemoved temporary workspace: {workspace_dir}")
    
    print("\n=== COAT Self-Correction Demonstration Complete ===")

if __name__ == "__main__":
    demonstrate_coat_self_correction()
