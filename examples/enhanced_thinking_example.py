"""
EnhancedPersistentThinkingAI の使用例

このスクリプトは、EnhancedPersistentThinkingAIの機能を示すための例です。
持続的思考、Webクローリング、知識データベースの更新などの機能をデモンストレーションします。
"""

import os
import sys
import time
import json
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core.enhanced_persistent_thinking_ai import EnhancedPersistentThinkingAI
from core.tools.web_crawling_tool import WebCrawlingTool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def main():
    workspace_dir = Path("./workspace/enhanced_thinking_example")
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    knowledge_db_path = workspace_dir / "knowledge_db.json"
    log_path = workspace_dir / "thinking_log.jsonl"
    
    config_path = Path("./config.json")
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}
    
    thinking_ai = EnhancedPersistentThinkingAI(
        model_name=config.get("local_model_name", "microsoft/phi-2"),
        workspace_dir=str(workspace_dir),
        knowledge_db_path=str(knowledge_db_path),
        log_path=str(log_path),
        device=config.get("device", "cpu"),
        use_compatibility_mode=True,
        tavily_api_key=config.get("tavily_api_key"),
        firecrawl_api_key=config.get("firecrawl_api_key")
    )
    
    thinking_ai.add_knowledge("Python", "Pythonは汎用プログラミング言語です", confidence=0.9)
    
    thinking_ai.start_thinking()
    
    try:
        print("タスク実行の例:")
        task_result = thinking_ai.execute_task(
            "Pythonの最新バージョンと主な特徴について調べてください"
        )
        print(f"タスク結果: {task_result}")
        
        print("\nバックグラウンド思考プロセスが動作中...")
        time.sleep(10)
        
        print("\n現在の知識データベース:")
        knowledge = thinking_ai.get_knowledge_db()
        for key, value in knowledge.items():
            print(f"- {key}: {value}")
        
        print("\nWeb検索の例:")
        web_search_result = thinking_ai.search_web("人工知能の最新トレンド")
        if web_search_result:
            print(f"検索結果: {web_search_result[:500]}...")  # 最初の500文字だけ表示
        
        print("\nさらに思考プロセスが進行中...")
        time.sleep(10)
        
        print("\n更新された知識データベース:")
        updated_knowledge = thinking_ai.get_knowledge_db()
        for key, value in updated_knowledge.items():
            print(f"- {key}: {value}")
        
    finally:
        thinking_ai.stop_thinking()
        print("\n思考プロセスを停止しました")

if __name__ == "__main__":
    main()
