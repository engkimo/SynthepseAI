import sys
import os
sys.path.append('.')
import time

from core.persistent_thinking_ai import PersistentThinkingAI
from core.rome_model_editor import ROMEModelEditor, EditRequest
from core.coat_reasoner import COATReasoner
from core.rgcn_processor import RGCNProcessor

def main():
    """
    LLLM（Larger LLM）統合デモ
    ROME、COAT、R-GCNを組み合わせた持続思考型AIの実装例
    """
    workspace_dir = "./workspace/lllm_integration"
    os.makedirs(workspace_dir, exist_ok=True)
    
    print("=== LLLM（Larger LLM）統合デモ ===")
    print("ROME、COAT、R-GCNを組み合わせた持続思考型AIの実装例")
    print("初期化中...")
    
    ai = PersistentThinkingAI(
        model_name="microsoft/phi-2",
        workspace_dir=workspace_dir,
        knowledge_db_path=f"{workspace_dir}/knowledge_db.json",
        log_path=f"{workspace_dir}/thinking_log.jsonl",
        device="cpu"  # MacBookの場合は"mps"も選択可能
    )
    
    print("\n=== 1. ROMEによる知識編集のデモ ===")
    subject = "東京"
    original_fact = "日本の首都"
    new_fact = "日本の首都であり、世界最大の都市圏の一つ"
    
    print(f"知識編集: {subject} - {original_fact} → {new_fact}")
    
    edit_success = ai.llm.edit_knowledge(
        subject=subject,
        target_fact=new_fact,
        original_fact=original_fact
    )
    
    print(f"編集結果: {'成功' if edit_success else '失敗'}")
    
    print("\n=== 2. COATによる自己反省型推論のデモ ===")
    task_description = "Pythonで素数を判定する関数を作成する方法を考えてください"
    current_state = "まだ素数判定の知識がありません"
    
    print(f"タスク: {task_description}")
    print("COAT推論チェーンを生成中...")
    
    coat_result = ai.coat_reasoner.generate_action_thought_chain(
        task_description=task_description,
        current_state=current_state
    )
    
    print("\nCOAT推論チェーン:")
    for i, step in enumerate(coat_result.get("coat_chain", [])[:3]):  # 最初の3ステップのみ表示
        print(f"ステップ {i+1}:")
        print(f"  行動: {step.get('action', '')[:100]}...")
        print(f"  思考: {step.get('thought', '')[:100]}...")
    
    print(f"\n最終解決策: {coat_result.get('final_solution', '')[:150]}...")
    
    print("\n=== 3. R-GCNによる知識グラフ処理のデモ ===")
    
    triples = [
        ("東京", "は", "日本の首都"),
        ("日本", "の首都は", "東京"),
        ("東京", "には", "スカイツリー"),
        ("東京", "には", "東京タワー"),
        ("大阪", "は", "日本の都市"),
        ("大阪", "には", "通天閣"),
        ("京都", "は", "日本の古都"),
        ("京都", "には", "金閣寺"),
        ("東京", "から", "大阪"),
        ("大阪", "から", "京都")
    ]
    
    print(f"知識トリプル数: {len(triples)}")
    print("知識グラフを構築中...")
    
    graph = ai.rgcn_processor.build_graph(triples)
    
    entity = "東京"
    print(f"\n'{entity}'に関連するエンティティを検索:")
    related = ai.rgcn_processor.find_related_entities(entity, top_k=3)
    
    for i, item in enumerate(related):
        print(f"  {i+1}. {item.get('entity', '')}")
    
    print("\n=== 4. 統合デモ - タスク実行と継続思考 ===")
    task = "日本の主要都市について簡単な情報をまとめてください"
    print(f"タスク: {task}")
    
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
    
    print("\n=== デモ完了 ===")
    print("LLLM（Larger LLM）統合が正常に動作しました")

if __name__ == "__main__":
    main()
