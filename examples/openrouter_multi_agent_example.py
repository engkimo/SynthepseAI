"""
OpenRouter マルチエージェント討論の使用例

このスクリプトは、OpenRouterを通じてClaude 3.7モデルを使用した
マルチエージェント討論機能の使用方法を示します。
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from core.multi_agent_discussion import MultiAgentDiscussion, DiscussionAgent
from core.openrouter_integration import OpenRouterChatModel

def main():
    """メイン関数"""
    print("=== OpenRouter マルチエージェント討論デモ ===\n")
    
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("警告: OPENROUTER_API_KEY環境変数が設定されていません。")
        print("以下のコマンドでAPIキーを設定してください:")
        print("export OPENROUTER_API_KEY=your_api_key_here")
        print("\nデモモードで実行します（実際のAPIコールは行われません）。")
        openrouter_api_key = "dummy_key_for_testing"
    
    workspace_dir = Path("./workspace/demo_multi_agent")
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    knowledge_db_path = workspace_dir / "knowledge_db.json"
    log_path = workspace_dir / "thinking_log.jsonl"
    
    discussion = MultiAgentDiscussion(
        knowledge_db_path=str(knowledge_db_path),
        log_path=str(log_path)
    )
    
    agents_config = [
        {
            "name": "コードエキスパート",
            "role": "プログラミング専門家",
            "expertise": ["コード生成", "デバッグ", "最適化"],
            "model_name": "anthropic/claude-3-7-sonnet",
            "temperature": 0.3,
            "provider": "openrouter",
            "api_key": openrouter_api_key
        },
        {
            "name": "リサーチャー",
            "role": "研究者",
            "expertise": ["データ分析", "情報検索", "文献調査"],
            "model_name": "anthropic/claude-3-5-sonnet",
            "temperature": 0.5,
            "provider": "openrouter",
            "api_key": openrouter_api_key
        },
        {
            "name": "クリティカルシンカー",
            "role": "批判的思考家",
            "expertise": ["論理分析", "仮説検証", "反論提示"],
            "model_name": "anthropic/claude-3-5-sonnet",
            "temperature": 0.7,
            "provider": "openrouter",
            "api_key": openrouter_api_key
        }
    ]
    
    for agent_config in agents_config:
        if agent_config.get("provider") == "openrouter":
            try:
                chat_model = OpenRouterChatModel(
                    api_key=agent_config.get("api_key"),
                    model_name=agent_config.get("model_name"),
                    temperature=agent_config.get("temperature", 0.7)
                )
                
                agent = DiscussionAgent(
                    name=agent_config.get("name"),
                    role=agent_config.get("role"),
                    expertise=agent_config.get("expertise"),
                    llm=chat_model  # LLMを直接渡す
                )
                
                discussion.add_agent(agent)
                print(f"エージェント追加: {agent_config.get('name')} ({agent_config.get('role')})")
                print(f"  モデル: {agent_config.get('model_name')} (OpenRouter経由)")
                
            except Exception as e:
                print(f"エージェント追加エラー: {str(e)}")
        
        else:
            try:
                agent = DiscussionAgent(
                    name=agent_config.get("name"),
                    role=agent_config.get("role"),
                    expertise=agent_config.get("expertise"),
                    model_name=agent_config.get("model_name"),
                    temperature=agent_config.get("temperature", 0.7),
                    api_key=agent_config.get("api_key")
                )
                
                discussion.add_agent(agent)
                print(f"エージェント追加: {agent_config.get('name')} ({agent_config.get('role')})")
                print(f"  モデル: {agent_config.get('model_name')}")
                
            except Exception as e:
                print(f"エージェント追加エラー: {str(e)}")
    
    topic = "Pythonでの効率的なデータ処理と可視化の最適なアプローチ"
    
    print(f"\n討論トピック: {topic}")
    print("討論を開始します...\n")
    
    if openrouter_api_key != "dummy_key_for_testing":
        try:
            start_time = time.time()
            result = discussion.conduct_discussion(topic=topic, rounds=2)
            end_time = time.time()
            
            print(f"\n討論完了 (所要時間: {end_time - start_time:.2f}秒)")
            
            if result and "consensus" in result:
                print("\n=== 討論の合意点 ===")
                print(result["consensus"])
                
                if os.path.exists(knowledge_db_path):
                    with open(knowledge_db_path, 'r', encoding='utf-8') as f:
                        knowledge_db = json.load(f)
                        print(f"\n知識DBに保存された項目数: {len(knowledge_db)}")
                
                if os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as f:
                        log_entries = [json.loads(line) for line in f]
                        print(f"思考ログに記録されたエントリ数: {len(log_entries)}")
            else:
                print("\n討論結果が取得できませんでした。")
        
        except Exception as e:
            print(f"\n討論実行エラー: {str(e)}")
    else:
        print("\nデモモードでは実際の討論は実行されません。")
        print("実際に使用するには、OpenRouter APIキーを設定してください。")

if __name__ == "__main__":
    main()
