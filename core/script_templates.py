# core/script_templates.py
"""
Pythonスクリプトのテンプレートを提供するモジュール
"""

# 依存関係を適切に処理するスクリプトテンプレート
DEPENDENCY_AWARE_TEMPLATE = """
# 必要なライブラリのインポート
{imports}

def main():
    try:
        # メイン処理
{main_code}
        
    except ImportError as e:
        # 必要なパッケージがない場合のエラー処理
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        result = f"エラー: 必要なモジュール '{missing_module}' がインストールされていません。"
        print(result)
        print(f"次のコマンドでインストールしてください: pip install {missing_module}")
        return result
        
    except Exception as e:
        # その他のエラー処理
        import traceback
        error_details = traceback.format_exc()
        result = f"エラー: {{str(e)}}"
        print(result)
        print(error_details)
        return result

# スクリプト実行
if __name__ == "__main__":
    result = main()
"""

# データ分析用スクリプトテンプレート
DATA_ANALYSIS_TEMPLATE = """
# 必要なライブラリのインポート
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from datetime import datetime, timedelta
    import os
    import json
    import csv
except ImportError as e:
    missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
    result = f"エラー: 必要なモジュール '{missing_module}' がインストールされていません。"
    print(result)
    if missing_module == "pandas":
        print("pandasをインストールするには: pip install pandas")
    elif missing_module == "numpy":
        print("numpyをインストールするには: pip install numpy")
    elif missing_module == "matplotlib":
        print("matplotlibをインストールするには: pip install matplotlib")
    else:
        print(f"次のコマンドでインストールしてください: pip install {missing_module}")
    # 実行を終了
    raise

def main():
    try:
        # メイン処理
{main_code}
        
    except Exception as e:
        # エラー処理
        import traceback
        error_details = traceback.format_exc()
        result = f"エラー: {{str(e)}}"
        print(result)
        print(error_details)
        return result

# スクリプト実行
result = main()
"""

# Webスクレイピング用スクリプトテンプレート
WEB_SCRAPING_TEMPLATE = """
# 必要なライブラリのインポート
try:
    import requests
    from bs4 import BeautifulSoup
    import re
    import json
    import os
except ImportError as e:
    missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
    result = f"エラー: 必要なモジュール '{missing_module}' がインストールされていません。"
    print(result)
    if missing_module == "bs4":
        print("BeautifulSoup4をインストールするには: pip install beautifulsoup4")
    elif missing_module == "requests":
        print("requestsをインストールするには: pip install requests")
    else:
        print(f"次のコマンドでインストールしてください: pip install {missing_module}")
    # 実行を終了
    raise

def main():
    try:
        # メイン処理
{main_code}
        
    except Exception as e:
        # エラー処理
        import traceback
        error_details = traceback.format_exc()
        result = f"エラー: {{str(e)}}"
        print(result)
        print(error_details)
        return result

# スクリプト実行
result = main()
"""

PERSISTENT_THINKING_TEMPLATE = '''
# 必要なライブラリのインポート
{imports}
import os
import json
import time

KNOWLEDGE_DB_PATH = "./workspace/persistent_thinking/knowledge_db.json"
THINKING_LOG_PATH = "./workspace/persistent_thinking/thinking_log.jsonl"

def load_knowledge_db():
    """知識データベースを読み込む"""
    try:
        if os.path.exists(KNOWLEDGE_DB_PATH):
            with open(KNOWLEDGE_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"知識データベース読み込みエラー: {str(e)}")
        return {}

def save_knowledge_db(knowledge_db):
    """知識データベースを保存する"""
    try:
        with open(KNOWLEDGE_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(knowledge_db, indent=2, ensure_ascii=False, f)
        return True
    except Exception as e:
        print(f"知識データベース保存エラー: {str(e)}")
        return False

def log_thought(thought_type, content):
    """思考ログに記録する"""
    try:
        log_entry = {
            "timestamp": time.time(),
            "type": thought_type,
            "content": content
        }
        with open(THINKING_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\\n")
        return True
    except Exception as e:
        print(f"思考ログ記録エラー: {str(e)}")
        return False

def update_knowledge(subject, fact, confidence=0.8):
    """知識を更新する"""
    try:
        knowledge_db = load_knowledge_db()
        
        if subject not in knowledge_db:
            knowledge_db[subject] = {}
            original_fact = None
        else:
            original_fact = knowledge_db[subject].get("fact")
        
        knowledge_db[subject]["fact"] = fact
        knowledge_db[subject]["confidence"] = confidence
        knowledge_db[subject]["last_updated"] = time.time()
        
        save_success = save_knowledge_db(knowledge_db)
        
        log_thought("knowledge_update", {
            "subject": subject,
            "original_fact": original_fact,
            "new_fact": fact,
            "confidence": confidence,
            "success": save_success
        })
        
        return save_success
    except Exception as e:
        print(f"知識更新エラー: {str(e)}")
        return False

def get_knowledge(subject):
    """特定の主題に関する知識を取得する"""
    try:
        knowledge_db = load_knowledge_db()
        return knowledge_db.get(subject, {}).get("fact")
    except Exception as e:
        print(f"知識取得エラー: {str(e)}")
        return None

def get_related_knowledge(keywords, limit=5):
    """キーワードに関連する知識を取得する"""
    try:
        knowledge_db = load_knowledge_db()
        results = []
        
        for subject, data in knowledge_db.items():
            for keyword in keywords:
                if keyword.lower() in subject.lower() or (data.get("fact") and keyword.lower() in data.get("fact", "").lower()):
                    results.append({
                        "subject": subject,
                        "fact": data.get("fact"),
                        "confidence": data.get("confidence", 0)
                    })
                    break
                    
            if len(results) >= limit:
                break
                
        return results
    except Exception as e:
        print(f"関連知識取得エラー: {str(e)}")
        return []

def main():
    try:
        task_info = getattr(globals().get('task_info', {}), 'task_description', 'Unknown task')
        log_thought("task_execution_start", {"task": task_info})
        
        knowledge_db = load_knowledge_db()
        
        # メイン処理
{main_code}
        
        log_thought("task_execution_complete", {
            "task": task_info,
            "result": result if 'result' in locals() else "No result variable found"
        })
        
        return result if 'result' in locals() else "Task completed successfully"
        
    except ImportError as e:
        # 必要なパッケージがない場合のエラー処理
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        error_msg = f"エラー: 必要なモジュール '{missing_module}' がインストールされていません。"
        print(error_msg)
        print(f"次のコマンドでインストールしてください: pip install {missing_module}")
        
        log_thought("task_execution_error", {
            "task": getattr(globals().get('task_info', {}), 'task_description', 'Unknown task'),
            "error_type": "ImportError",
            "error_message": error_msg
        })
        
        return error_msg
        
    except Exception as e:
        # その他のエラー処理
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"エラー: {str(e)}"
        print(error_msg)
        print(error_details)
        
        log_thought("task_execution_error", {
            "task": getattr(globals().get('task_info', {}), 'task_description', 'Unknown task'),
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": error_details
        })
        
        update_knowledge(
            f"エラーパターン: {type(e).__name__}",
            f"タスク「{task_info}」で発生: {str(e)}",
            confidence=0.7
        )
        
        return error_msg

# スクリプト実行
if __name__ == "__main__":
    result = main()
'''

def get_template_for_task(task_description, required_libraries=None):
    """
    タスクの説明に基づいて適切なテンプレートを選択
    
    Args:
        task_description (str): タスクの説明
        required_libraries (list, optional): 必要なライブラリのリスト
        
    Returns:
        str: 適切なテンプレート
    """
    # タスクの説明を小文字に変換
    task_lower = task_description.lower()
    
    # データ分析関連のキーワード
    data_analysis_keywords = [
        'csv', 'pandas', 'numpy', 'データ分析', 'データ処理', 'グラフ', 'matplotlib',
        'statistics', '統計', 'データフレーム', 'dataframe', '計算', 'calculate'
    ]
    
    # Webスクレイピング関連のキーワード
    web_scraping_keywords = [
        'web', 'スクレイピング', 'scraping', 'html', 'requests', 'beautifulsoup',
        'bs4', 'ウェブ', 'サイト', 'site', 'url', 'http'
    ]
    
    persistent_thinking_keywords = [
        '知識', '学習', 'knowledge', 'learning', '思考', 'thinking', '継続学習',
        '自己改善', 'self-improvement', '知識ベース', 'knowledge base', '記憶',
        'memory', '持続', 'persistent', '連携', 'integration', '知識グラフ'
    ]
    
    template = PERSISTENT_THINKING_TEMPLATE
    
    task_type = "general"
    if any(keyword in task_lower for keyword in data_analysis_keywords):
        task_type = "data_analysis"
    elif any(keyword in task_lower for keyword in web_scraping_keywords):
        task_type = "web_scraping"
    
    try:
        import time
        import json
        import os
        
        log_path = "./workspace/persistent_thinking/thinking_log.jsonl"
        if os.path.exists(log_path):
            with open(log_path, 'a', encoding='utf-8') as f:
                log_entry = {
                    "timestamp": time.time(),
                    "type": "template_selection",
                    "content": {
                        "task_description": task_description,
                        "selected_template_type": task_type
                    }
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"テンプレート選択のログ記録に失敗: {str(e)}")
    
    # テンプレート内のプレースホルダーを検証
    import re
    placeholders = re.findall(r'{([^{}]*)}', template)
    
    # 基本的なプレースホルダー
    required_placeholders = {"imports", "main_code"}
    
    # 不明なプレースホルダーがある場合は修正
    if set(placeholders) - required_placeholders:
        print(f"Warning: Template has unknown placeholders. Using basic template.")
        # 基本テンプレートを使用（インデントに注意）
        template = """
# 必要なライブラリのインポート
{imports}

def main():
    try:
        # メイン処理
{main_code}
    except Exception as e:
        print(f"Error: {{str(e)}}")
        return str(e)
    
    return "Task completed successfully"

# スクリプト実行
if __name__ == "__main__":
    result = main()
"""
    
    # 念のため、テンプレート内の中括弧をエスケープ（f文字列内の中括弧のみ）
    template = re.sub(r'f"([^"]*){([^{}]*)}([^"]*)"', r'f"\1{{\2}}\3"', template)
    template = re.sub(r"f'([^']*){([^{}]*)}([^']*)'", r"f'\1{{\2}}\3'", template)
    
    return template
