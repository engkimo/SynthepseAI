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
        result = f"エラー: {str(e)}"
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
        result = f"エラー: {str(e)}"
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
        result = f"エラー: {str(e)}"
        print(result)
        print(error_details)
        return result

# スクリプト実行
result = main()
"""

PERSISTENT_THINKING_TEMPLATE = r'''
{imports}
import os
import json
import time
import re
import datetime
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple

task_description = ""
insights = []
hypotheses = []
conclusions = []
execution_results = []

KNOWLEDGE_DB_PATH = "./workspace/persistent_thinking/knowledge_db.json"
THINKING_LOG_PATH = "./workspace/persistent_thinking/thinking_log.jsonl"

def load_knowledge_db():
    """
    知識データベースを読み込み、タスク実行に必要な知識を取得します。
    この関数は継続的思考プロセスの一部として、過去の知識を活用するために使用されます。
    
    Returns:
        Dict: 知識データベースの内容
    """
    try:
        if os.path.exists(KNOWLEDGE_DB_PATH):
            with open(KNOWLEDGE_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"知識データベース読み込みエラー: {str(e)}")
        return {}

def save_knowledge_db(knowledge_db):
    try:
        os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
        with open(KNOWLEDGE_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(knowledge_db, fp=f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"知識データベース保存エラー: {str(e)}")
        return False

def log_thought(thought_type, content):
    try:
        os.makedirs(os.path.dirname(THINKING_LOG_PATH), exist_ok=True)
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

def update_knowledge(subject, fact, confidence=0.8, source=None):
    """
    知識データベースに新しい知識を追加または更新します。
    この関数は継続的思考プロセスの一部として、タスク実行から得られた知見を
    知識ベースに統合するために使用されます。
    
    Args:
        subject (str): 知識の主題
        fact (str): 知識の内容
        confidence (float): 知識の確信度 (0.0-1.0)
        source (str, optional): 知識の出所
        
    Returns:
        bool: 更新が成功したかどうか
    """
    try:
        knowledge_db = load_knowledge_db()
        
        if subject not in knowledge_db:
            knowledge_db[subject] = {}
            original_fact = None
        else:
            original_fact = knowledge_db[subject].get("fact")
            
        existing_confidence = knowledge_db[subject].get("confidence", 0)
        if existing_confidence > confidence + 0.1:
            log_thought("knowledge_update_rejected", {
                "subject": subject,
                "existing_fact": original_fact,
                "new_fact": fact,
                "existing_confidence": existing_confidence,
                "new_confidence": confidence,
                "reason": "新しい情報の確信度が既存の情報より低いため更新を拒否"
            })
            return False
        
        knowledge_db[subject]["fact"] = fact
        knowledge_db[subject]["confidence"] = confidence
        knowledge_db[subject]["last_updated"] = time.time()
        
        if source:
            knowledge_db[subject]["source"] = source
        
        save_success = save_knowledge_db(knowledge_db)
        
        log_thought("knowledge_update", {
            "subject": subject,
            "original_fact": original_fact,
            "new_fact": fact,
            "confidence": confidence,
            "source": source,
            "success": save_success
        })
        
        return save_success
    except Exception as e:
        print(f"知識更新エラー: {str(e)}")
        return False

def add_insight(insight, confidence=0.7):
    global insights
    insights.append({
        "content": insight,
        "confidence": confidence,
        "timestamp": time.time()
    })
    
    log_thought("task_insight", {
        "task": task_description,
        "insight": insight,
        "confidence": confidence
    })

def add_hypothesis(hypothesis, confidence=0.6):
    global hypotheses
    hypotheses.append({
        "content": hypothesis,
        "confidence": confidence,
        "timestamp": time.time(),
        "verified": False
    })
    
    log_thought("task_hypothesis", {
        "task": task_description,
        "hypothesis": hypothesis,
        "confidence": confidence
    })

def verify_hypothesis(hypothesis, verified, evidence, confidence=0.7):
    global hypotheses
    
    for h in hypotheses:
        if h["content"] == hypothesis:
            h["verified"] = verified
            h["evidence"] = evidence
            h["verification_confidence"] = confidence
            h["verification_time"] = time.time()
            break
    
    log_thought("hypothesis_verification", {
        "task": task_description,
        "hypothesis": hypothesis,
        "verified": verified,
        "evidence": evidence,
        "confidence": confidence
    })
    
    if verified and confidence > 0.7:
        update_knowledge(
            f"検証済み仮説: {hypothesis[:50]}...",
            f"検証結果: {evidence}",
            confidence,
            "hypothesis_verification"
        )

def verify_hypothesis_with_simulation(hypothesis, simulation_code):
    global task_description
    
    result = {
        "hypothesis": hypothesis,
        "verified": False,
        "confidence": 0.0,
        "evidence": [],
        "timestamp": time.time()
    }
    
    try:
        local_vars = {}
        exec(simulation_code, {"__builtins__": __builtins__}, local_vars)
        
        simulation_result = local_vars.get("result", None)
        
        if simulation_result:
            result["simulation_result"] = str(simulation_result)
            result["verified"] = local_vars.get("verified", False)
            result["confidence"] = local_vars.get("confidence", 0.5)
            result["evidence"] = local_vars.get("evidence", [])
            
            log_thought("hypothesis_simulation", {
                "task": task_description,
                "hypothesis": hypothesis,
                "verified": result["verified"],
                "confidence": result["confidence"],
                "evidence": result["evidence"]
            })
            
            if result["verified"] and result["confidence"] > 0.7:
                subject = f"検証済み仮説: {hypothesis[:50]}..."
                fact = f"検証結果: {result['simulation_result']}"
                update_knowledge(subject, fact, result["confidence"], "hypothesis_simulation")
        else:
            log_thought("hypothesis_simulation_warning", {
                "task": task_description,
                "hypothesis": hypothesis,
                "warning": "シミュレーション結果が取得できませんでした"
            })
    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        log_thought("hypothesis_simulation_error", {
            "task": task_description,
            "hypothesis": hypothesis,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        
    return result

def add_conclusion(conclusion, confidence=0.8):
    """
    タスクの結論を追加し、高い確信度の結論は知識ベースに保存します。
    
    Args:
        conclusion (str): 結論の内容
        confidence (float): 結論の確信度 (0.0-1.0)
    """
    global conclusions
    conclusions.append({
        "content": conclusion,
        "confidence": confidence,
        "timestamp": time.time()
    })
    
    log_thought("task_conclusion", {
        "task": task_description,
        "conclusion": conclusion,
        "confidence": confidence
    })
    
    if confidence > 0.7:
        update_knowledge(
            f"タスク結論: {task_description[:50]}...",
            conclusion,
            confidence,
            "task_conclusion"
        )

def record_execution_result(result_type, content, metadata=None):
    """
    スクリプト実行結果を記録し、知識ベースに反映します。
    この関数は継続的思考プロセスの一部として、スクリプト実行から得られた
    結果を知識ベースに統合するために使用されます。
    
    Args:
        result_type (str): 結果の種類 (例: "data_analysis", "calculation", "visualization")
        content (Any): 結果の内容
        metadata (Dict, optional): 結果に関する追加情報
    
    Returns:
        bool: 記録が成功したかどうか
    """
    global execution_results
    
    if metadata is None:
        metadata = {}
    
    result = {
        "type": result_type,
        "content": str(content),
        "timestamp": time.time(),
        "metadata": metadata
    }
    
    execution_results.append(result)
    
    log_thought("execution_result", {
        "task": task_description,
        "result_type": result_type,
        "content_summary": str(content)[:100] + "..." if len(str(content)) > 100 else str(content),
        "metadata": metadata
    })
    
    if result_type == "data_analysis":
        update_knowledge(
            f"データ分析結果: {task_description[:30]}...",
            f"分析結果: {content}",
            0.9,
            "execution_result"
        )
    elif result_type == "calculation":
        update_knowledge(
            f"計算結果: {metadata.get('calculation_name', task_description[:30])}...",
            f"計算結果: {content}",
            0.95,
            "execution_result"
        )
    elif result_type == "visualization":
        update_knowledge(
            f"可視化結果: {metadata.get('visualization_name', task_description[:30])}...",
            f"可視化から得られた洞察: {metadata.get('insights', '特に洞察なし')}",
            0.8,
            "execution_result"
        )
    
    return True

def request_multi_agent_discussion(topic):
    try:
        log_thought("multi_agent_discussion_request", {
            "topic": topic,
            "timestamp": time.time()
        })
        
        update_knowledge(
            f"討論リクエスト: {topic[:50]}...",
            f"マルチエージェント討論がリクエストされました: {topic}",
            confidence=0.9,
            source="multi_agent_discussion_request"
        )
        
        add_insight(f"マルチエージェント討論の結果を待機中: {topic}", confidence=0.8)
        
        return {
            "topic": topic,
            "requested": True,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"マルチエージェント討論リクエストエラー: {str(e)}")
        return {}

def main():
    global task_description, insights, hypotheses, conclusions, execution_results
    global THINKING_LOG_PATH, KNOWLEDGE_DB_PATH
    
    try:
        task_info = globals().get('task_info', {})
        task_description = task_info.get('description', 'Unknown task')
        task_start_time = time.time()
        
        log_thought("task_execution_start", {
            "task": task_description,
            "timestamp_readable": datetime.datetime.now().isoformat()
        })
        
        keywords = [word for word in task_description.lower().split() if len(word) > 3]
        
        related_knowledge = []
        try:
            knowledge_db = load_knowledge_db()
            for subject, data in knowledge_db.items():
                for keyword in keywords:
                    if keyword.lower() in subject.lower() or (data.get("fact") and keyword.lower() in data.get("fact", "").lower()):
                        related_knowledge.append({
                            "subject": subject,
                            "fact": data.get("fact"),
                            "confidence": data.get("confidence", 0),
                            "last_updated": data.get("last_updated"),
                            "source": data.get("source")
                        })
                        break
                        
            error_patterns = []
            if os.path.exists(THINKING_LOG_PATH):
                with open(THINKING_LOG_PATH, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get("type") == "task_execution_error":
                                content = entry.get("content", {})
                                error_patterns.append({
                                    "error_type": content.get("error_type", "unknown"),
                                    "error_message": content.get("error_message", "")
                                })
                        except:
                            continue
            
            if error_patterns:
                add_insight(f"過去のエラーパターン {len(error_patterns)} 件を分析し、同様のエラーを回避します", confidence=0.8)
                for pattern in error_patterns[-3:]:  # 最新の3つのエラーパターンを考慮
                    add_hypothesis(f"エラー '{pattern['error_type']}' を回避するため、適切な対策が必要", confidence=0.7)
        except Exception as e:
            print(f"関連知識取得エラー: {str(e)}")
        
        if related_knowledge:
            print(f"タスク '{task_description}' に関連する既存知識が {len(related_knowledge)} 件見つかりました:")
            for i, knowledge in enumerate(related_knowledge):
                print(f"  {i+1}. {knowledge['subject']}: {knowledge['fact']} (確信度: {knowledge['confidence']:.2f})")
            
            if len(related_knowledge) >= 2:
                hypothesis = f"タスク '{task_description}' は {related_knowledge[0]['subject']} と {related_knowledge[1]['subject']} に関連している可能性がある"
                add_hypothesis(hypothesis, confidence=0.6)
                
                for i in range(min(len(related_knowledge), 3)):
                    for j in range(i+1, min(len(related_knowledge), 4)):
                        if i != j:
                            insight = f"{related_knowledge[i]['subject']}と{related_knowledge[j]['subject']}を組み合わせることで、新しい視点が得られるかもしれない"
                            add_insight(insight, confidence=0.65)
        else:
            print(f"タスク '{task_description}' に関連する既存知識は見つかりませんでした。")
            add_insight("このタスクに関連する既存知識がないため、新しい知識の獲得が必要")
            
            discussion_request = request_multi_agent_discussion(f"「{task_description}」に関する基礎知識と仮説")
            if discussion_request:
                add_insight(f"複数エージェントによる討論をリクエストしました: {task_description}", confidence=0.8)
        
{main_code}
        
        log_thought("task_execution_complete", {
            "task": task_description,
            "execution_time": time.time() - task_start_time,
            "insights_count": len(insights),
            "hypotheses_count": len(hypotheses),
            "conclusions_count": len(conclusions)
        })
        
        return result if 'result' in locals() else "Task completed successfully"
        
    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        error_msg = f"エラー: 必要なモジュール '{missing_module}' がインストールされていません。"
        print(error_msg)
        print(f"次のコマンドでインストールしてください: pip install {missing_module}")
        
        try:
            log_thought("task_execution_error", {
                "task": task_description,
                "error_type": "ImportError",
                "error_message": error_msg
            })
        except:
            pass
            
        return error_msg
        
    except Exception as e:
        error_details = traceback.format_exc()
        error_msg = f"エラー: {str(e)}"
        print(error_msg)
        print(error_details)
        
        try:
            log_thought("task_execution_error", {
                "task": task_description,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": error_details
            })
            
            update_knowledge(
                f"エラーパターン: {type(e).__name__}",
                f"タスク実行中に発生: {str(e)}",
                confidence=0.7
            )
        except:
            pass
            
        return error_msg

if __name__ == "__main__":
    result = main()
'''

def get_template_for_task(task_description, required_libraries=None):
    """
    タスクの説明に基づいて適切なテンプレートを選択
    常にPERSISTENT_THINKING_TEMPLATEを使用し、タスクタイプのみを記録
    
    スクリプト生成時に、知識ベースとの双方向同期を強化し、
    継続的思考プロセスに貢献するテンプレートを提供します。
    
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
    
    knowledge_thinking_keywords = [
        '知識', '学習', 'knowledge', 'learning', '思考', 'thinking', '継続学習',
        '自己改善', 'self-improvement', '知識ベース', 'knowledge base', '記憶',
        'memory', '持続', 'persistent', '連携', 'integration', '知識グラフ'
    ]
    
    research_keywords = [
        '検索', 'search', '調査', 'research', '情報収集', 'information gathering',
        '分析', 'analysis', '評価', 'evaluation', '比較', 'comparison'
    ]
    
    template = PERSISTENT_THINKING_TEMPLATE
    
    task_type = "general"
    if any(keyword in task_lower for keyword in data_analysis_keywords):
        task_type = "data_analysis"
    elif any(keyword in task_lower for keyword in web_scraping_keywords):
        task_type = "web_scraping"
    elif any(keyword in task_lower for keyword in knowledge_thinking_keywords):
        task_type = "knowledge_thinking"
    elif any(keyword in task_lower for keyword in research_keywords):
        task_type = "research"
    
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
                        "selected_template_type": task_type,
                        "template": "PERSISTENT_THINKING_TEMPLATE",
                        "required_libraries": required_libraries
                    }
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\\n")
    except Exception as e:
        print(f"テンプレート選択のログ記録に失敗: {str(e)}")
    
    # テンプレート内のプレースホルダーを検証
    template = template.replace("{", "{{").replace("}", "}}")
    
    template = template.replace("{{imports}}", "{imports}")
    template = template.replace("{{main_code}}", "{main_code}")
    
    template = template.replace('print(f"Error: {{{{str(e)}}}}")', 'print(f"Error: {str(e)}")')
    template = template.replace('print(f"エラー: {{{{str(e)}}}}")', 'print(f"エラー: {str(e)}")')
    
    if "{imports}" not in template or "{main_code}" not in template:
        print(f"Warning: Template missing required placeholders. Using basic template.")
        # 基本テンプレートを使用（インデントに注意）
        template = """
# 必要なライブラリのインポート
{imports}

def main():
    try:
        # メイン処理
{main_code}
    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e)
    
    return "Task completed successfully"

# スクリプト実行
if __name__ == "__main__":
    result = main()
"""
    
    return template
