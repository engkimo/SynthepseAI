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

PERSISTENT_THINKING_TEMPLATE = '''
# 必要なライブラリのインポート
{imports}
import os
import json
import time
import re
import datetime
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple

KNOWLEDGE_DB_PATH = "./workspace/persistent_thinking/knowledge_db.json"
THINKING_LOG_PATH = "./workspace/persistent_thinking/thinking_log.jsonl"
KNOWLEDGE_GRAPH_PATH = "./knowledge_graph.json"

class PersistentThinkingManager:
    """持続思考AIとの連携を管理するクラス"""
    
    def __init__(self, task_description: str):
        """
        持続思考マネージャーの初期化
        
        Args:
            task_description: 現在のタスクの説明
        """
        self.task_description = task_description
        self.knowledge_db = self.load_knowledge_db()
        self.task_start_time = time.time()
        self.insights = []
        self.hypotheses = []
        self.conclusions = []
        
        self.log_thought("task_execution_start", {
            "task": self.task_description,
            "timestamp_readable": datetime.datetime.now().isoformat()
        })
        
        self.related_knowledge = self._get_initial_knowledge()
        
        if self.related_knowledge:
            self.log_thought("initial_knowledge_analysis", {
                "task": self.task_description,
                "related_knowledge_count": len(self.related_knowledge),
                "knowledge_subjects": [k["subject"] for k in self.related_knowledge]
            })
    
    def load_knowledge_db(self) -> Dict:
        """知識データベースを読み込む"""
        try:
            if os.path.exists(KNOWLEDGE_DB_PATH):
                with open(KNOWLEDGE_DB_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"知識データベース読み込みエラー: {str(e)}")
            return {}
    
    def save_knowledge_db(self, knowledge_db: Dict) -> bool:
        """知識データベースを保存する"""
        try:
            os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
            
            with open(KNOWLEDGE_DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(knowledge_db, indent=2, ensure_ascii=False, f)
            return True
        except Exception as e:
            print(f"知識データベース保存エラー: {str(e)}")
            return False
    
    def log_thought(self, thought_type: str, content: Dict[str, Any]) -> bool:
        """思考ログに記録する"""
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
    
    def update_knowledge(self, subject: str, fact: str, confidence: float = 0.8, source: str = None) -> bool:
        """
        知識を更新する
        
        Args:
            subject: 知識の主題
            fact: 事実や知識の内容
            confidence: 確信度 (0.0-1.0)
            source: 情報源（ある場合）
            
        Returns:
            bool: 更新が成功したかどうか
        """
        try:
            knowledge_db = self.load_knowledge_db()
            
            if subject not in knowledge_db:
                knowledge_db[subject] = {}
                original_fact = None
            else:
                original_fact = knowledge_db[subject].get("fact")
                
                existing_confidence = knowledge_db[subject].get("confidence", 0)
                if existing_confidence > confidence + 0.1:
                    self.log_thought("knowledge_update_rejected", {
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
            
            save_success = self.save_knowledge_db(knowledge_db)
            
            self.log_thought("knowledge_update", {
                "subject": subject,
                "original_fact": original_fact,
                "new_fact": fact,
                "confidence": confidence,
                "source": source,
                "success": save_success
            })
            
            self.knowledge_db = knowledge_db
            
            return save_success
        except Exception as e:
            print(f"知識更新エラー: {str(e)}")
            return False
    
    def get_knowledge(self, subject: str) -> Optional[str]:
        """特定の主題に関する知識を取得する"""
        try:
            return self.knowledge_db.get(subject, {}).get("fact")
        except Exception as e:
            print(f"知識取得エラー: {str(e)}")
            return None
    
    def get_related_knowledge(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """キーワードに関連する知識を取得する"""
        try:
            results = []
            
            for subject, data in self.knowledge_db.items():
                for keyword in keywords:
                    if keyword.lower() in subject.lower() or (data.get("fact") and keyword.lower() in data.get("fact", "").lower()):
                        results.append({
                            "subject": subject,
                            "fact": data.get("fact"),
                            "confidence": data.get("confidence", 0),
                            "last_updated": data.get("last_updated"),
                            "source": data.get("source")
                        })
                        break
                        
                if len(results) >= limit:
                    break
                    
            return results
        except Exception as e:
            print(f"関連知識取得エラー: {str(e)}")
            return []
    
    def add_insight(self, insight: str, confidence: float = 0.7) -> None:
        """タスク実行中の洞察を追加"""
        self.insights.append({
            "content": insight,
            "confidence": confidence,
            "timestamp": time.time()
        })
        
        self.log_thought("task_insight", {
            "task": self.task_description,
            "insight": insight,
            "confidence": confidence
        })
    
    def add_hypothesis(self, hypothesis: str, evidence: List[str] = None) -> None:
        """仮説を追加"""
        hypothesis_entry = {
            "content": hypothesis,
            "evidence": evidence or [],
            "timestamp": time.time(),
            "verified": False
        }
        
        self.hypotheses.append(hypothesis_entry)
        
        self.log_thought("hypothesis_formation", {
            "task": self.task_description,
            "hypothesis": hypothesis,
            "evidence": evidence or []
        })
    
    def verify_hypothesis(self, hypothesis_idx: int, verified: bool, conclusion: str) -> None:
        """仮説を検証"""
        if 0 <= hypothesis_idx < len(self.hypotheses):
            self.hypotheses[hypothesis_idx]["verified"] = verified
            self.hypotheses[hypothesis_idx]["conclusion"] = conclusion
            
            self.log_thought("hypothesis_verification", {
                "task": self.task_description,
                "hypothesis": self.hypotheses[hypothesis_idx]["content"],
                "verified": verified,
                "conclusion": conclusion
            })
    
    def add_conclusion(self, conclusion: str, confidence: float = 0.8) -> None:
        """タスクの結論を追加"""
        self.conclusions.append({
            "content": conclusion,
            "confidence": confidence,
            "timestamp": time.time()
        })
        
        self.log_thought("task_conclusion", {
            "task": self.task_description,
            "conclusion": conclusion,
            "confidence": confidence
        })
        
        if confidence >= 0.7:
            subject = f"結論: {self.task_description}"
            self.update_knowledge(subject, conclusion, confidence)
    
    def finalize_task(self, result: Any) -> None:
        """タスクの完了を記録"""
        execution_time = time.time() - self.task_start_time
        
        result_str = str(result) if result is not None else "No result"
        
        self.log_thought("task_execution_complete", {
            "task": self.task_description,
            "result": result_str,
            "execution_time_seconds": execution_time,
            "insights_count": len(self.insights),
            "hypotheses_count": len(self.hypotheses),
            "conclusions_count": len(self.conclusions),
            "timestamp_readable": datetime.datetime.now().isoformat()
        })
        
        if self.conclusions:
            best_conclusion = max(self.conclusions, key=lambda x: x["confidence"])
            subject = f"タスク結論: {self.task_description}"
            self.update_knowledge(
                subject=subject,
                fact=best_conclusion["content"],
                confidence=best_conclusion["confidence"]
            )
    
    def _get_initial_knowledge(self) -> List[Dict]:
        """タスクに関連する初期知識を取得"""
        keywords = self._extract_keywords(self.task_description)
        
        return self.get_related_knowledge(keywords, limit=10)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抽出"""
        words = re.findall(r'\\b\\w+\\b', text.lower())
        return [w for w in words if len(w) > 3]
    
    def get_thinking_history(self, limit: int = 20) -> List[Dict]:
        """最近の思考履歴を取得"""
        try:
            if not os.path.exists(THINKING_LOG_PATH):
                return []
                
            history = []
            with open(THINKING_LOG_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        history.append(entry)
                    except:
                        continue
            
            return sorted(history, key=lambda x: x.get("timestamp", 0), reverse=True)[:limit]
        except Exception as e:
            print(f"思考履歴取得エラー: {str(e)}")
            return []
    
    def search_thinking_log(self, query: str, limit: int = 10) -> List[Dict]:
        """思考ログを検索"""
        try:
            if not os.path.exists(THINKING_LOG_PATH):
                return []
                
            results = []
            with open(THINKING_LOG_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_str = json.dumps(entry, ensure_ascii=False).lower()
                        if query.lower() in entry_str:
                            results.append(entry)
                    except:
                        continue
            
            return sorted(results, key=lambda x: x.get("timestamp", 0), reverse=True)[:limit]
        except Exception as e:
            print(f"思考ログ検索エラー: {str(e)}")
            return []

def main():
    try:
        task_info = globals().get('task_info', {})
        task_description = getattr(task_info, 'description', 'Unknown task')
        
        thinking = PersistentThinkingManager(task_description)
        
        if thinking.related_knowledge:
            print(f"タスク '{task_description}' に関連する既存知識が {len(thinking.related_knowledge)} 件見つかりました:")
            for i, knowledge in enumerate(thinking.related_knowledge):
                print(f"  {i+1}. {knowledge['subject']}: {knowledge['fact']} (確信度: {knowledge['confidence']:.2f})")
        else:
            print(f"タスク '{task_description}' に関連する既存知識は見つかりませんでした。")
            thinking.add_insight("このタスクに関連する既存知識がないため、新しい知識の獲得が必要")
        
        # メイン処理
{main_code}
        
        thinking.finalize_task(result if 'result' in locals() else "Task completed successfully")
        
        return result if 'result' in locals() else "Task completed successfully"
        
    except ImportError as e:
        # 必要なパッケージがない場合のエラー処理
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        error_msg = f"エラー: 必要なモジュール '{missing_module}' がインストールされていません。"
        print(error_msg)
        print(f"次のコマンドでインストールしてください: pip install {missing_module}")
        
        try:
            thinking = PersistentThinkingManager("エラー発生タスク")
            thinking.log_thought("task_execution_error", {
                "task": task_description,
                "error_type": "ImportError",
                "error_message": error_msg
            })
        except:
            pass
        
        return error_msg
        
    except Exception as e:
        # その他のエラー処理
        error_details = traceback.format_exc()
        error_msg = f"エラー: {str(e)}"
        print(error_msg)
        print(error_details)
        
        try:
            thinking = PersistentThinkingManager("エラー発生タスク")
            thinking.log_thought("task_execution_error", {
                "task": task_description,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": error_details
            })
            
            thinking.update_knowledge(
                f"エラーパターン: {type(e).__name__}",
                f"タスク実行中に発生: {str(e)}",
                confidence=0.7
            )
        except:
            pass
        
        return error_msg

# スクリプト実行
if __name__ == "__main__":
    result = main()
'''

def get_template_for_task(task_description, required_libraries=None):
    """
    タスクの説明に基づいて適切なテンプレートを選択
    常にPERSISTENT_THINKING_TEMPLATEを使用し、タスクタイプのみを記録
    
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
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"テンプレート選択のログ記録に失敗: {str(e)}")
    
    # テンプレート内のプレースホルダーを検証
    import re
    
    # 念のため、テンプレート内の中括弧をエスケープ（f文字列内の中括弧のみ）
    template = template.replace("{{", "{{").replace("}}", "}}")
    
    f_string_patterns = [
        ('f"Error: {str(e)}"', 'f"Error: {{str(e)}}"'),
        ('f"エラー: {str(e)}"', 'f"エラー: {{str(e)}}"'),
        ('f"', 'f"'),
        ('{str(e)}', '{{str(e)}}'),
        ('{e}', '{{e}}'),
        ('{type(e).__name__}', '{{type(e).__name__}}'),
        ('{result=}', '{{result=}}'),
        ('{val=}', '{{val=}}')
    ]
    
    for pattern, replacement in f_string_patterns:
        template = template.replace(pattern, replacement)
    
    template = template.replace("{imports}", "##IMPORTS##")
    template = template.replace("{main_code}", "##MAIN_CODE##")
    
    remaining_placeholders = re.findall(r'{([^{}]*)}', template)
    
    if remaining_placeholders:
        print(f"Warning: Escaping remaining placeholders: {remaining_placeholders}")
        for placeholder in remaining_placeholders:
            template = template.replace(f"{{{placeholder}}}", f"{{{{{placeholder}}}}}")
    
    template = template.replace("##IMPORTS##", "{imports}")
    template = template.replace("##MAIN_CODE##", "{main_code}")
    
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
        print(f"Error: {{str(e)}}")
        return str(e)
    
    return "Task completed successfully"

# スクリプト実行
if __name__ == "__main__":
    result = main()
"""
    
    return template
