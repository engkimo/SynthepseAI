
# 必要なライブラリのインポート
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
    "task_id": "d572590e-c797-455f-b7e9-0d9c1bdad336",
    "description": "銘柄メタデータを読み込み、プライム市場のみ抽出。列名を標準化（証券コード、銘柄名、業種、上場市場、時価総額等）。証券コードをティッカー（例: 7203.T）に正規化し、日本語列のエンコーディング問題を処理する。",
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
            "task_id": "d572590e-c797-455f-b7e9-0d9c1bdad336",
            "description": "銘柄メタデータを読み込み、プライム市場のみ抽出。列名を標準化（証券コード、銘柄名、業種、上場市場、時価総額等）。証券コードをティッカー（例: 7203.T）に正規化し、日本語列のエンコーディング問題を処理する。",
            "plan_id": "e10bf2d3-25bb-4fb3-a073-49c8e45a434c",
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
        
        def get_knowledge(subject: str):
            try:
                db = load_knowledge_db()
                return db.get(subject)
            except Exception as e:
                print(f"知識取得エラー: {str(e)}")
                return None
        
        def get_related_knowledge(keywords: List[str], limit: int = 10):
            try:
                db = load_knowledge_db()
                results = []
                for subject, data in db.items():
                    text = f"{subject} {data.get('fact','')}".lower()
                    if any(k.lower() in text for k in keywords):
                        results.append({"subject": subject, **data})
                        if len(results) >= limit:
                            break
                return results
            except Exception as e:
                print(f"関連知識取得エラー: {str(e)}")
                return []
        
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
                if simulation_result is not None:
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
                tinfo = globals().get('task_info', {})
                task_description = tinfo.get('description', 'Unknown task')
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
                            fact_text = data.get("fact", "")
                            if keyword.lower() in subject.lower() or (fact_text and keyword.lower() in str(fact_text).lower()):
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
                    "file_used": None,
                    "encoding": None,
                    "n_rows": 0,
                    "n_prime": 0,
                    "columns": [],
                    "data": [],
                    "errors": [],
                    "warnings": [],
                    "summary": {},
                    "hypotheses": [],
                    "tested_hypotheses": []
                }
        
                def _safe_import(module_name):
                    try:
                        return __import__(module_name), None
                    except Exception as e:
                        return None, e
        
                os_mod, _ = _safe_import("os")
                sys_mod, _ = _safe_import("sys")
                io_mod, _ = _safe_import("io")
                re_mod, _ = _safe_import("re")
                json_mod, _ = _safe_import("json")
                glob_mod, _ = _safe_import("glob")
                hashlib_mod, _ = _safe_import("hashlib")
                traceback_mod, _ = _safe_import("traceback")
                unicodedata_mod, _ = _safe_import("unicodedata")
                datetime_mod, _ = _safe_import("datetime")
                time_mod, _ = _safe_import("time")
                pandas, pandas_err = _safe_import("pandas")
                chardet, _ = _safe_import("chardet")
        
                def _log_info(message):
                    try:
                        log_thought("info", message)
                    except Exception:
                        pass
        
                def _log_warning(message):
                    try:
                        log_thought("warning", message)
                    except Exception:
                        pass
        
                def _log_error(message):
                    try:
                        log_thought("error", message)
                    except Exception:
                        pass
        
                def _update_knowledge(subject, fact, confidence=0.7):
                    try:
                        update_knowledge(subject, fact, confidence)
                    except Exception:
                        pass
        
                def _get_knowledge(subject):
                    try:
                        return get_knowledge(subject)
                    except Exception:
                        return None
        
                def _get_related_knowledge(keywords, limit=10):
                    try:
                        return get_related_knowledge(keywords, limit)
                    except Exception:
                        return []
        
                def normalize_text(text):
                    if text is None:
                        return ""
                    try:
                        text = str(text)
                    except Exception:
                        try:
                            text = f"{text}"
                        except Exception:
                            return ""
                    try:
                        text = unicodedata_mod.normalize("NFKC", text)
                    except Exception:
                        pass
                    text = text.replace("\u3000", " ")
                    text = text.strip()
                    return text
        
                def quick_file_hash(path, max_bytes=65536):
                    try:
                        h = hashlib_mod.sha256()
                        with open(path, "rb") as f:
                            chunk = f.read(max_bytes)
                            h.update(chunk)
                        return h.hexdigest()
                    except Exception:
                        return None
        
                def detect_encoding(path, sample_size=65536):
                    if chardet is None:
                        candidates = ["utf-8-sig", "utf-8", "cp932", "shift_jis", "euc_jp"]
                        _log_warning("chardet not available; will attempt common encodings.")
                        return candidates
                    try:
                        with open(path, "rb") as f:
                            data = f.read(sample_size)
                        guess = chardet.detect(data)
                        enc = guess.get("encoding") or ""
                        conf = guess.get("confidence") or 0.0
                        _log_info(f"Encoding detection: {enc} (confidence={conf:.2f}) for {os.path.basename(path)}")
                        if enc:
                            lower_enc = enc.lower()
                            if "shift_jis" in lower_enc or lower_enc == "sjis":
                                enc = "cp932"
                            elif lower_enc in ("utf-8", "utf_8", "utf8") and data.startswith(b"\xef\xbb\xbf"):
                                enc = "utf-8-sig"
                        candidates = []
                        if enc:
                            candidates.append(enc)
                        for alt in ("utf-8-sig", "utf-8", "cp932", "shift_jis", "euc_jp", "iso2022_jp"):
                            if alt not in candidates:
                                candidates.append(alt)
                        return candidates
                    except Exception as e:
                        _log_warning(f"Failed to detect encoding for {os.path.basename(path)}: {e}")
                        return ["utf-8-sig", "utf-8", "cp932", "shift_jis", "euc_jp"]
        
                def list_candidate_files():
                    try:
                        cwd = os.getcwd()
                    except Exception:
                        cwd = "."
                    search_dirs = [
                        cwd,
                        os.path.join(cwd, "data"),
                        os.path.join(cwd, "dataset"),
                        os.path.join(cwd, "datasets"),
                        os.path.join(cwd, "download"),
                        os.path.join(cwd, "downloads"),
                        os.path.join(cwd, "input"),
                        os.path.join(cwd, "resources"),
                        os.path.join(cwd, "workspace"),
                    ]
                    seen = set()
                    files = []
                    for d in search_dirs:
                        if not os.path.isdir(d):
                            continue
                        for ext in ("*.csv", "*.tsv", "*.xlsx", "*.xls"):
                            pattern = os.path.join(d, "**", ext)
                            try:
                                matches = glob_mod.glob(pattern, recursive=True)
                            except Exception:
                                matches = []
                            for path in matches:
                                try:
                                    abspath = os.path.abspath(path)
                                except Exception:
                                    abspath = path
                                if abspath not in seen and os.path.isfile(path):
                                    seen.add(abspath)
                                    files.append(abspath)
                    return files
        
                def score_file_name(path):
                    name = os.path.basename(path).lower()
                    score = 0
                    keywords = [
                        "metadata", "meta", "銘柄", "上場", "market", "listing", "prime", "プライム", "東証", "ticker",
                        "company", "企業", "銘柄一覧", "companies", "stock", "securities", "jpx", "tokyo"
                    ]
                    for kw in keywords:
                        if kw in name:
                            score += 2
                    if name.endswith(".csv") or name.endswith(".tsv"):
                        score += 1
                    if ".bak" in name or "backup" in name:
                        score -= 2
                    return score
        
                def validate_files(files):
                    valid = []
                    invalid = []
                    for path in files:
                        try:
                            st = os.stat(path)
                            if st.st_size <= 0:
                                invalid.append((path, "Empty file"))
                                continue
                            _, ext = os.path.splitext(path.lower())
                            if ext not in (".csv", ".tsv", ".xlsx", ".xls"):
                                invalid.append((path, f"Unsupported extension: {ext}"))
                                continue
                            with open(path, "rb") as f:
                                head = f.read(4096)
                                if head is None or len(head) == 0:
                                    invalid.append((path, "Cannot read file header"))
                                    continue
                            file_hash = quick_file_hash(path)
                            valid.append((path, file_hash))
                        except Exception as e:
                            invalid.append((path, f"Validation error: {e}"))
                    return valid, invalid
        
                def try_read_with_pandas(path):
                    if pandas is None:
                        raise RuntimeError("pandas is required but not available. Please install pandas to proceed.")
                    _, ext = os.path.splitext(path.lower())
                    df = None
                    used_encoding = None
                    read_errors = []
                    if ext in (".csv", ".tsv"):
                        seps = [","]
                        if ext == ".tsv":
                            seps = ["\t", ","]
                        encodings = detect_encoding(path)
                        for enc in encodings:
                            for sep in seps:
                                try:
                                    df = pandas.read_csv(path, encoding=enc, sep=sep, dtype=str, engine="python")
                                    used_encoding = enc
                                    return df, used_encoding
                                except Exception as e:
                                    read_errors.append(f"CSV read failed (enc={enc}, sep={'TAB' if sep=='\t' else sep}): {e}")
                                    continue
                    else:
                        engine = None
                        if ext == ".xlsx":
                            openpyxl, openpyxl_err = _safe_import("openpyxl")
                            if openpyxl is None:
                                _log_warning("openpyxl not available; attempting default engine for .xlsx.")
                            else:
                                engine = "openpyxl"
                        try:
                            df = pandas.read_excel(path, dtype=str, engine=engine)
                            used_encoding = "binary(excel)"
                            return df, used_encoding
                        except Exception as e:
                            read_errors.append(f"Excel read failed: {e}")
                    raise RuntimeError("Failed to read file with pandas. Errors: " + " | ".join(read_errors[:5]))
        
                def build_column_mapping(existing_mapping=None):
                    base_map = {
                        "証券コード": "証券コード",
                        "銘柄コード": "証券コード",
                        "コード": "証券コード",
                        "コード(4桁)": "証券コード",
                        "証券コード(4桁)": "証券コード",
                        "銘柄cd": "証券コード",
                        "code": "証券コード",
                        "securitycode": "証券コード",
                        "ticker": "証券コード",
                        "ティッカー": "ティッカー",
                        "銘柄名": "銘柄名",
                        "名称": "銘柄名",
                        "会社名": "銘柄名",
                        "企業名": "銘柄名",
                        "社名": "銘柄名",
                        "name": "銘柄名",
                        "company": "銘柄名",
                        "shortname": "銘柄名",
                        "業種": "業種",
                        "業種名": "業種",
                        "業種分類": "業種",
                        "セクター": "業種",
                        "sector": "業種",
                        "industry": "業種",
                        "上場市場": "上場市場",
                        "市場": "上場市場",
                        "市場区分": "上場市場",
                        "市場・商品区分": "上場市場",
                        "上場区分": "上場市場",
                        "市場名称": "上場市場",
                        "listing": "上場市場",
                        "market": "上場市場",
                        "section/品種": "上場市場",
                        "時価総額": "時価総額",
                        "時価総額(百万円)": "時価総額",
                        "時価総額［百万円］": "時価総額",
                        "時価総額[百万円]": "時価総額",
                        "時価総額 (百万円)": "時価総額",
                        "時価総額(円)": "時価総額",
                        "market cap": "時価総額",
                        "marketcap": "時価総額",
                        "時価総額(単位:百万円)": "時価総額",
                        "時価総額(単位：百万円)": "時価総額",
                        "証券取引所": "上場市場",
                        "取引所": "上場市場",
                    }
                    mapping_subject = "jp_stock_metadata_column_mapping"
                    kb_map = _get_knowledge(mapping_subject)
                    if isinstance(kb_map, dict):
                        for k, v in kb_map.items():
                            base_map[normalize_text(k).lower()] = normalize_text(v)
                    if isinstance(existing_mapping, dict):
                        for k, v in existing_mapping.items():
                            base_map[normalize_text(k).lower()] = normalize_text(v)
                    return base_map
        
                def normalize_header(header):
                    h = normalize_text(header)
                    h = h.replace("　", " ").replace(" ", "")
                    h_lower = h.lower()
                    return h_lower
        
                def apply_column_mapping(df, mapping):
                    col_map = {}
                    for col in list(df.columns):
                        key = normalize_header(col)
                        if key in mapping:
                            target = mapping[key]
                            col_map[col] = target
                    if len(col_map) == 0:
                        return df, {}
                    df2 = df.rename(columns=col_map)
                    return df2, col_map
        
                def normalize_market_label(label):
                    s = normalize_text(label).lower()
                    s = s.replace("（", "(").replace("）", ")")
                    replacements = {
                        "東証ﾌﾟﾗｲﾑ": "東証プライム",
                        "tse prime": "東証プライム",
                        "tosho prime": "東証プライム",
                        "prime market": "東証プライム",
                        "prime": "東証プライム",
                        "東証p": "東証プライム",
                        "prm": "東証プライム",
                        "p部": "東証プライム",
                    }
                    for k, v in replacements.items():
                        if k in s:
                            return v
                    if "ﾌﾟﾗｲﾑ" in s or "プライム" in s:
                        return "東証プライム"
                    if "東証プライム" in s:
                        return "東証プライム"
                    if "standard" in s or "スタンダード" in s or "std" in s:
                        return "東証スタンダード"
                    if "growth" in s or "グロース" in s or "gth" in s:
                        return "東証グロース"
                    return normalize_text(label)
        
                def is_prime_market(label):
                    lab = normalize_market_label(label)
                    return lab == "東証プライム" or "プライム" in lab
        
                def normalize_code_to_4digits(code):
                    s = normalize_text(code)
                    digits = "".join([ch for ch in s if ch.isdigit()])
                    if len(digits) >= 4:
                        digits = digits[:4]
                    else:
                        digits = digits.zfill(4)
                    return digits
        
                def to_ticker(code):
                    code4 = normalize_code_to_4digits(code)
                    return f"{code4}.T"
        
                def standardize_dataframe(df):
                    for c in df.columns:
                        try:
                            df[c] = df[c].astype(str)
                        except Exception:
                            pass
                    mapping = build_column_mapping()
                    df, used_map = apply_column_mapping(df, mapping)
                    if "証券コード" not in df.columns:
                        candidate_cols = [c for c in df.columns if "code" in normalize_header(c) or "ticker" in normalize_header(c)]
                        for c in candidate_cols:
                            if "ティッカー" not in df.columns and ("ticker" in normalize_header(c) or "ティッカー" in c):
                                df["ティッカー"] = df[c].astype(str).apply(lambda x: x if x.endswith(".T") else to_ticker(x))
                            df["証券コード"] = df[c].astype(str).apply(normalize_code_to_4digits)
                            break
                    if "ティッカー" not in df.columns:
                        if "ticker" in [normalize_header(c) for c in df.columns]:
                            for c in df.columns:
                                if normalize_header(c) == "ticker":
                                    df["ティッカー"] = df[c].astype(str).apply(lambda x: x if x.endswith(".T") else to_ticker(x))
                                    break
                        elif "証券コード" in df.columns:
                            df["ティッカー"] = df["証券コード"].astype(str).apply(to_ticker)
                    if "上場市場" in df.columns:
                        df["上場市場"] = df["上場市場"].apply(normalize_market_label)
                    required = ["証券コード", "銘柄名", "業種", "上場市場"]
                    for col in required:
                        if col not in df.columns:
                            df[col] = ""
                    if "時価総額" in df.columns:
                        def _to_num(x):
                            s = normalize_text(x)
                            s = s.replace(",", "").replace("円", "").replace("百万円", "")
                            try:
                                if s == "":
                                    return None
                                return float(s)
                            except Exception:
                                return None
                        df["時価総額"] = df["時価総額"].apply(_to_num)
                    if "証券コード" in df.columns:
                        df = df.drop_duplicates(subset=["証券コード"])
                    return df, used_map
        
                def filter_prime_only(df):
                    if "上場市場" not in df.columns:
                        return df.copy()
                    try:
                        mask = df["上場市場"].apply(is_prime_market)
                    except Exception:
                        mask = df["上場市場"].astype(str).apply(is_prime_market)
                    filtered = df[mask].copy()
                    return filtered
        
                def select_columns_for_output(df):
                    cols = []
                    for c in ["証券コード", "ティッカー", "銘柄名", "業種", "上場市場", "時価総額"]:
                        if c in df.columns:
                            cols.append(c)
                    extra_candidates = []
                    for c in df.columns:
                        if c not in cols:
                            ch = normalize_header(c)
                            if any(k in ch for k in ["設立", "本社", "住所", "url", "hp", "従業員", "売上", "利益", "shares", "発行済"]):
                                extra_candidates.append(c)
                    cols.extend(extra_candidates[:4])
                    return df[cols].copy()
        
                def summarize_markets(df):
                    if "上場市場" not in df.columns:
                        return {}
                    try:
                        counts = df["上場市場"].value_counts(dropna=False).to_dict()
                    except Exception:
                        counts = {}
                        for v in list(df["上場市場"]):
                            counts[v] = counts.get(v, 0) + 1
                    return counts
        
                try:
                    start_ts = time_mod.time()
                    _log_info("Task start: Load knowledge DB and prepare hypotheses.")
                    _ = load_knowledge_db()
                    hypothesis_1 = "Market labels for TSE Prime appear in multiple variants (e.g., 東証プライム, プライム, PRM, Prime)."
                    hypothesis_2 = "Column names vary; a mapping is required to standardize to 証券コード, 銘柄名, 業種, 上場市場, 時価総額."
                    result["hypotheses"] = [hypothesis_1, hypothesis_2]
                    for t, m in [("info", "Hypothesis 1: Prime market labels vary across datasets."),
                                 ("info", "Hypothesis 2: Column naming conventions differ and must be normalized.")]:
                        try:
                            log_thought(t, m)
                        except Exception:
                            pass
                    if pandas is None:
                        msg = "Missing required module: pandas. Please install it (e.g., pip install pandas)."
                        result["errors"].append(msg)
                        _log_error(msg)
                        result["status"] = "failed"
                        _update_knowledge("dependency:pandas", "pandas missing prevented reading tabular metadata.", 0.9)
                    else:
                        _log_info("pandas is available.")
                    if pandas is not None:
                        candidates = list_candidate_files()
                        if not candidates:
                            warn = "No candidate metadata files found in common directories. Place a CSV/TSV/XLSX/XLS file with stock metadata in the working directory."
                            result["warnings"].append(warn)
                            _log_warning(warn)
                        else:
                            _log_info(f"Found {len(candidates)} candidate files.")
                        valid, invalid = validate_files(candidates)
                        for path, reason in invalid:
                            msg = f"Invalid file skipped: {os.path.basename(path)} | Reason: {reason}"
                            result["warnings"].append(msg)
                            _log_warning(msg)
                        if len(valid) == 0:
                            if candidates:
                                _log_warning("All candidate files failed validation. Suggest re-downloading the source files.")
                                result["warnings"].append("All candidate files failed validation. Suggest re-downloading the source files.")
                            else:
                                _log_warning("No files to validate.")
                        else:
                            scored = []
                            for path, fhash in valid:
                                scored.append((score_file_name(path), path, fhash))
                            scored.sort(key=lambda x: x[0], reverse=True)
                            best_score, best_path, best_hash = scored[0]
                            _log_info(f"Selected file: {os.path.basename(best_path)} (score={best_score}, hash={best_hash})")
                            result["file_used"] = best_path
                            try:
                                df_raw, used_enc = try_read_with_pandas(best_path)
                                result["encoding"] = used_enc
                                _log_info(f"Loaded file with encoding={used_enc}, shape={df_raw.shape}")
                                df_std, used_map = standardize_dataframe(df_raw)
                                if used_map:
                                    _update_knowledge("jp_stock_metadata_column_mapping_used", used_map, 0.8)
                                    _log_info(f"Applied column mapping to {len(used_map)} columns.")
                                else:
                                    _log_warning("No column mapping applied; headers may already match or require additional rules.")
                                mk_summary_before = summarize_markets(df_raw.rename(columns=used_map) if used_map else df_raw)
                                if mk_summary_before:
                                    _update_knowledge("market_label_observations", mk_summary_before, 0.6)
                                df_prime = filter_prime_only(df_std)
                                market_counts = summarize_markets(df_std)
                                prime_counts = summarize_markets(df_prime)
                                result["n_rows"] = int(len(df_std))
                                result["n_prime"] = int(len(df_prime))
                                result["summary"] = {
                                    "market_counts_all": market_counts,
                                    "market_counts_prime": prime_counts,
                                    "file_hash": best_hash
                                }
                                tested = []
                                mk_labels = list(market_counts.keys()) if market_counts else []
                                varied = any(lab for lab in mk_labels if "東証プライム" not in str(lab))
                                tested.append({
                                    "hypothesis": hypothesis_1,
                                    "result": "supported" if varied else "inconclusive",
                                    "evidence": {"unique_market_labels": mk_labels}
                                })
                                required_cols = ["証券コード", "銘柄名", "業種", "上場市場"]
                                has_required = all(c in df_std.columns for c in required_cols)
                                tested.append({
                                    "hypothesis": hypothesis_2,
                                    "result": "supported" if has_required else "partially_supported",
                                    "evidence": {"columns_after_mapping": list(df_std.columns)}
                                })
                                result["tested_hypotheses"] = tested
                                for t in tested:
                                    _update_knowledge("tested_hypothesis", t, 0.8)
                                df_out = select_columns_for_output(df_prime if len(df_prime) > 0 else df_std)
                                result["columns"] = list(df_out.columns)
                                max_rows = 500
                                data_records = df_out.head(max_rows).to_dict(orient="records")
                                result["data"] = data_records
                                _update_knowledge("prime_filter_stats", {
                                    "file": os.path.basename(best_path),
                                    "total_rows": int(len(df_std)),
                                    "prime_rows": int(len(df_prime))
                                }, 0.85)
                                observed_prime_labels = [normalize_market_label(x) for x in (df_std["上場市場"].unique().tolist() if "上場市場" in df_std.columns else [])]
                                _update_knowledge("prime_market_label_variants", list(sorted(set(observed_prime_labels))), 0.7)
                                result["status"] = "success"
                                _log_info(f"Processing complete. Rows: total={len(df_std)}, prime={len(df_prime)}")
                            except Exception as e:
                                tb = traceback_mod.format_exc()
                                err = f"Failed to process file: {e}"
                                result["errors"].append(err)
                                result["errors"].append(tb)
                                _log_error(err)
                                _log_error(tb)
                                result["status"] = "failed"
                    duration = time_mod.time() - start_ts
                    if isinstance(result.get("summary"), dict):
                        result["summary"]["duration_sec"] = round(duration, 3)
                    else:
                        result["summary"] = {"duration_sec": round(duration, 3)}
                    try:
                        save_knowledge_db(load_knowledge_db())
                    except Exception:
                        pass
                except Exception as e:
                    tb = traceback.format_exc()
                    result["status"] = "failed"
                    result["errors"].append(f"Unexpected error: {e}")
                    result["errors"].append(tb)
                    _log_error(f"Unexpected error: {e}")
                    _log_error(tb)
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