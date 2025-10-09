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
# 必要なライブラリのインポート
{imports}
import os
import json
import time
import re
import datetime
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple

task_info = {
    "task_id": "{task_id}",
    "description": "{description}",
    "plan_id": "{plan_id}"
}

task_description = task_info.get("description", "Unknown task")
insights = []
hypotheses = []
conclusions = []

KNOWLEDGE_DB_PATH = "./workspace/persistent_thinking/knowledge_db.json"
THINKING_LOG_PATH = "./workspace/persistent_thinking/thinking_log.jsonl"

# 成果物の出力先（プランごとのディレクトリ）
ARTIFACTS_BASE = "./workspace/artifacts"
ARTIFACTS_DIR = os.path.join(ARTIFACTS_BASE, task_info.get("plan_id", "default"))

def ensure_artifacts_dir():
    try:
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    except Exception:
        pass

def save_text_artifact(filename: str, content: str, mode: str = "a") -> str:
    try:
        ensure_artifacts_dir()
        path = os.path.join(ARTIFACTS_DIR, filename)
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)
            if not content.endswith("\n"):
                f.write("\n")
        return path
    except Exception:
        return ""

def append_report(section_title: str, body: str):
    ts = datetime.datetime.now().isoformat()
    md = f"\n\n## {section_title} ({ts})\n\n{body}\n"
    save_text_artifact("report.md", md, mode="a")

def save_placeholder_plot():
    """matplotlibが利用可能なら簡易プロットを成果物として保存"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        ensure_artifacts_dir()
        x = np.arange(5)
        y = np.linspace(1, 5, 5)
        plt.figure(figsize=(6, 4))
        plt.bar(x, y, color="#5B8FF9")
        plt.title("Placeholder Plot")
        plt.tight_layout()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(ARTIFACTS_DIR, f"plot_{ts}.png")
        plt.savefig(path)
        plt.close()
        return path
    except Exception:
        return ""

def load_knowledge_db():
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

def integrate_task_results(task_result, confidence=0.8):
    """
    タスク実行結果を知識ベースに統合する
    
    Args:
        task_result: タスク実行の結果
        confidence: 確信度 (0.0-1.0)
    """
    global task_description
    
    if not task_result:
        return False
        
    try:
        knowledge_items = []
        
        if isinstance(task_result, dict):
            for key, value in task_result.items():
                if isinstance(value, (str, int, float, bool)):
                    subject = f"{task_description[:30]} - {key}"
                    fact = str(value)
                    knowledge_items.append({
                        "subject": subject,
                        "fact": fact,
                        "confidence": confidence
                    })
        elif isinstance(task_result, str):
            lines = task_result.split('\\n')
            for line in lines:
                if ':' in line and len(line) > 10:
                    parts = line.split(':', 1)
                    subject = f"{task_description[:30]} - {parts[0].strip()}"
                    fact = parts[1].strip()
                    knowledge_items.append({
                        "subject": subject,
                        "fact": fact,
                        "confidence": confidence
                    })
        
        for item in knowledge_items:
            update_knowledge(
                item["subject"],
                item["fact"],
                item["confidence"],
                "task_result_integration"
            )
            
        log_thought("task_result_integration", {
            "task": task_description,
            "extracted_knowledge_count": len(knowledge_items)
        })
        
        return True
    except Exception as e:
        print(f"タスク結果統合エラー: {str(e)}")
        return False

def request_multi_agent_discussion(topic):
    try:
        log_thought("multi_agent_discussion_request", {
            "topic": topic,
            "timestamp": time.time()
        })
        
        return {
            "topic": topic,
            "requested": True,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"マルチエージェント討論リクエストエラー: {str(e)}")
        return {}

def prepare_task():
    global task_description, insights, hypotheses, conclusions
    
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
        except Exception as e:
            print(f"関連知識取得エラー: {str(e)}")
        
        if related_knowledge:
            print(f"タスク '{task_description}' に関連する既存知識が {len(related_knowledge)} 件見つかりました:")
            for i, knowledge in enumerate(related_knowledge):
                print(f"  {i+1}. {knowledge['subject']}: {knowledge['fact']} (確信度: {knowledge['confidence']:.2f})")
            
            if len(related_knowledge) >= 2:
                hypothesis = f"タスク '{task_description}' は {related_knowledge[0]['subject']} と {related_knowledge[1]['subject']} に関連している可能性がある"
                add_hypothesis(hypothesis, confidence=0.6)
        else:
            print(f"タスク '{task_description}' に関連する既存知識は見つかりませんでした。")
            add_insight("このタスクに関連する既存知識がないため、新しい知識の獲得が必要")
            
            request_multi_agent_discussion(f"「{task_description}」に関する基礎知識と仮説")
        
        return task_start_time
    except Exception as e:
        print(f"タスク準備エラー: {str(e)}")
        return time.time()

def run_task():
    """
    タスクを実行して結果を返す関数
    この関数は継続的思考AIで得られた知見を活用し、結果を知識ベースに統合する
    
    Returns:
        Any: タスク実行結果（辞書形式が望ましい）
    """
    try:
        result = None
{main_code}
        if result is None:
            result = "Task completed successfully"
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"タスク実行エラー: {str(e)}")
        print(error_details)
        return {
            "status": "error",
            "error": str(e),
            "traceback": error_details
        }

def main():
    """
    メイン実行関数
    タスクの準備、実行、結果の統合を行う
    """
    global task_description, insights, hypotheses, conclusions
    
    try:
        task_start_time = prepare_task()
        
        print("タスクを実行中...")
        task_result = run_task()
        print("タスク実行完了")
        
        if task_result is not None:
            print("タスク結果を知識ベースに統合中...")
            integrate_success = integrate_task_results(task_result)
            if integrate_success:
                print("知識ベースへの統合に成功しました")
            else:
                print("知識ベースへの統合に失敗しました")
            # 成果物として簡易レポートを追記
            try:
                ensure_artifacts_dir()
                preview = str(task_result)
                if len(preview) > 1200:
                    preview = preview[:1200] + "..."
                body = f"### Task\n- Description: {task_description}\n\n### Result Preview\n```
{preview}
```\n"
                append_report("Task Result", body)
                # 画像のプレースホルダーを生成（環境にmatplotlib/numpyがあれば）
                try:
                    save_placeholder_plot()
                except Exception:
                    pass
            except Exception:
                pass
        else:
            print("タスク結果がないため知識ベースに統合しません")
        
        log_thought("task_execution_complete", {
            "task": task_description,
            "execution_time": time.time() - task_start_time,
            "insights_count": len(insights),
            "hypotheses_count": len(hypotheses),
            "conclusions_count": len(conclusions)
        })
        
        return task_result if task_result is not None else "Task completed successfully"
        
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

def get_template_for_task(task_description, required_libraries=None, recommended_packages=None):
    """
    タスクの説明に基づいて適切なテンプレートを選択
    常にPERSISTENT_THINKING_TEMPLATEを使用し、タスクタイプのみを記録
    
    Args:
        task_description (str): タスクの説明
        required_libraries (list, optional): 必要なライブラリのリスト
        recommended_packages (list, optional): AIが推奨するパッケージのリスト
        
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
                        "required_libraries": required_libraries,
                        "recommended_packages": recommended_packages
                    }
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\\n")
    except Exception as e:
        print(f"テンプレート選択のログ記録に失敗: {str(e)}")
    
    if required_libraries is None:
        required_libraries = []
    
    stock_data_keywords = [
        '株価', '株式', 'stock', 'finance', '金融', 'yfinance', 'yahoo', '日経',
        'nikkei', '証券', 'investment', '投資', 'market', 'マーケット'
    ]
    
    if recommended_packages:
        for package in recommended_packages:
            package_name = package.get("name", "")
            if package_name and package_name not in required_libraries:
                required_libraries.append(package_name)
                print(f"Adding recommended package: {package_name} (confidence: {package.get('confidence', 0)})")
    
    if task_type == "data_analysis" and "pandas" not in required_libraries:
        required_libraries.append("pandas")
    if task_type == "data_analysis" and "matplotlib" not in required_libraries:
        required_libraries.append("matplotlib")
    if task_type == "web_scraping" and "requests" not in required_libraries:
        required_libraries.append("requests")
    if task_type == "web_scraping" and "beautifulsoup4" not in required_libraries:
        required_libraries.append("beautifulsoup4")
    if any(keyword in task_lower for keyword in stock_data_keywords) and "yfinance" not in required_libraries:
        required_libraries.append("yfinance")
    
    if any(lib in ["Dict", "List", "Any", "Optional", "Union", "Tuple"] for lib in required_libraries):
        for typing_type in ["Dict", "List", "Any", "Optional", "Union", "Tuple"]:
            if typing_type in required_libraries:
                required_libraries.remove(typing_type)
        
        if "typing" not in required_libraries:
            required_libraries.append("typing")
    
    # テンプレート内のプレースホルダーを検証
    template = template.replace("{imports}", "___IMPORTS_PLACEHOLDER___")
    template = template.replace("{main_code}", "___MAIN_CODE_PLACEHOLDER___")
    
    template = template.replace('{str(e)}', '{{str(e)}}')
    
    template = template.replace("___IMPORTS_PLACEHOLDER___", "{imports}")
    template = template.replace("___MAIN_CODE_PLACEHOLDER___", "{main_code}")
    
    if "{imports}" not in template or "{main_code}" not in template:
        print(f"Warning: Template missing required placeholders. Using basic template.")
        # 基本テンプレートを使用（インデントに注意）
        template = r"""
# 必要なライブラリのインポート
{imports}
import typing  # 型アノテーション用
import time  # 時間計測用
import traceback  # エラートレース用
import os  # ファイル操作用
import json  # JSON処理用
import datetime  # 日付処理用

task_info = {{
    "task_id": "{task_id}",
    "description": "{description}",
    "plan_id": "{plan_id}"
}}

def run_task():
    # タスクを実行して結果を返す関数
    try:
        result = None
{main_code}
        if result is None:
            result = "Task completed successfully"
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error: {{str(e)}}")
        print(error_details)
        return {{"error": str(e), "traceback": error_details}}

def main():
    try:
        print("タスクを実行中...")
        task_result = run_task()
        print("タスク実行完了")
        return task_result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error: {{str(e)}}")
        print(error_details)
        return str(e)
    
# スクリプト実行
if __name__ == "__main__":
    result = main()
"""
    
    return template

def get_relevant_knowledge(task_keywords, limit=5):
    """タスクに関連する知識を取得"""
    try:
        import json
        import os
        
        knowledge_db_path = "./workspace/persistent_thinking/knowledge_db.json"
        if not os.path.exists(knowledge_db_path):
            return []
            
        with open(knowledge_db_path, 'r', encoding='utf-8') as f:
            knowledge_db = json.load(f)
            
        relevant_knowledge = []
        
        for subject, data in knowledge_db.items():
            fact = data.get("fact", "")
            confidence = data.get("confidence", 0)
            
            is_relevant = False
            for keyword in task_keywords:
                if keyword.lower() in subject.lower() or keyword.lower() in fact.lower():
                    is_relevant = True
                    break
            
            if is_relevant:
                relevant_knowledge.append({
                    "subject": subject,
                    "fact": fact,
                    "confidence": confidence,
                    "source": data.get("source", "unknown")
                })
        
        relevant_knowledge.sort(key=lambda x: x["confidence"], reverse=True)
        return relevant_knowledge[:limit]
        
    except Exception as e:
        print(f"関連知識取得エラー: {str(e)}")
        return []

def apply_success_patterns(task_description):
    """成功パターンを適用"""
    try:
        import json
        import os
        
        knowledge_db_path = "./workspace/persistent_thinking/knowledge_db.json"
        if not os.path.exists(knowledge_db_path):
            return []
            
        with open(knowledge_db_path, 'r', encoding='utf-8') as f:
            knowledge_db = json.load(f)
            
        success_patterns = []
        
        for subject, data in knowledge_db.items():
            if "[success_factor]" in subject:
                success_patterns.append({
                    "pattern": data.get("fact", ""),
                    "confidence": data.get("confidence", 0)
                })
        
        if success_patterns:
            print("適用可能な成功パターン:")
            for pattern in success_patterns[:3]:
                print(f"- {pattern['pattern']} (確信度: {pattern['confidence']})")
        
        return success_patterns
        
    except Exception as e:
        print(f"成功パターン適用エラー: {str(e)}")
        return []

def avoid_failure_patterns(task_description):
    """失敗パターンを回避"""
    try:
        import json
        import os
        
        knowledge_db_path = "./workspace/persistent_thinking/knowledge_db.json"
        if not os.path.exists(knowledge_db_path):
            return []
            
        with open(knowledge_db_path, 'r', encoding='utf-8') as f:
            knowledge_db = json.load(f)
            
        failure_patterns = []
        
        for subject, data in knowledge_db.items():
            if "[failure_factor]" in subject:
                failure_patterns.append({
                    "pattern": data.get("fact", ""),
                    "confidence": data.get("confidence", 0)
                })
        
        if failure_patterns:
            print("回避すべき失敗パターン:")
            for pattern in failure_patterns[:3]:
                print(f"- {pattern['pattern']} (確信度: {pattern['confidence']})")
        
        return failure_patterns
        
    except Exception as e:
        print(f"失敗パターン回避エラー: {str(e)}")
        return []
