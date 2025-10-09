
# 必要なライブラリのインポート
import matplotlib
import JPX
import numpy
import typing
import Path
import os
import json
import time
import re
import datetime
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

task_info = {
    "task_id": "df0f4b71-3bf2-4ae8-9338-d2eec3121823",
    "description": "JPX等の公開情報から2024年のプライム上場銘柄リスト（CSV/XLSX）をダウンロードする。既知の候補URLを順に試行し、HTTPエラー時は指数バックオフでリトライ。失敗時はキャッシュにある最新ファイルにフォールバック。",
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
        # -*- coding: utf-8 -*-
            "task_id": "df0f4b71-3bf2-4ae8-9338-d2eec3121823",
            "description": "JPX等の公開情報から2024年のプライム上場銘柄リスト（CSV/XLSX）をダウンロードする。既知の候補URLを順に試行し、HTTPエラー時は指数バックオフでリトライ。失敗時はキャッシュにある最新ファイルにフォールバック。",
            "plan_id": "e10bf2d3-25bb-4fb3-a073-49c8e45a434c"
        }
        
        import os
        import json
        import time
        import re
        import datetime
        import traceback
        from typing import Dict, List, Any, Optional, Union, Tuple
        
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
        
        def get_related_knowledge(keywords: List[str], limit: int = 10):
            try:
                db = load_knowledge_db()
                results = []
                for subject, data in db.items():
                    fact = str(data.get("fact", ""))
                    content = f"{subject} {fact}"
                    if any(k.lower() in content.lower() for k in keywords):
                        results.append({
                            "subject": subject,
                            "fact": fact,
                            "confidence": data.get("confidence", 0),
                            "last_updated": data.get("last_updated"),
                            "source": data.get("source", None)
                        })
                    if len(results) >= limit:
                        break
                return results
            except Exception as e:
                log_thought("warning", f"関連知識の取得に失敗: {e}")
                return []
        
            global task_description, insights, hypotheses, conclusions
            try:
                ti = globals().get('task_info', {})
                task_description = ti.get('description', 'Unknown task')
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
        
            try:
                result = {
                    "status": "init",
                    "messages": [],
                    "dependencies": {},
                    "used_url": None,
                    "output_path": None,
                    "file_type": None,
                    "rows_count": None,
                    "fallback_used": False,
                    "errors": []
                }
        
                def _get_module(name, alias=None):
                    try:
                        module = __import__(name)
                        return module
                    except Exception:
                        return None
        
                def _get_from_module(module_name, fromlist):
                    try:
                        module = __import__(module_name, fromlist=fromlist)
                        return module
                    except Exception:
                        return None
        
                os_mod = _get_module("os")
                sys_mod = _get_module("sys")
                time_mod = _get_module("time")
                json_mod = _get_module("json")
                re_mod = _get_module("re")
                traceback_mod = _get_module("traceback")
                glob_mod = _get_module("glob")
                io_mod = _get_module("io")
                csv_mod = _get_module("csv")
                datetime_module = _get_from_module("datetime", ["datetime"])
                pathlib = _get_module("pathlib")
                Path = getattr(pathlib, "Path") if pathlib else None
                urllib_parse = _get_from_module("urllib.parse", ["urljoin"])
                urljoin = getattr(urllib_parse, "urljoin") if urllib_parse else None
        
                if not (os_mod and sys_mod and time_mod and re_mod and traceback_mod and Path and urljoin and datetime_module):
                    missing = []
                    if not os_mod: missing.append("os")
                    if not sys_mod: missing.append("sys")
                    if not time_mod: missing.append("time")
                    if not re_mod: missing.append("re")
                    if not traceback_mod: missing.append("traceback")
                    if not Path: missing.append("pathlib.Path")
                    if not urljoin: missing.append("urllib.parse.urljoin")
                    if not datetime_module: missing.append("datetime")
                    msg = "Missing critical standard modules: " + ", ".join(missing)
                    result["status"] = "failed"
                    result["errors"].append(msg)
                    log_thought("error", msg)
        
                def _now_str():
                    try:
                        return datetime_module.datetime.now().strftime("%Y%m%d_%H%M%S")
                    except Exception:
                        return "unknown_time"
        
                knowledge_db = None
                try:
                    knowledge_db = load_knowledge_db()
                    log_thought("info", "Loaded knowledge database successfully.")
                except Exception as e:
                    result["messages"].append("Could not load knowledge database; continuing without it.")
                    log_thought("warning", "Failed to load knowledge DB: " + str(e))
        
                log_thought("observation", "Previous task failed due to IndentationError. Ensuring consistent 4-space indentation and removing invalid imports.")
        
                def ensure_directories(base=None):
                    base_dir = Path(os_mod.getcwd()) if base is None else Path(base)
                    dirs = [
                        base_dir / "data" / "raw",
                        base_dir / "data" / "processed",
                        base_dir / "cache",
                        base_dir / "outputs" / "figures",
                        base_dir / "outputs" / "reports",
                        base_dir / "logs"
                    ]
                    created = []
                    for d in dirs:
                        try:
                            d.mkdir(parents=True, exist_ok=True)
                            created.append(str(d))
                        except Exception as e:
                            msg = f"Failed to create directory {d}: {e}"
                            result["errors"].append(msg)
                            log_thought("error", msg)
                    return {
                        "base_dir": str(base_dir),
                        "data_raw": str(dirs[0]),
                        "data_processed": str(dirs[1]),
                        "cache": str(dirs[2]),
                        "outputs_figures": str(dirs[3]),
                        "outputs_reports": str(dirs[4]),
                        "logs": str(dirs[5]),
                        "created": created
                    }
        
                dirs_info = ensure_directories()
                if len(result["errors"]) > 0:
                    result["messages"].append("Some directories could not be created; proceeding with available paths.")
        
                def append_run_log(message):
                    try:
                        logs_dir = Path(dirs_info["logs"])
                        logs_dir.mkdir(parents=True, exist_ok=True)
                        log_file = logs_dir / f"run_{_now_str()}.log"
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(message + "\n")
                    except Exception:
                        pass
        
                append_run_log("Run started: Ensuring directories and preparing download task.")
        
                def check_dependencies():
                    deps = {}
                    requests_mod = _get_module("requests")
                    deps["requests"] = {"available": requests_mod is not None, "module": requests_mod, "note": ""}
                    if requests_mod is None:
                        deps["requests"]["note"] = "Install with: pip install requests"
                        result["messages"].append("Module 'requests' not available. Online download will be skipped; attempting cache fallback.")
                        log_thought("warning", "requests module not found; cannot perform HTTP downloads.")
                    pandas_mod = _get_module("pandas")
                    deps["pandas"] = {"available": pandas_mod is not None, "module": pandas_mod, "note": ""}
                    if pandas_mod is None:
                        deps["pandas"]["note"] = "Install with: pip install pandas"
                        result["messages"].append("Module 'pandas' not available. Will skip detailed parsing; raw file will still be downloaded.")
                    openpyxl_mod = _get_module("openpyxl")
                    deps["openpyxl"] = {"available": openpyxl_mod is not None, "module": openpyxl_mod, "note": ""}
                    if openpyxl_mod is None:
                        deps["openpyxl"]["note"] = "Install with: pip install openpyxl"
                    return deps
        
                dependencies = check_dependencies()
                result["dependencies"] = {k: {"available": v["available"], "note": v["note"]} for k, v in dependencies.items()}
        
                def get_prior_candidate_urls():
                    urls = []
                    try:
                        related = get_related_knowledge(["JPX", "Prime", "2024", "list", "銘柄", "プライム"], limit=10)
                        if isinstance(related, list):
                            for item in related:
                                try:
                                    fact_str = json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
                                    for u in re.findall(r"https?://[^\s\"'>)]+", fact_str):
                                        if u not in urls:
                                            urls.append(u)
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    return urls
        
                prior_urls = get_prior_candidate_urls()
        
                seed_pages = [
                    "https://www.jpx.co.jp/markets/statistics-equities/misc/01.html",
                    "https://www.jpx.co.jp/english/markets/statistics-equities/misc/01.html",
                    "https://www.jpx.co.jp/markets/statistics-equities/misc/",
                    "https://www.jpx.co.jp/english/markets/statistics-equities/misc/",
                    "https://www.jpx.co.jp/listing/stocks/new/index.html",
                    "https://www.jpx.co.jp/english/listing/stocks/new/index.html"
                ]
        
                for u in prior_urls:
                    if any(ext in u.lower() for ext in [".csv", ".xlsx", ".xls", "/misc/", "01.html"]) and (u.startswith("http://") or u.startswith("https://")):
                        if u not in seed_pages:
                            seed_pages.append(u)
        
                def score_link(url):
                    s = 0
                    l = url.lower()
                    if l.endswith(".csv") or l.endswith(".xlsx") or l.endswith(".xls"):
                        s += 2
                    keywords = [
                        ("prime", 3),
                        ("プライム", 4),
                        ("securities", 2),
                        ("list", 2),
                        ("銘柄", 3),
                        ("上場", 2),
                        ("market", 1),
                        ("constituent", 3),
                        ("tse", 1),
                        ("prime-market", 3),
                        ("プライム市場", 4)
                    ]
                    for kw, w in keywords:
                        if kw in url:
                            s += w
                    if "2024" in url:
                        s += 4
                    if "-att/" in url:
                        s += 2
                    return s
        
                def http_get_with_retries(url, requests_mod, max_retries=5, timeout=30, backoff_factor=1.8):
                    tries = 0
                    last_err = None
                    while tries < max_retries:
                        tries += 1
                        try:
                            resp = requests_mod.get(url, timeout=timeout, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (compatible; DataCollector/1.0)"})
                            if 200 <= resp.status_code < 300:
                                return {"ok": True, "status": resp.status_code, "content": resp.content, "headers": dict(resp.headers)}
                            else:
                                if resp.status_code in (500, 502, 503, 504, 429) or tries < 3:
                                    sleep_s = (backoff_factor ** tries)
                                    log_thought("info", f"HTTP {resp.status_code} for {url}; retry {tries}/{max_retries} after {sleep_s:.1f}s.")
                                    time.sleep(sleep_s)
                                    continue
                                else:
                                    return {"ok": False, "status": resp.status_code, "error": f"HTTP {resp.status_code}", "content": b"", "headers": dict(resp.headers)}
                        except Exception as e:
                            last_err = e
                            sleep_s = (backoff_factor ** tries)
                            log_thought("warning", f"Request error for {url}: {e}; retry {tries}/{max_retries} after {sleep_s:.1f}s.")
                            time.sleep(sleep_s)
                    return {"ok": False, "status": None, "error": str(last_err) if last_err else "Unknown error", "content": b"", "headers": {}}
        
                def extract_links(html_bytes, base_url):
                    try:
                        text = html_bytes.decode("utf-8", errors="ignore")
                    except Exception:
                        try:
                            text = html_bytes.decode("cp932", errors="ignore")
                        except Exception:
                            text = str(html_bytes)
                    links = []
                    for m in re.finditer(r'href\s*=\s*["\']([^"\']+)["\']', text, flags=re.IGNORECASE):
                        href = m.group(1).strip()
                        if href.startswith("#") or href.lower().startswith("javascript:"):
                            continue
                        abs_url = urljoin(base_url, href)
                        if abs_url not in links:
                            links.append(abs_url)
                    return links
        
                def discover_candidate_files(requests_mod, seeds):
                    discovered = []
                    for page in seeds:
                        log_thought("info", f"Scraping seed page: {page}")
                        resp = http_get_with_retries(page, requests_mod=requests_mod, max_retries=4, timeout=30)
                        if not resp.get("ok"):
                            log_thought("warning", f"Failed to fetch seed page: {page} reason: {resp.get('error') or resp.get('status')}")
                            continue
                        links = extract_links(resp.get("content", b""), page)
                        for link in links:
                            lower = link.lower()
                            if lower.endswith(".csv") or lower.endswith(".xlsx") or lower.endswith(".xls"):
                                if any(key in link for key in ["prime", "プライム", "銘柄", "securities", "list", "constituent", "市場"]):
                                    discovered.append(link)
                            else:
                                if ("prime" in lower or "プライム" in link or "銘柄" in link) and (lower.endswith(".html") or lower.endswith("/")):
                                    discovered.append(link)
                    dedup = []
                    seen = set()
                    for u in discovered:
                        if u not in seen and (u.startswith("http://") or u.startswith("https://")):
                            seen.add(u)
                            dedup.append(u)
                    return dedup
        
                def resolve_file_links(requests_mod, candidates, max_depth=1):
                    file_links = []
                    visited = set()
                    def is_file(u):
                        lu = u.lower()
                        return lu.endswith(".csv") or lu.endswith(".xlsx") or lu.endswith(".xls")
                    frontier = list(candidates)
                    depth = 0
                    while depth <= max_depth and frontier:
                        next_frontier = []
                        for url in frontier:
                            if url in visited:
                                continue
                            visited.add(url)
                            if is_file(url):
                                file_links.append(url)
                                continue
                            resp = http_get_with_retries(url, requests_mod=requests_mod, max_retries=3, timeout=25)
                            if not resp.get("ok"):
                                continue
                            links = extract_links(resp.get("content", b""), url)
                            for l in links:
                                if l in visited:
                                    continue
                                if is_file(l):
                                    file_links.append(l)
                                else:
                                    if any(k in l for k in ["prime", "プライム", "銘柄", "securities", "constituent", "list", "市場"]):
                                        next_frontier.append(l)
                        depth += 1
                        frontier = next_frontier
                    unique_files = []
                    seenf = set()
                    for f in file_links:
                        if f not in seenf:
                            seenf.add(f)
                            unique_files.append(f)
                    unique_files.sort(key=lambda u: score_link(u), reverse=True)
                    return unique_files
        
                def download_file(requests_mod, file_url, cache_dir, raw_dir):
                    log_thought("info", f"Attempt to download file: {file_url}")
                    resp = http_get_with_retries(file_url, requests_mod=requests_mod, max_retries=5, timeout=60)
                    if not resp.get("ok"):
                        return {"ok": False, "error": f"Download failed: {resp.get('error') or resp.get('status')}"}
                    fname = None
                    try:
                        cd = resp.get("headers", {}).get("Content-Disposition", "")
                        m = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';]+)', cd, flags=re.IGNORECASE)
                        if m:
                            fname = m.group(1)
                    except Exception:
                        fname = None
                    if not fname:
                        fname = file_url.rstrip("/").split("/")[-1]
                        if not any(fname.lower().endswith(ext) for ext in [".csv", ".xlsx", ".xls"]):
                            ctype = (resp.get("headers", {}).get("Content-Type") or "").lower()
                            if "excel" in ctype:
                                fname = fname + ".xlsx"
                            elif "csv" in ctype or "text" in ctype:
                                fname = fname + ".csv"
                            else:
                                fname = fname + ".bin"
                    timestamp = _now_str()
                    lower = fname.lower()
                    if lower.endswith(".xlsx"):
                        fext = ".xlsx"
                    elif lower.endswith(".xls"):
                        fext = ".xls"
                    elif lower.endswith(".csv"):
                        fext = ".csv"
                    else:
                        fext = ".bin"
                    safe_fname = fname
                    if "2024" not in safe_fname:
                        safe_fname = safe_fname.replace(fext, f"_2024{fext}")
                    cache_name = f"prime_list_{timestamp}_{safe_fname}"
                    cache_path = Path(cache_dir) / cache_name
                    temp_path = Path(str(cache_path) + ".part")
                    try:
                        with open(temp_path, "wb") as f:
                            f.write(resp.get("content", b""))
                        temp_path.rename(cache_path)
                    except Exception as e:
                        return {"ok": False, "error": f"Failed saving to cache: {e}"}
                    try:
                        raw_path = Path(raw_dir) / cache_name
                        with open(cache_path, "rb") as src, open(raw_path, "wb") as dst:
                            dst.write(src.read())
                    except Exception as e:
                        log_thought("warning", f"Could not copy to data/raw: {e}")
                        raw_path = None
                    return {"ok": True, "cache_path": str(cache_path), "raw_path": str(raw_path) if raw_path else None, "file_type": fext}
        
                def find_latest_cache(cache_dir):
                    p = Path(cache_dir)
                    if not p.exists():
                        return None
                    files = []
                    for ext in ["*.csv", "*.xlsx", "*.xls", "*.*"]:
                        files.extend(list(p.glob(ext)))
                    if not files:
                        return None
                    def priority(path_obj):
                        name = path_obj.name.lower()
                        pri = 0
                        if "prime" in name or "プライム" in name:
                            pri += 5
                        if "2024" in name:
                            pri += 5
                        if any(name.endswith(e) for e in [".csv", ".xlsx", ".xls"]):
                            pri += 2
                        try:
                            mtime = path_obj.stat().st_mtime
                        except Exception:
                            mtime = 0
                        return (pri, mtime)
                    files.sort(key=lambda x: priority(x), reverse=True)
                    return str(files[0]) if files else None
        
                def summarize_file(file_path, pandas_mod):
                    summary = {"rows": None, "columns": None, "prime_rows": None, "notes": []}
                    if pandas_mod is None:
                        summary["notes"].append("pandas not available; skipping detailed parsing.")
                        return summary
                    try:
                        lower = file_path.lower()
                        df = None
                        if lower.endswith(".csv"):
                            encodings = ["utf-8-sig", "utf-8", "cp932", "shift-jis"]
                            for enc in encodings:
                                try:
                                    df = pandas_mod.read_csv(file_path, encoding=enc)
                                    summary["notes"].append(f"Parsed CSV with encoding {enc}.")
                                    break
                                except Exception:
                                    df = None
                            if df is None:
                                summary["notes"].append("Failed to parse CSV with common encodings.")
                                return summary
                        elif lower.endswith(".xlsx") or lower.endswith(".xls"):
                            try:
                                df = pandas_mod.read_excel(file_path)
                                summary["notes"].append("Parsed Excel file.")
                            except Exception as e:
                                summary["notes"].append(f"Failed to parse Excel: {e}")
                                return summary
                        if df is not None:
                            summary["rows"] = int(df.shape[0])
                            summary["columns"] = int(df.shape[1])
                            market_cols = ["市場区分", "市場・商品区分", "Market", "Market Segment", "市場", "MarketDivision", "Market division"]
                            found_col = None
                            for c in df.columns:
                                cl = str(c).strip()
                                if cl in market_cols or any(k in cl for k in ["市場", "Market"]):
                                    found_col = c
                                    break
                            if found_col is not None:
                                col_series = df[found_col].astype(str).str.lower()
                                prime_mask = col_series.str.contains("prime") | col_series.str.contains("プライム")
                                summary["prime_rows"] = int(prime_mask.sum())
                            else:
                                summary["notes"].append("Could not detect market segment column.")
                    except Exception as e:
                        summary["notes"].append(f"Error summarizing file: {e}")
                    return summary
        
                log_thought("hypothesis", "JPX seed pages contain links to 2024 Prime Market listed companies as CSV/XLSX attachments.")
        
                selected_file_path = None
                selected_url = None
                file_type = None
                used_fallback = False
        
                requests_mod = dependencies.get("requests", {}).get("module")
        
                if requests_mod:
                    log_thought("info", f"Discovering candidate links from {len(seed_pages)} seed pages.")
                    discovered = discover_candidate_files(requests_mod, seed_pages)
                    file_links = resolve_file_links(requests_mod, discovered, max_depth=1)
                    file_links = [u for u in file_links if u.lower().endswith((".csv", ".xlsx", ".xls"))]
                    prioritized = sorted(file_links, key=lambda u: (1 if "2024" in u else 0) + score_link(u), reverse=True)
                    for u in prioritized[:15]:
                        dl = download_file(requests_mod, u, dirs_info["cache"], dirs_info["data_raw"])
                        if dl.get("ok"):
                            selected_file_path = dl.get("cache_path")
                            selected_url = u
                            file_type = dl.get("file_type")
                            log_thought("result", f"Downloaded file from {u} to {selected_file_path}")
                            update_knowledge("JPX prime list 2024", f"Found downloadable file: {u}", 0.8)
                            break
                        else:
                            log_thought("warning", f"Failed to download {u}: {dl.get('error')}")
                else:
                    pass
        
                if not selected_file_path:
                    cache_latest = find_latest_cache(dirs_info["cache"])
                    if cache_latest:
                        selected_file_path = cache_latest
                        selected_url = None
                        used_fallback = True
                        file_type = "." + selected_file_path.lower().split(".")[-1]
                        msg = f"Used cached file: {selected_file_path}"
                        result["messages"].append(msg)
                        log_thought("info", msg)
                    else:
                        msg = "No cached file available for fallback."
                        result["errors"].append(msg)
                        log_thought("error", msg)
        
                summary = None
                if selected_file_path:
                    pandas_mod = dependencies.get("pandas", {}).get("module")
                    summary = summarize_file(selected_file_path, pandas_mod)
                    try:
                        from pathlib import Path as _Path
                        processed_dir = _Path(dirs_info["data_processed"])
                        processed_dir.mkdir(parents=True, exist_ok=True)
                        summary_path = processed_dir / f"prime_list_summary_{_now_str()}.json"
                        payload = {
                            "source_url": selected_url,
                            "file_path": selected_file_path,
                            "file_type": file_type,
                            "summary": summary
                        }
                        with open(summary_path, "w", encoding="utf-8") as f:
                            f.write(json.dumps(payload, ensure_ascii=False, indent=2))
                        log_thought("result", f"Wrote summary to {str(summary_path)}")
                        update_knowledge("JPX prime list 2024", f"Latest file cached at {selected_file_path}", 0.9 if not used_fallback else 0.6)
                    except Exception as e:
                        result["messages"].append(f"Failed to write summary: {e}")
        
                if selected_file_path:
                    result["status"] = "success" if not used_fallback else "partial"
                    result["used_url"] = selected_url
                    result["output_path"] = selected_file_path
                    result["file_type"] = file_type
                    result["fallback_used"] = used_fallback
                    if summary:
                        result["rows_count"] = summary.get("rows")
                        if summary.get("prime_rows") is not None:
                            result["messages"].append(f"Prime row count detected: {summary.get('prime_rows')}")
                else:
                    result["status"] = "failed"
                    if dependencies.get("requests", {}).get("available") is False:
                        result["messages"].append("requests module missing; cannot download online.")
                    result["messages"].append("Could not obtain 2024 Prime list from JPX or cache.")
        
                if result["status"] == "success":
                    log_thought("conclusion", "Hypothesis supported: Successfully obtained file via discovered link(s).")
                elif result["status"] == "partial":
                    log_thought("conclusion", "Hypothesis partially supported: Used cache fallback due to online retrieval issues.")
                else:
                    log_thought("conclusion", "Hypothesis not supported: Could not retrieve file and no cache available.")
        
                try:
                    if knowledge_db is not None:
                        save_knowledge_db(knowledge_db)
                except Exception:
                    pass
        
                return result if result is not None else {"status": "success"}
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