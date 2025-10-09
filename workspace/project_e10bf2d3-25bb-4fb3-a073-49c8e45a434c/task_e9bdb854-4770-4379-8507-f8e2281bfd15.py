
# 必要なライブラリのインポート
import candidate
import matplotlib
import numpy
import typing
import os
import json
import time
import re
import datetime
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

task_info = {
    "task_id": "e9bdb854-4770-4379-8507-f8e2281bfd15",
    "description": "ダウンロードした原本ファイルの検証（サイズ>0、拡張子/フォーマット整合、開封可能性、簡易ハッシュ記録）。不正ファイルは破棄して再取得を促す。",
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
        
            "task_id": "e9bdb854-4770-4379-8507-f8e2281bfd15",
            "description": "ダウンロードした原本ファイルの検証（サイズ>0、拡張子/フォーマット整合、開封可能性、簡易ハッシュ記録）。不正ファイルは破棄して再取得を促す。",
            "plan_id": "e10bf2d3-25bb-4fb3-a073-49c8e45a434c"
        }
        
        task_description = task_info.get("description", "Unknown task")
        insights = []
        hypotheses = []
        conclusions = []
        
        
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
        
        
        def get_knowledge(subject, default=None):
            try:
                db = load_knowledge_db()
                data = db.get(subject)
                if isinstance(data, dict):
                    return data.get("fact", default)
                return default
            except Exception as e:
                print(f"知識取得エラー: {str(e)}")
                return default
        
        
        def get_related_knowledge(keywords: List[str], limit: int = 50):
            try:
                db = load_knowledge_db()
                results = []
                kws = [str(k).lower() for k in keywords if k]
                for subject, data in db.items():
                    try:
                        subj_l = subject.lower()
                        fact = data.get("fact")
                        fact_s = json.dumps(fact, ensure_ascii=False) if not isinstance(fact, str) else fact
                        fact_l = fact_s.lower() if fact_s else ""
                        if any(k in subj_l or (k in fact_l) for k in kws):
                            results.append({
                                "subject": subject,
                                "fact": data.get("fact"),
                                "confidence": data.get("confidence"),
                                "last_updated": data.get("last_updated"),
                                "source": data.get("source")
                            })
                            if len(results) >= limit:
                                break
                    except Exception:
                        continue
                return results
            except Exception as e:
                print(f"関連知識取得エラー: {str(e)}")
                return []
        
        
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
        
        
            global task_description, insights, hypotheses, conclusions
            try:
                task_info_local = globals().get('task_info', {})
                task_description_local = task_info_local.get('description', 'Unknown task')
                task_start_time = time.time()
                task_description = task_description_local
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
                            try:
                                fact_text = data.get("fact", "")
                                if not isinstance(fact_text, str):
                                    fact_text = json.dumps(fact_text, ensure_ascii=False)
                                if keyword.lower() in subject.lower() or (fact_text and keyword.lower() in fact_text.lower()):
                                    related_knowledge.append({
                                        "subject": subject,
                                        "fact": data.get("fact"),
                                        "confidence": data.get("confidence", 0),
                                        "last_updated": data.get("last_updated"),
                                        "source": data.get("source")
                                    })
                                    break
                            except Exception:
                                continue
                except Exception as e:
                    print(f"関連知識取得エラー: {str(e)}")
                if related_knowledge:
                    print(f"タスク '{task_description}' に関連する既存知識が {len(related_knowledge)} 件見つかりました:")
                    for i, knowledge in enumerate(related_knowledge):
                        try:
                            fact_print = knowledge['fact']
                            if not isinstance(fact_print, str):
                                fact_print = json.dumps(fact_print, ensure_ascii=False)
                            print(f"  {i+1}. {knowledge['subject']}: {fact_print} (確信度: {knowledge.get('confidence', 0):.2f})")
                        except Exception:
                            continue
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
        
        
            try:
                result = None
                os_mod = __import__('os')
                sys = __import__('sys')
                hashlib = __import__('hashlib')
                json_mod = __import__('json')
                re_mod = __import__('re')
                csv = __import__('csv')
                time_mod = __import__('time')
                traceback_mod = __import__('traceback')
                pathlib = __import__('pathlib')
                datetime_mod = __import__('datetime')
                try:
                    pd = __import__('pandas')
                except Exception:
                    pd = None
                try:
                    openpyxl = __import__('openpyxl')
                except Exception:
                    openpyxl = None
        
                def safe_log(thought_type, content):
                    try:
                        log_thought(thought_type, content)
                    except Exception:
                        pass
        
                def add_knowledge(subject, fact, confidence=0.7):
                    try:
                        if not isinstance(fact, str):
                            fact_to_store = json_mod.dumps(fact, ensure_ascii=False)
                        else:
                            fact_to_store = fact
                        update_knowledge(subject, fact_to_store, confidence)
                    except Exception:
                        pass
        
                def check_dependencies():
                    deps = {
                        "pandas": pd is not None,
                        "openpyxl": openpyxl is not None,
                    }
                    messages = []
                    if not deps["pandas"]:
                        messages.append("pandas is not available. Excel reading tests may be limited.")
                    if not deps["openpyxl"]:
                        messages.append("openpyxl is not available. XLSX opening tests may be limited.")
                    if messages:
                        safe_log("observation", "Dependency check warnings: " + "; ".join(messages))
                    add_knowledge("validation_dependencies", {"dependencies": deps, "timestamp": time_mod.time()}, 0.7)
                    return deps
        
                def compute_file_hash(file_path, algo='sha256', chunk_size=1024 * 1024):
                    h = hashlib.new(algo)
                    with open(file_path, 'rb') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            h.update(chunk)
                    return h.hexdigest()
        
                def detect_file_format(file_path, max_sig=8):
                    with open(file_path, 'rb') as f:
                        sig = f.read(max_sig)
                    if len(sig) >= 4 and sig[0:4] == b'PK\x03\x04':
                        return 'xlsx'
                    if len(sig) >= 8 and sig[0:8] == b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1':
                        return 'xls'
                    try:
                        sig.decode('utf-8')
                        return 'csv_text'
                    except Exception:
                        try:
                            sig.decode('cp932')
                            return 'csv_text'
                        except Exception:
                            return 'unknown'
        
                def get_extension(file_path):
                    return pathlib.Path(file_path).suffix.lower()
        
                def open_csv_preview(file_path, max_rows=5):
                    encodings = ['utf-8-sig', 'utf-8', 'cp932', 'utf-16', 'latin1']
                    last_err = None
                    for enc in encodings:
                        try:
                            with open(file_path, 'r', encoding=enc, newline='') as f:
                                sample = f.read(4096)
                                f.seek(0)
                                sniffer = csv.Sniffer()
                                dialect = None
                                try:
                                    dialect = sniffer.sniff(sample)
                                except Exception:
                                    pass
                                reader = csv.reader(f, dialect=dialect) if dialect else csv.reader(f)
                                rows = []
                                for i, row in enumerate(reader):
                                    rows.append(row)
                                    if i + 1 >= max_rows:
                                        break
                                non_empty_rows = [r for r in rows if any((str(cell).strip() if cell is not None else "") for cell in r)]
                                if len(non_empty_rows) == 0:
                                    return False, f"No non-empty rows detected in CSV using encoding {enc}", {"encoding": enc, "rows": rows}
                                if len(non_empty_rows[0]) < 1:
                                    return False, f"CSV appears to have too few columns using encoding {enc}", {"encoding": enc, "rows": rows}
                                return True, f"CSV opened successfully with encoding {enc}", {"encoding": enc, "rows": rows}
                        except Exception as e:
                            last_err = str(e)
                            continue
                    return False, f"CSV could not be opened with tried encodings. Last error: {last_err}", {"encoding": None, "rows": []}
        
                def open_excel_preview(file_path, max_rows=5):
                    errors = []
                    if pd is not None:
                        try:
                            df = pd.read_excel(file_path, nrows=max_rows)
                            if df is not None and df.shape[0] >= 0:
                                return True, "Excel opened via pandas successfully", {"method": "pandas", "shape": list(df.shape), "columns": list(df.columns)}
                        except Exception as e:
                            errors.append(f"pandas read_excel failed: {e}")
                    if openpyxl is not None and get_extension(file_path) == ".xlsx":
                        try:
                            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                            ws = wb.active
                            rows = []
                            i = 0
                            for row in ws.iter_rows(values_only=True):
                                rows.append([c if c is not None else "" for c in row])
                                i += 1
                                if i >= max_rows:
                                    break
                            wb.close()
                            return True, "XLSX opened via openpyxl successfully", {"method": "openpyxl", "rows": rows}
                        except Exception as e:
                            errors.append(f"openpyxl load_workbook failed: {e}")
                    msg = "Excel open preview failed. " + ("; ".join(errors) if errors else "No Excel libraries available.")
                    return False, msg, {"method": None}
        
                def validate_file(file_path, deps):
                    info = {
                        "path": file_path,
                        "exists": os_mod.path.exists(file_path),
                        "size_bytes": None,
                        "size_ok": False,
                        "ext": get_extension(file_path),
                        "detected_format": None,
                        "ext_format_consistent": None,
                        "open_ok": False,
                        "open_message": "",
                        "hash": None,
                        "status": "unknown",
                        "issues": [],
                        "details": {},
                    }
                    if not info["exists"]:
                        info["status"] = "invalid"
                        info["issues"].append("File does not exist")
                        return info
                    try:
                        size = os_mod.path.getsize(file_path)
                        info["size_bytes"] = size
                        if size > 0:
                            info["size_ok"] = True
                        else:
                            info["issues"].append("File size is zero")
                    except Exception as e:
                        info["issues"].append(f"Failed to get file size: {e}")
                    try:
                        detected = detect_file_format(file_path)
                        info["detected_format"] = detected
                    except Exception as e:
                        info["issues"].append(f"Failed to detect file format: {e}")
                        detected = 'unknown'
                        info["detected_format"] = detected
                    allowed_exts = {".csv": "csv_text", ".xlsx": "xlsx", ".xls": "xls"}
                    if info["ext"] not in allowed_exts:
                        info["issues"].append(f"Unsupported extension: {info['ext']}")
                        info["ext_format_consistent"] = False
                    else:
                        info["ext_format_consistent"] = (allowed_exts[info["ext"]] == info["detected_format"]) or (info["detected_format"] == 'unknown')
                    try:
                        if info["ext"] == ".csv":
                            ok, msg, details = open_csv_preview(file_path)
                            info["open_ok"] = ok
                            info["open_message"] = msg
                            info["details"]["csv"] = details
                        elif info["ext"] in (".xlsx", ".xls"):
                            ok, msg, details = open_excel_preview(file_path)
                            info["open_ok"] = ok
                            info["open_message"] = msg
                            info["details"]["excel"] = details
                        else:
                            info["open_ok"] = False
                            info["open_message"] = "Unsupported extension for opening"
                    except Exception as e:
                        info["open_ok"] = False
                        info["open_message"] = f"Exception while opening: {e}"
                        info["issues"].append(f"Open exception: {e}")
                    try:
                        if info["size_ok"]:
                            info["hash"] = compute_file_hash(file_path, 'sha256')
                    except Exception as e:
                        info["issues"].append(f"Failed to compute hash: {e}")
                    if not info["size_ok"]:
                        info["status"] = "invalid"
                        info["issues"].append("Invalid due to zero size")
                    elif not info["ext_format_consistent"]:
                        info["status"] = "invalid"
                        info["issues"].append(f"Extension and detected format mismatch: ext={info['ext']} detected={info['detected_format']}")
                    elif not info["open_ok"]:
                        if info["ext"] in (".xlsx", ".xls") and not (deps.get("pandas") or deps.get("openpyxl")):
                            info["status"] = "needs_attention"
                            info["issues"].append("Could not test opening due to missing Excel libraries")
                        else:
                            info["status"] = "invalid"
                            info["issues"].append("File could not be opened successfully")
                    else:
                        info["status"] = "valid"
                    return info
        
                def move_to_quarantine(file_path, quarantine_dir):
                    try:
                        os_mod.makedirs(quarantine_dir, exist_ok=True)
                        base = os_mod.path.basename(file_path)
                        ts = datetime_mod.datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_name = f"{ts}__{base}"
                        target = os_mod.path.join(quarantine_dir, new_name)
                        counter = 1
                        while os_mod.path.exists(target):
                            new_name = f"{ts}__{counter}__{base}"
                            target = os_mod.path.join(quarantine_dir, new_name)
                            counter += 1
                        os_mod.replace(file_path, target)
                        return True, target
                    except Exception as e:
                        return False, str(e)
        
                def find_candidate_files(extra_paths=None, max_depth=3):
                    patterns = [
                        r'prime', r'プライム', r'listing', r'list', r'上場', r'銘柄', r'prime.*2024', r'2024.*prime',
                        r'2024', r'jpx', r'tse', r'tokyo', r'stock'
                    ]
                    allowed_exts = {".csv", ".xlsx", ".xls"}
                    candidate_dirs = set()
                    cwd = os_mod.getcwd()
                    candidate_dirs.add(cwd)
                    for d in ['data', 'downloads', 'download', 'cache', 'workspace', 'tmp', 'input']:
                        candidate_dirs.add(os_mod.path.join(cwd, d))
                    for env_key in ['DATA_DIR', 'DOWNLOAD_DIR', 'CACHE_DIR', 'WORKSPACE_DIR']:
                        val = os_mod.environ.get(env_key)
                        if val:
                            candidate_dirs.add(val)
                    if extra_paths:
                        for p in extra_paths:
                            candidate_dirs.add(p)
                    files = []
                    compiled = [re_mod.compile(pat, re_mod.IGNORECASE) for pat in patterns]
                    visited = set()
                    for root in list(candidate_dirs):
                        if not os_mod.path.isdir(root):
                            continue
                        queue = [(root, 0)]
                        while queue:
                            cur, depth = queue.pop(0)
                            if cur in visited:
                                continue
                            visited.add(cur)
                            try:
                                entries = os_mod.listdir(cur)
                            except Exception:
                                continue
                            for name in entries:
                                full = os_mod.path.join(cur, name)
                                if os_mod.path.isdir(full):
                                    if depth < max_depth:
                                        queue.append((full, depth + 1))
                                else:
                                    ext = pathlib.Path(full).suffix.lower()
                                    if ext in allowed_exts:
                                        fname = name.lower()
                                        if any(p.search(fname) for p in compiled):
                                            files.append(full)
                    return sorted(set(files))
        
                def plausible_prime_2024_filename(name):
                    name_l = name.lower()
                    keywords = ['prime', 'listing', 'list', '2024', 'jpx', 'tse', '上場', '銘柄', 'プライム']
                    score = sum(1 for k in keywords if k in name_l)
                    return score >= 2
        
                    safe_log("plan", "Start validation of downloaded JPX Prime 2024 files. Validate size, extension/format consistency, openability, and record hash. Invalid files will be quarantined and re-fetch will be suggested.")
                    result_summary = {
                        "validated_files": [],
                        "invalid_files": [],
                        "needs_attention": [],
                        "stats": {
                            "total": 0,
                            "valid": 0,
                            "invalid": 0,
                            "needs_attention": 0
                        },
                        "messages": [],
                        "dependency_warnings": []
                    }
                    deps = check_dependencies()
                    if not deps.get("pandas"):
                        result_summary["dependency_warnings"].append("pandas missing: Excel validation via pandas not available.")
                    if not deps.get("openpyxl"):
                        result_summary["dependency_warnings"].append("openpyxl missing: Native XLSX validation limited.")
                    candidates = set()
                    try:
                        known = get_knowledge("JPX_Prime_2024_source_files")
                        if isinstance(known, list):
                            for item in known:
                                try:
                                    if isinstance(item, str) and os_mod.path.exists(item):
                                        candidates.add(item)
                                except Exception:
                                    continue
                        elif isinstance(known, str) and os_mod.path.exists(known):
                            candidates.add(known)
                    except Exception:
                        pass
                    try:
                        related = get_related_knowledge(["JPX", "Prime", "2024", "listing"], limit=20)
                        if isinstance(related, list):
                            for entry in related:
                                try:
                                    text = json_mod.dumps(entry, ensure_ascii=False) if isinstance(entry, dict) else str(entry)
                                    for m in re_mod.findall(r'([A-Za-z]:\\[^\s\'"]+|\/[^\s\'"]+)', text):
                                        p = m.strip().strip('",\'')
                                        if os_mod.path.exists(p) and plausible_prime_2024_filename(os_mod.path.basename(p)):
                                            ext = pathlib.Path(p).suffix.lower()
                                            if ext in (".csv", ".xlsx", ".xls"):
                                                candidates.add(p)
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    extra_paths = []
                    try:
                        home = os_mod.path.expanduser("~")
                        extra_paths.append(os_mod.path.join(home, "Downloads"))
                    except Exception:
                        pass
                    discovered = find_candidate_files(extra_paths=extra_paths, max_depth=3)
                    for f in discovered:
                        candidates.add(f)
                    try:
                        for name in os_mod.listdir(os_mod.getcwd()):
                            f = os_mod.path.join(os_mod.getcwd(), name)
                            if os_mod.path.isfile(f) and pathlib.Path(f).suffix.lower() in (".csv", ".xlsx", ".xls"):
                                if plausible_prime_2024_filename(name):
                                    candidates.add(f)
                    except Exception:
                        pass
                    candidates = sorted(candidates)
                    if not candidates:
                        msg = "No candidate files found. Please run the download task to obtain 2024 Prime listing files."
                        safe_log("observation", msg)
                        result_summary["messages"].append(msg)
                        try:
                            urls_knowledge = get_knowledge("JPX_Prime_2024_candidate_urls")
                            if urls_knowledge:
                                add_knowledge("action_suggestion", {"suggestion": "Re-download files from candidate URLs", "urls": urls_knowledge}, 0.8)
                                result_summary["messages"].append("Candidate URLs found in knowledge DB; please re-run the downloader.")
                        except Exception:
                            pass
                        return result_summary
                    safe_log("hypothesis", f"Found {len(candidates)} candidate files. Hypothesis: At least one will be a valid CSV/XLSX Prime 2024 list.")
                    quarantine_dir = os_mod.path.join(os_mod.getcwd(), "invalid_discarded")
                    registry_subject = "file_hash_registry"
                    for path in candidates:
                        try:
                            info = validate_file(path, deps)
                            result_summary["stats"]["total"] += 1
                            registry_record = {
                                "path": info["path"],
                                "hash": info["hash"],
                                "size_bytes": info["size_bytes"],
                                "detected_format": info["detected_format"],
                                "ext": info["ext"],
                                "timestamp": time_mod.time(),
                                "status": info["status"]
                            }
                            add_knowledge(registry_subject, registry_record, 0.75)
                            if info["status"] == "valid":
                                result_summary["stats"]["valid"] += 1
                                result_summary["validated_files"].append(info)
                                safe_log("observation", f"Validated: {os_mod.path.basename(path)} hash={info['hash']}")
                            elif info["status"] == "needs_attention":
                                result_summary["stats"]["needs_attention"] += 1
                                result_summary["needs_attention"].append(info)
                                safe_log("decision", f"Needs attention: {os_mod.path.basename(path)} - {info['issues']}. Recommend installing missing dependencies or re-downloading.")
                            else:
                                result_summary["stats"]["invalid"] += 1
                                result_summary["invalid_files"].append(info)
                                safe_log("decision", f"Invalid file detected: {os_mod.path.basename(path)} - Issues: {info['issues']}")
                                moved, target_or_err = move_to_quarantine(path, quarantine_dir)
                                if moved:
                                    safe_log("observation", f"File moved to quarantine: {target_or_err}")
                                    info["quarantined_to"] = target_or_err
                                else:
                                    safe_log("error", f"Failed to quarantine file: {path} - {target_or_err}")
                                    info["quarantine_error"] = target_or_err
                        except Exception as e:
                            err_msg = f"Unexpected error during validation of {path}: {e}"
                            safe_log("error", err_msg + "\n" + traceback_mod.format_exc())
                            result_summary["messages"].append(err_msg)
                    if result_summary["stats"]["valid"] > 0:
                        add_knowledge("JPX_Prime_2024_validation", {
                            "summary": "Validation run successful for some files",
                            "stats": result_summary["stats"],
                            "timestamp": time_mod.time()
                        }, 0.8)
                    else:
                        add_knowledge("JPX_Prime_2024_validation", {
                            "summary": "No valid files found",
                            "stats": result_summary["stats"],
                            "timestamp": time_mod.time()
                        }, 0.6)
                    if result_summary["stats"]["invalid"] > 0:
                        result_summary["messages"].append("One or more files were invalid and have been quarantined. Please re-download the original 2024 Prime listing files.")
                    if result_summary["stats"]["needs_attention"] > 0:
                        if not deps.get("pandas") or not deps.get("openpyxl"):
                            result_summary["messages"].append("Install missing dependencies to fully validate Excel files: pip install pandas openpyxl")
                    safe_log("result", f"Validation completed. Stats: {result_summary['stats']}")
                    return result_summary
        
                try:
                    result = main_inner()
                except Exception as e:
                    safe_log("error", f"Fatal error in validation script: {e}\n{traceback_mod.format_exc()}")
                    result = {
                        "error": str(e),
                        "traceback": traceback_mod.format_exc(),
                        "message": "Validation script encountered a fatal error. Please check logs."
                    }
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