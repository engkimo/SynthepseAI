#!/usr/bin/env python3
"""
継続的思考AIの双方向同期強化のテストスクリプト
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_knowledge_sync():
    """強化された知識同期をテスト"""
    print("=== 継続的思考AIの双方向同期強化テスト ===")
    
    try:
        from core.enhanced_persistent_thinking_ai import EnhancedPersistentThinkingAI
        
        ai = EnhancedPersistentThinkingAI(
            workspace_dir="./workspace",
            knowledge_db_path="./workspace/persistent_thinking/knowledge_db.json",
            log_path="./workspace/persistent_thinking/thinking_log.jsonl",
            use_compatibility_mode=True,
            llm_provider="openai"
        )
        
        test_goal = "データ分析スクリプトの自動生成と改善"
        
        print(f"テスト目標: {test_goal}")
        
        print("\n1. 目標指向の継続的思考を開始...")
        ai.start_continuous_thinking(
            initial_task=test_goal,
            thinking_goal="データ分析の効率化と品質向上"
        )
        
        print("\n2. スクリプト生成用の知識を取得...")
        knowledge = ai.get_knowledge_for_script(test_goal)
        
        print(f"関連知識: {len(knowledge['related_knowledge'])}件")
        print(f"成功パターン: {len(knowledge['success_patterns'])}件")
        print(f"失敗パターン: {len(knowledge['failure_patterns'])}件")
        print(f"最適化ヒント: {len(knowledge['optimization_tips'])}件")
        
        print("\n3. タスク実行結果の統合をテスト...")
        test_result = """
        データ分析スクリプトを正常に生成しました。
        使用ライブラリ: pandas, matplotlib, seaborn
        処理時間: 2.3秒
        生成されたグラフ: 3個
        エラー: なし
        """
        
        integration_success = ai.integrate_task_results(test_goal, test_result)
        print(f"結果統合: {'成功' if integration_success else '失敗'}")
        
        print("\n4. 継続的思考を実行中...")
        time.sleep(5)
        
        print("\n5. 思考状態を確認...")
        thinking_state = ai.get_thinking_state()
        print(f"現在のタスク: {thinking_state.get('current_task', 'なし')}")
        print(f"反省回数: {len(thinking_state.get('reflections', []))}")
        print(f"知識更新回数: {len(thinking_state.get('knowledge_updates', []))}")
        
        print("\n6. 継続的思考を停止...")
        ai.stop_continuous_thinking()
        
        print("\n=== テスト完了 ===")
        return True
        
    except ImportError as e:
        print(f"インポートエラー: {str(e)}")
        print("モックモードでテストを実行します...")
        
        print("\n=== モックテスト実行 ===")
        print("1. 知識ベースの読み込みテスト...")
        
        knowledge_db_path = "./workspace/persistent_thinking/knowledge_db.json"
        if os.path.exists(knowledge_db_path):
            with open(knowledge_db_path, 'r', encoding='utf-8') as f:
                knowledge_db = json.load(f)
            print(f"知識ベース項目数: {len(knowledge_db)}")
        else:
            print("知識ベースファイルが見つかりません")
        
        print("\n2. 思考ログの読み込みテスト...")
        thinking_log_path = "./workspace/persistent_thinking/thinking_log.jsonl"
        if os.path.exists(thinking_log_path):
            with open(thinking_log_path, 'r', encoding='utf-8') as f:
                log_entries = [json.loads(line.strip()) for line in f if line.strip()]
            print(f"思考ログエントリ数: {len(log_entries)}")
        else:
            print("思考ログファイルが見つかりません")
        
        print("\n3. スクリプトテンプレート機能テスト...")
        try:
            from core.script_templates import get_relevant_knowledge, apply_success_patterns, avoid_failure_patterns
            
            test_keywords = ["データ", "分析", "スクリプト"]
            relevant_knowledge = get_relevant_knowledge(test_keywords)
            print(f"関連知識取得: {len(relevant_knowledge)}件")
            
            success_patterns = apply_success_patterns("データ分析")
            print(f"成功パターン: {len(success_patterns)}件")
            
            failure_patterns = avoid_failure_patterns("データ分析")
            print(f"失敗パターン: {len(failure_patterns)}件")
            
        except Exception as template_error:
            print(f"スクリプトテンプレート機能エラー: {str(template_error)}")
        
        print("\n=== モックテスト完了 ===")
        return True

if __name__ == "__main__":
    try:
        test_enhanced_knowledge_sync()
    except Exception as e:
        print(f"テスト中にエラーが発生: {str(e)}")
        import traceback
        traceback.print_exc()
