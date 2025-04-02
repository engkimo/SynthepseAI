import sys
import os
sys.path.append('.')

from core.llm import LLM
from core.tools.planning_tool import PlanningTool
from core.task_database import TaskDatabase

def test_planning_tool_json_parsing():
    """プランニングツールのJSON解析機能をテスト"""
    print("=== プランニングツールのJSON解析テスト ===")
    
    db_path = ":memory:"  # インメモリデータベース
    task_db = TaskDatabase(db_path)
    
    try:
        from core.local_model_manager import LocalModelManager
        llm = LLM(
            api_key=None,
            model="gpt-4-turbo",
            temperature=0.7,
            use_local_model=True,
            local_model_name="microsoft/phi-2",
            device=None
        )
    except Exception as e:
        print(f"ローカルモデルのロードエラー: {str(e)}")
        print("OpenAI APIを使用します")
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OpenAI API key not found in environment variables")
            return
        llm = LLM(api_key=api_key)
    
    planning_tool = PlanningTool(llm, task_db)
    
    goals = [
        "財務省はなぜデモを受けているか調べて",
        "東京の天気予報を教えてください",
        "人工知能の最新研究について調査する"
    ]
    
    for goal in goals:
        print(f"\n目標: '{goal}'")
        try:
            result = planning_tool._handle_generate_plan(goal=goal)
            print(f"成功: {result.result}")
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    english_goals = [
        "Research the latest advancements in AI",
        "Create a simple web scraper",
        "Analyze stock market data"
    ]
    
    for goal in english_goals:
        print(f"\n目標: '{goal}'")
        try:
            result = planning_tool._handle_generate_plan(goal=goal)
            print(f"成功: {result.result}")
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_planning_tool_json_parsing()
