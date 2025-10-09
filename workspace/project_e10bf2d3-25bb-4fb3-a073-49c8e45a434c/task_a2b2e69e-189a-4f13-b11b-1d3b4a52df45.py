
# 必要なライブラリのインポート
import matplotlib
import numpy
import typing
import importlib
import os
import json
import time
import re
import datetime
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

task_info = {
    "task_id": "a2b2e69e-189a-4f13-b11b-1d3b4a52df45",
    "description": "分析設定値を定義する（対象年=2024、日付範囲、出力/キャッシュ/データのパス、リスクフリーレート、タイムゾーン=Asia/Tokyo、リトライ回数・タイムアウト、プロキシ、使用データソースURL、フォント名等）。環境変数（.env）からAPIキーやプロキシを読み込む。",
    "plan_id": "e10bf2d3-25bb-4fb3-a073-49c8e45a434c"
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
        print(f"知識データベース読み込みエラー: {{str(e)}}")
        return {}

def save_knowledge_db(knowledge_db):
    try:
        os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
        with open(KNOWLEDGE_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(knowledge_db, fp=f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"知識データベース保存エラー: {{str(e)}}")
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
        print(f"思考ログ記録エラー: {{str(e)}}")
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
        print(f"知識更新エラー: {{str(e)}}")
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
        print(f"タスク結果統合エラー: {{str(e)}}")
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
        print(f"マルチエージェント討論リクエストエラー: {{str(e)}}")
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
            print(f"関連知識取得エラー: {{str(e)}}")
        
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
        print(f"タスク準備エラー: {{str(e)}}")
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
        import os
        import json
        import time
        import re
        import datetime
        import traceback
        from typing import Dict, List, Any, Optional, Union, Tuple
        
            "task_id": "a2b2e69e-189a-4f13-b11b-1d3b4a52df45",
            "description": "分析設定値を定義する（対象年=2024、日付範囲、出力/キャッシュ/データのパス、リスクフリーレート、タイムゾーン=Asia/Tokyo、リトライ回数・タイムアウト、プロキシ、使用データソースURL、フォント名等）。環境変数（.env）からAPIキーやプロキシを読み込む。",
            "plan_id": "e10bf2d3-25bb-4fb3-a073-49c8e45a434c"
        }
        
        task_description = task_info.get("description", "Unknown task")
        insights: List[Dict[str, Any]] = []
        hypotheses: List[Dict[str, Any]] = []
        conclusions: List[Dict[str, Any]] = []
        
        
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
        
        
            try:
                if os.path.exists(KNOWLEDGE_DB_PATH):
                    with open(KNOWLEDGE_DB_PATH, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return {}
            except Exception as e:
                print(f"知識データベース読み込みエラー: {str(e)}")
                return {}
        
        
            try:
                os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
                with open(KNOWLEDGE_DB_PATH, 'w', encoding='utf-8') as f:
                    json.dump(knowledge_db, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"知識データベース保存エラー: {str(e)}")
                return False
        
        
            try:
                os.makedirs(os.path.dirname(THINKING_LOG_PATH), exist_ok=True)
                log_entry = {
                    "timestamp": time.time(),
                    "type": thought_type,
                    "content": content
                }
                with open(THINKING_LOG_PATH, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                return True
            except Exception as e:
                print(f"思考ログ記録エラー: {str(e)}")
                return False
        
        
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
                    lines = task_result.split('\n')
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
        
        
        def get_related_knowledge(keywords: List[str], limit: int = 5) -> List[Dict[str, Any]]:
            """キーワードに関連する知識ベースの項目を返す"""
            try:
                db = load_knowledge_db()
                results: List[Dict[str, Any]] = []
                for subject, data in db.items():
                    text = f"{subject} {str(data.get('fact', ''))}"
                    if any(k.lower() in text.lower() for k in keywords):
                        results.append({
                            "subject": subject,
                            "fact": data.get("fact"),
                            "confidence": data.get("confidence", 0),
                            "last_updated": data.get("last_updated"),
                            "source": data.get("source")
                        })
                    if len(results) >= limit:
                        break
                return results
            except Exception as e:
                print(f"関連知識取得エラー: {str(e)}")
                return []
        
        
            global task_description, insights, hypotheses, conclusions
        
            try:
                info = globals().get('task_info', {})
                task_description = info.get('description', 'Unknown task')
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
        
        
            """
            タスクを実行して結果を返す関数
            この関数は継続的思考AIで得られた知見を活用し、結果を知識ベースに統合する
        
            Returns:
                Any: タスク実行結果（辞書形式が望ましい）
            """
            try:
                def safe_main():
                    try:
                        # Dynamic imports to adhere to optional dependencies
                        missing_optional = []
        
                        import importlib as importlib_mod
                        os_mod = __import__('os')
                        sys_mod = __import__('sys')
                        json_mod = __import__('json')
                        time_mod = __import__('time')
                        datetime_mod = __import__('datetime')
                        random_mod = __import__('random')
                        warnings_mod = __import__('warnings')
                        logging_mod = __import__('logging')
                        pathlib_mod = __import__('pathlib')
        
                        # Timezone support: prefer zoneinfo (stdlib), fallback to pytz
                        ZoneInfo = None
                        pytz = None
                        try:
                            zoneinfo = importlib_mod.import_module('zoneinfo')
                            ZoneInfo = getattr(zoneinfo, 'ZoneInfo', None)
                        except Exception:
                            ZoneInfo = None
        
                        if ZoneInfo is None:
                            try:
                                pytz = importlib_mod.import_module('pytz')
                            except Exception:
                                missing_optional.append('pytz (timezone fallback)')
                                pytz = None
        
                        # Optional scientific stack
                        try:
                            numpy = importlib_mod.import_module('numpy')
                        except Exception:
                            numpy = None
                            missing_optional.append('numpy')
        
                        try:
                            pandas = importlib_mod.import_module('pandas')
                        except Exception:
                            pandas = None
                            missing_optional.append('pandas')
        
                        # Matplotlib optional
                        matplotlib = None
                        mpl_pyplot = None
                        mpl_font_manager = None
                        try:
                            matplotlib = importlib_mod.import_module('matplotlib')
                            mpl_pyplot = importlib_mod.import_module('matplotlib.pyplot')
                            mpl_font_manager = importlib_mod.import_module('matplotlib.font_manager')
                        except Exception:
                            matplotlib = None
                            mpl_pyplot = None
                            mpl_font_manager = None
                            missing_optional.append('matplotlib')
        
                        # dotenv optional (we will fallback to manual loader)
                        load_dotenv = None
                        try:
                            dotenv_mod = importlib_mod.import_module('dotenv')
                            load_dotenv = getattr(dotenv_mod, 'load_dotenv', None)
                        except Exception:
                            load_dotenv = None
                            missing_optional.append('python-dotenv')
        
                        # Initialize logging
                        log_level = os_mod.environ.get('LOG_LEVEL', 'INFO').upper()
                        try:
                            level_value = getattr(logging_mod, log_level)
                        except Exception:
                            level_value = logging_mod.INFO
                        logging_mod.basicConfig(
                            level=level_value,
                            format='%(asctime)s [%(levelname)s] %(message)s'
                        )
                        logger = logging_mod.getLogger('prime2024_setup')
        
                        # Initialize warnings
                        warnings_mod.simplefilter('default')
                        if matplotlib is not None:
                            try:
                                warnings_mod.filterwarnings('ignore', category=UserWarning, module='matplotlib')
                            except Exception:
                                pass
        
                        # Thinking log: plan
                        log_thought('plan', 'Initialize environment, load .env, define 2024 analysis settings, configure fonts and randomness.')
        
                        # Load knowledge DB
                        knowledge_db = None
                        try:
                            knowledge_db = load_knowledge_db()
                        except Exception as e:
                            log_thought('warning', f'Could not load knowledge DB: {e}')
        
                        # Load .env
                        env_loaded = False
                        if load_dotenv is not None:
                            try:
                                r = load_dotenv()
                                env_loaded = r if r is not None else True
                            except Exception as e:
                                log_thought('warning', f'python-dotenv failed: {e}')
                        if not env_loaded:
                            # Manual .env loader
                            candidates = ['.env', os_mod.path.join(os_mod.getcwd(), '.env')]
                            for candidate in candidates:
                                if os_mod.path.exists(candidate):
                                    try:
                                        with open(candidate, 'r', encoding='utf-8') as f:
                                            for line in f:
                                                s = line.strip()
                                                if not s or s.startswith('#') or '=' not in s:
                                                    continue
                                                k, v = s.split('=', 1)
                                                k = k.strip()
                                                v = v.strip().strip('"').strip("'")
                                                if k and v is not None and k not in os_mod.environ:
                                                    os_mod.environ[k] = v
                                        env_loaded = True
                                        break
                                    except Exception as e:
                                        log_thought('warning', f'Failed to parse .env: {e}')
                        update_knowledge('environment', f'dotenv_loaded={env_loaded}', 0.9)
        
                        # Retrieve any related prior knowledge to build upon
                        try:
                            prior_font_knowledge = get_related_knowledge(['matplotlib', 'font', 'Japanese'], limit=3)
                            if prior_font_knowledge:
                                log_thought('analysis', f'Found prior font knowledge entries: {len(prior_font_knowledge)}')
                        except Exception as e:
                            log_thought('warning', f'get_related_knowledge failed: {e}')
        
                        # Project directories
                        Path = getattr(pathlib_mod, 'Path')
                        cwd = os_mod.getcwd()
                        base_dir = os_mod.environ.get('PROJECT_ROOT', cwd)
        
                        out_dir = Path(os_mod.environ.get('OUTPUT_DIR', os_mod.path.join(base_dir, 'output')))
                        cache_dir = Path(os_mod.environ.get('CACHE_DIR', os_mod.path.join(base_dir, 'cache')))
                        data_dir = Path(os_mod.environ.get('DATA_DIR', os_mod.path.join(base_dir, 'data')))
                        logs_dir = Path(os_mod.environ.get('LOG_DIR', os_mod.path.join(base_dir, 'logs')))
        
                        for d in [out_dir, cache_dir, data_dir, logs_dir]:
                            try:
                                d.mkdir(parents=True, exist_ok=True)
                            except Exception as e:
                                log_thought('warning', f'Failed to create directory {d}: {e}')
        
                        # Network config
                        proxies = {}
                        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY']:
                            val = os_mod.environ.get(key) or os_mod.environ.get(key.lower()) or os_mod.environ.get(key.upper())
                            if val:
                                proxies[key.upper()] = val
        
                        try:
                            retry_count = int(os_mod.environ.get('RETRY_COUNT', '3'))
                        except Exception:
                            retry_count = 3
        
                        try:
                            timeout_sec = float(os_mod.environ.get('TIMEOUT', '30'))
                        except Exception:
                            timeout_sec = 30.0
        
                        # Timezone
                        tz_name = os_mod.environ.get('TIMEZONE', 'Asia/Tokyo')
                        tzobj = None
                        if ZoneInfo is not None:
                            try:
                                tzobj = ZoneInfo(tz_name)
                            except Exception as e:
                                log_thought('warning', f'ZoneInfo failed for {tz_name}: {e}')
                        if tzobj is None and pytz is not None:
                            try:
                                tzobj = pytz.timezone(tz_name)
                            except Exception as e:
                                log_thought('error', f'pytz failed for {tz_name}: {e}')
                        if tzobj is None:
                            log_thought('warning', f'Timezone not available: {tz_name}; using naive datetimes')
        
                        # Date range for 2024
                        dt = datetime_mod.datetime
                        if tzobj is not None:
                            start_dt = dt(2024, 1, 1, 0, 0, 0, tzinfo=tzobj)
                            end_dt = dt(2024, 12, 31, 23, 59, 59, tzinfo=tzobj)
                        else:
                            start_dt = dt(2024, 1, 1, 0, 0, 0)
                            end_dt = dt(2024, 12, 31, 23, 59, 59)
        
                        # Risk-free rate (annualized, decimal)
                        try:
                            risk_free_rate = float(os_mod.environ.get('RISK_FREE_RATE', '0.005'))
                        except Exception:
                            risk_free_rate = 0.005
        
                        # Random seed initialization
                        try:
                            seed = int(os_mod.environ.get('RANDOM_SEED', '2024'))
                        except Exception:
                            seed = 2024
                        try:
                            random_mod.seed(seed)
                        except Exception:
                            pass
                        if numpy is not None:
                            try:
                                numpy.random.seed(seed)
                            except Exception:
                                pass
        
                        # Data sources (URLs)
                        data_sources = {
                            'JPX_prime_list_csv': 'https://www.jpx.co.jp/english/markets/statistics-equities/misc/01.html',
                            'JPX_prime_list_pdf': 'https://www.jpx.co.jp/english/markets/statistics-equities/misc/index.html',
                            'JPX_daily_quotes': 'https://www.jpx.co.jp/english/markets/statistics-equities/individual/index.html',
                            'EDINET_API': 'https://disclosure.edinet-fsa.go.jp/api/v2/documents.json',
                            'MOF_yields': 'https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/index.htm',
                            'YahooFinance': 'https://query1.finance.yahoo.com/v7/finance/download',
                            'Stooq_Daily': 'https://stooq.com/q/d/l/',
                            'Nikkei225_info': 'https://indexes.nikkei.co.jp/en/nkave/index'
                        }
        
                        # Font configuration (optional)
                        selected_font = None
                        font_test_results = []
                        try:
                            if matplotlib is not None and mpl_font_manager is not None:
                                FontProperties = getattr(mpl_font_manager, 'FontProperties', None)
                                findfont = getattr(mpl_font_manager, 'findfont', None)
                                if FontProperties is None or findfont is None:
                                    raise RuntimeError('matplotlib.font_manager does not expose required API')
        
                                preferred_fonts = [
                                    os_mod.environ.get('JP_FONT', 'Noto Sans CJK JP'),
                                    'Noto Sans JP',
                                    'Noto Sans CJK',
                                    'IPAGothic',
                                    'IPAexGothic',
                                    'Hiragino Sans',
                                    'Yu Gothic',
                                    'TakaoGothic'
                                ]
                                for fname in preferred_fonts:
                                    try:
                                        prop = FontProperties(family=fname)
                                        path = findfont(prop, fallback_to_default=False)
                                        if isinstance(path, str) and path.lower().endswith(('.ttf', '.otf', '.ttc')):
                                            selected_font = fname
                                            font_test_results.append({'font': fname, 'status': 'found', 'path': path})
                                            break
                                        else:
                                            font_test_results.append({'font': fname, 'status': 'not_found', 'detail': str(path)})
                                    except Exception as fe:
                                        font_test_results.append({'font': fname, 'status': 'error', 'error': str(fe)})
        
                                if selected_font:
                                    matplotlib.rcParams['font.family'] = selected_font
                                    matplotlib.rcParams['axes.unicode_minus'] = False
                                    log_thought('analysis', f'Selected Japanese font: {selected_font}')
                                    update_knowledge('matplotlib.font', f'Selected Japanese font: {selected_font}', 0.95)
                                else:
                                    warn_msg = 'No preferred Japanese font found; recommend installing "Noto Sans CJK JP".'
                                    log_thought('warning', warn_msg)
                                    update_knowledge('matplotlib.font', 'No Japanese font found; install Noto Sans CJK JP.', 0.9)
                            else:
                                log_thought('warning', 'matplotlib not available; skipping font configuration.')
                                update_knowledge('matplotlib.font', 'matplotlib not available; font config skipped', 0.7)
                        except Exception as e:
                            log_thought('error', f'Font configuration failed: {e}')
                            update_knowledge('matplotlib.font', f'Font configuration failed: {e}', 0.7)
        
                        # Hypotheses: environment variables provide proxies and API keys
                        log_thought('hypothesis', 'If .env is loaded, proxies and API keys should be present in os.environ.')
                        api_keys_present = []
                        for key in ['OPENAI_API_KEY', 'ALPHAVANTAGE_API_KEY', 'FMP_API_KEY', 'QUANDL_API_KEY', 'PROXY_USER', 'PROXY_PASS']:
                            if os_mod.environ.get(key):
                                api_keys_present.append(key)
                        if api_keys_present:
                            log_thought('result', f'API/Proxy secrets detected: {api_keys_present}')
                            update_knowledge('environment.secrets', f'Present: {",".join(api_keys_present)}', 0.8)
                        else:
                            log_thought('warning', 'No API keys detected in environment.')
        
                        # Test timezone correctness
                        time_hypothesis = {}
                        try:
                            now_local = datetime_mod.datetime.now(tzobj) if tzobj else datetime_mod.datetime.utcnow()
                            time_hypothesis['now'] = now_local.isoformat()
                            time_hypothesis['tzinfo_ok'] = bool(tzobj is not None and now_local.tzinfo is not None)
                        except Exception as e:
                            time_hypothesis['error'] = str(e)
                            log_thought('warning', f'Timezone test failed: {e}')
        
                        # Build settings
                        settings = {
                            'project': '2024年プライム上場企業のデータ分析',
                            'year': 2024,
                            'timezone': tz_name,
                            'date_range': {
                                'start': start_dt.isoformat(),
                                'end': end_dt.isoformat()
                            },
                            'paths': {
                                'base': str(base_dir),
                                'output': str(out_dir),
                                'cache': str(cache_dir),
                                'data': str(data_dir),
                                'logs': str(logs_dir)
                            },
                            'network': {
                                'retry_count': retry_count,
                                'timeout_sec': timeout_sec,
                                'proxies': proxies
                            },
                            'risk_free_rate': risk_free_rate,
                            'random_seed': seed,
                            'data_sources': data_sources,
                            'matplotlib': {
                                'selected_font': selected_font,
                                'font_tests': font_test_results
                            },
                            'secrets_present': api_keys_present,
                            'time_hypothesis': time_hypothesis,
                            'dependencies': {
                                'numpy': bool(numpy is not None),
                                'pandas': bool(pandas is not None),
                                'matplotlib': bool(matplotlib is not None),
                                'pytz': bool(pytz is not None),
                                'zoneinfo': bool(ZoneInfo is not None)
                            },
                            'missing_optional': missing_optional
                        }
        
                        # Persist any new knowledge (noop if knowledge_db is managed internally)
                        try:
                            if knowledge_db is not None:
                                save_knowledge_db(knowledge_db)
                        except Exception as e:
                            log_thought('warning', f'Failed to save knowledge DB: {e}')
        
                        status_msg = 'Analysis settings initialized successfully.'
                        return {
                            'status': 'ok',
                            'message': status_msg,
                            'settings': settings
                        }
        
                    except Exception as e:
                        err_msg = f'Unexpected error: {type(e).__name__}: {e}'
                        try:
                            log_thought('error', err_msg)
                        except Exception:
                            pass
                        return {'status': 'error', 'message': err_msg}
        
                result = safe_main()
                if result is None:
                    result = {"status": "ok", "message": "Task completed successfully"}
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
                        body = f"### Task\n- Description: {task_description}\n\n### Result Preview\n\n{preview}\n\n"
                        append_report("Task Result", body)
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
                except Exception:
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
                except Exception:
                    pass
        
                return error_msg
        
        
        if __name__ == "__main__":
            result = main()
        if result is None:
            result = "Task completed successfully"
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"タスク実行エラー: {{str(e)}}")
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
        error_msg = f"エラー: {{str(e)}}"
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
                f"タスク実行中に発生: {{str(e)}}",
                confidence=0.7
            )
        except:
            pass
            
        return error_msg

if __name__ == "__main__":
    result = main()