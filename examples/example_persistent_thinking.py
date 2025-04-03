import sys
import os
sys.path.append('.')
import time

from core.persistent_thinking_ai import PersistentThinkingAI

def main():
    workspace_dir = "./workspace/persistent_thinking"
    os.makedirs(workspace_dir, exist_ok=True)
    
    print("Initializing PersistentThinkingAI...")
    ai = PersistentThinkingAI(
        model_name="microsoft/phi-2",
        workspace_dir=workspace_dir,
        knowledge_db_path=f"{workspace_dir}/knowledge_db.json",
        log_path=f"{workspace_dir}/thinking_log.jsonl",
        device="cpu"
    )
    
    task = "簡単な計算機プログラムを作成してください"
    print(f"\n実行するタスク: {task}\n")
    
    result = ai.execute_task(task)
    print("\n実行結果:")
    print(result)
    
    thinking_state = ai.get_thinking_state()
    print("\n思考状態:")
    print(f"反省の数: {len(thinking_state['reflections'])}")
    print(f"知識更新の数: {len(thinking_state['knowledge_updates'])}")
    
    print("\n10秒間の継続思考を実行...")
    ai.continuous_thinking(duration_seconds=10)
    
    thinking_state = ai.get_thinking_state()
    print("\n更新された思考状態:")
    print(f"反省の数: {len(thinking_state['reflections'])}")
    
    print("\n継続思考後の新しい反省:")
    for i, reflection in enumerate(thinking_state['reflections'][-3:]):
        print(f"反省 {i+1}: {reflection.get('content', '')[:100]}...")

if __name__ == "__main__":
    main()
