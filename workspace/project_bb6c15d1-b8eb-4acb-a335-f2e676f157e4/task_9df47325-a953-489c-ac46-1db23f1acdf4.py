
# 必要なライブラリのインポート
import numpy
import typing
import matplotlib
import os
import json
import time
import re
import datetime
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

task_info = {
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
        }
        
        # 必要なライブラリのインポート
        import os
        import json
        import time
        import datetime
        import traceback
        from typing import Dict, List, Any, Optional, Union, Tuple
        
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
                import matplotlib
                matplotlib.use("Agg")  # headless 環境向け
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
                        try:
                            return json.load(f)
                        except json.JSONDecodeError:
                            # 壊れたJSONを避けるためバックアップ
                            try:
                                backup_path = KNOWLEDGE_DB_PATH + ".corrupt_backup"
                                with open(backup_path, 'w', encoding='utf-8') as bf:
                                    bf.write(f.read())
                            except Exception:
                                pass
                            return {}
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
                local_vars: Dict[str, Any] = {}
                exec(simulation_code, {"__builtins__": __builtins__}, local_vars)
                simulation_result = local_vars.get("result", None)
                if simulation_result is not None:
                    result["simulation_result"] = str(simulation_result)
                    result["verified"] = bool(local_vars.get("verified", False))
                    result["confidence"] = float(local_vars.get("confidence", 0.5))
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
        
        def get_related_knowledge(keywords, limit=5):
            try:
                db = load_knowledge_db()
                if not isinstance(keywords, (list, tuple)):
                    keywords = [str(keywords)]
                kws = [str(k).lower() for k in keywords if isinstance(k, (str, bytes))]
                results = []
                for subject, data in db.items():
                    hay = f"{subject} {data.get('fact','')}".lower()
                    if any(k in hay for k in kws):
                        results.append({
                            "subject": subject,
                            "fact": data.get("fact"),
                            "confidence": data.get("confidence", 0),
                            "last_updated": data.get("last_updated"),
                            "source": data.get("source")
                        })
                        if len(results) >= int(limit or 5):
                            break
                return results
            except Exception:
                return []
        
            global task_description, insights, hypotheses, conclusions
            try:
                task_info_local = globals().get('task_info', {})
                task_description = task_info_local.get('description', 'Unknown task')
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
                            if keyword.lower() in subject.lower() or (isinstance(fact_text, str) and keyword.lower() in fact_text.lower()):
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
            """
            try:
                result = None
                errors: List[str] = []
                warnings: List[str] = []
                notes: List[str] = []
        
                # Safe imports helper
                def _import_module(name):
                    try:
                        return importlib.import_module(name)
                    except Exception:
                        return None
        
                os_mod = __import__('os')
                sys_mod = __import__('sys')
                time_mod = __import__('time')
                json_mod = __import__('json')
                hashlib_mod = __import__('hashlib')
                io_mod = __import__('io')
                csv_mod = __import__('csv')
                re_mod = __import__('re')
                random_mod = __import__('random')
                pathlib_mod = __import__('pathlib')
                traceback_mod = __import__('traceback')
        
                requests = _import_module('requests')
                chardet = _import_module('chardet')
                charset_normalizer = _import_module('charset_normalizer')
                pandas = _import_module('pandas')
                urllib = _import_module('urllib')
                urllib_request = getattr(urllib, 'request', None) if urllib else None
                urllib_error = getattr(urllib, 'error', None) if urllib else None
        
                # Knowledge DB setup
                try:
                    knowledge_db = load_knowledge_db()
                    log_thought('init', 'Loaded knowledge database successfully.')
                except Exception as e:
                    knowledge_db = {}
                    warnings.append('Knowledge DB could not be loaded.')
                    try:
                        log_thought('warning', f'Failed to load knowledge DB: {e}')
                    except Exception:
                        pass
        
                # Retrieve related knowledge to guide implementation
                try:
                    related = get_related_knowledge(['retry', 'encoding', 'CSV', 'cache', 'HTTP', '欠損', 'リトライ'], limit=5)
                    log_thought('context', f'Retrieved related knowledge entries: {len(related)}')
                except Exception:
                    related = []
                    try:
                        log_thought('warning', 'Could not retrieve related knowledge.')
                    except Exception:
                        pass
        
                # Set defaults and directories
                BASE_DIR = os_mod.getcwd()
                DATA_DIR = os_mod.path.join(BASE_DIR, 'data')
                CACHE_DIR = os_mod.path.join(BASE_DIR, '.cache_http')
                for _d in (DATA_DIR, CACHE_DIR):
                    try:
                        os_mod.makedirs(_d, exist_ok=True)
                    except Exception as e:
                        errors.append(f'Failed to create directory "{_d}": {e}')
        
                # Random seed stabilization
                try:
                    random_mod.seed(2024)
                    log_thought('decision', 'Random seed fixed to 2024 for reproducibility.')
                except Exception:
                    pass
        
                # User Agent builder
                def build_user_agent():
                    py_ver = f'{sys_mod.version_info.major}.{sys_mod.version_info.minor}.{sys_mod.version_info.micro}'
                    req_ver = getattr(requests, '__version__', 'n/a') if requests else 'n/a'
                    plat = sys_mod.platform
                    return f'Mozilla/5.0 (compatible; Prime2024Analytics/1.0; +https://example.invalid/bot) Python/{py_ver} Requests/{req_ver} ({plat})'
        
                DEFAULT_UA = build_user_agent()
        
                # Utility: File cache
                class FileCache:
                    def __init__(self, cache_dir):
                        self.cache_dir = cache_dir
                        try:
                            os_mod.makedirs(self.cache_dir, exist_ok=True)
                        except Exception as e:
                            raise RuntimeError(f'Cannot create cache directory: {e}')
        
                    def _hash(self, key):
                        if isinstance(key, str):
                            key = key.encode('utf-8', errors='ignore')
                        return hashlib_mod.sha256(key).hexdigest()
        
                    def _path(self, key_base, suffix):
                        return os_mod.path.join(self.cache_dir, f'{key_base}{suffix}')
        
                    def get(self, key):
                        h = self._hash(key)
                        bin_path = self._path(h, '.bin')
                        meta_path = self._path(h, '.meta.json')
                        if os_mod.path.exists(bin_path):
                            try:
                                with open(bin_path, 'rb') as f:
                                    data = f.read()
                            except Exception:
                                data = None
                            meta = None
                            if os_mod.path.exists(meta_path):
                                try:
                                    with open(meta_path, 'r', encoding='utf-8') as f:
                                        meta = json_mod.load(f)
                                except Exception:
                                    meta = None
                            return {'bytes': data, 'meta': meta, 'hash': h, 'bin_path': bin_path, 'meta_path': meta_path}
                        return {'bytes': None, 'meta': None, 'hash': h, 'bin_path': bin_path, 'meta_path': meta_path}
        
                    def set(self, key, data_bytes, meta):
                        h = self._hash(key)
                        bin_path = self._path(h, '.bin')
                        meta_path = self._path(h, '.meta.json')
                        try:
                            with open(bin_path, 'wb') as f:
                                f.write(data_bytes)
                        except Exception as e:
                            raise RuntimeError(f'Cache write error (data): {e}')
                        try:
                            with open(meta_path, 'w', encoding='utf-8') as f:
                                json_mod.dump(meta, f, ensure_ascii=False, indent=2)
                        except Exception as e:
                            raise RuntimeError(f'Cache write error (meta): {e}')
                        return {'bin_path': bin_path, 'meta_path': meta_path, 'hash': h}
        
                    def update_meta_timestamp(self, key, new_ts=None):
                        info = self.get(key)
                        meta = info.get('meta') or {}
                        meta['timestamp'] = float(new_ts if new_ts is not None else time_mod.time())
                        try:
                            with open(info['meta_path'], 'w', encoding='utf-8') as f:
                                json_mod.dump(meta, f, ensure_ascii=False, indent=2)
                        except Exception:
                            pass
                        return meta
        
                # Utility: Encoding detection
                def detect_encoding(data_bytes):
                    # Returns dict: {'encoding': str, 'confidence': float, 'source': 'bom|chardet|charset_normalizer|fallback'}
                    if not data_bytes:
                        return {'encoding': 'utf-8', 'confidence': 0.0, 'source': 'fallback-empty'}
                    # BOM detection
                    bom_map = {
                        b'\xef\xbb\xbf': ('utf-8-sig', 1.0, 'bom'),
                        b'\xff\xfe\x00\x00': ('utf-32le', 1.0, 'bom'),
                        b'\x00\x00\xfe\xff': ('utf-32be', 1.0, 'bom'),
                        b'\xff\xfe': ('utf-16le', 1.0, 'bom'),
                        b'\xfe\xff': ('utf-16be', 1.0, 'bom'),
                    }
                    for bom, info in bom_map.items():
                        if data_bytes.startswith(bom):
                            return {'encoding': info[0], 'confidence': info[1], 'source': info[2]}
                    # chardet
                    if chardet:
                        try:
                            res = chardet.detect(data_bytes[:65536])
                            enc = res.get('encoding')
                            conf = float(res.get('confidence') or 0.0)
                            if enc:
                                return {'encoding': enc, 'confidence': conf, 'source': 'chardet'}
                        except Exception:
                            pass
                    # charset_normalizer
                    if charset_normalizer:
                        try:
                            from_bytes = getattr(charset_normalizer, 'from_bytes', None)
                            if from_bytes:
                                result = from_bytes(data_bytes[:65536])
                                best = result.best()
                                if best:
                                    enc = best.encoding
                                    conf = float(getattr(best, 'confidence', 0.0) or 0.0)
                                    return {'encoding': enc, 'confidence': conf, 'source': 'charset_normalizer'}
                        except Exception:
                            pass
                    # Fallback: try utf-8 else cp932 then latin-1
                    for enc in ('utf-8', 'cp932', 'latin-1'):
                        try:
                            data_bytes.decode(enc)
                            return {'encoding': enc, 'confidence': 0.2, 'source': 'fallback-probe'}
                        except Exception:
                            continue
                    return {'encoding': 'utf-8', 'confidence': 0.0, 'source': 'fallback'}
        
                def decode_bytes(data_bytes, specified_encoding=None, errors='replace'):
                    used = None
                    if specified_encoding:
                        try:
                            text = data_bytes.decode(specified_encoding, errors=errors)
                            used = specified_encoding
                            return {'text': text, 'encoding': used, 'source': 'specified'}
                        except Exception:
                            pass
                    det = detect_encoding(data_bytes)
                    enc = det.get('encoding') or 'utf-8'
                    try:
                        text = data_bytes.decode(enc, errors=errors)
                        used = enc
                    except Exception:
                        # Secondary fallbacks
                        for alt in ('utf-8', 'cp932', 'latin-1'):
                            try:
                                text = data_bytes.decode(alt, errors=errors)
                                used = alt
                                break
                            except Exception:
                                continue
                        if used is None:
                            text = data_bytes.decode('utf-8', errors='replace')
                            used = 'utf-8'
                    return {'text': text, 'encoding': used, 'source': det.get('source', 'unknown')}
        
                # Utility: Robust CSV/TSV reading
                def read_delimited(data_or_path, encoding=None, delimiter='auto', pandas_prefer=True, errors='replace', sample_bytes=65536):
                    # Returns dict: {'data': DataFrame|list, 'delimiter': str, 'encoding': str, 'reader': 'pandas|csv', 'num_rows': int}
                    text = None
                    enc_used = encoding
                    is_path = False
                    try:
                        if isinstance(data_or_path, (bytes, bytearray)):
                            dec = decode_bytes(bytes(data_or_path), specified_encoding=encoding, errors=errors)
                            text = dec['text']
                            enc_used = dec['encoding']
                        elif isinstance(data_or_path, str):
                            if os_mod.path.exists(data_or_path) and os_mod.path.isfile(data_or_path):
                                is_path = True
                                try:
                                    with open(data_or_path, 'rb') as f:
                                        raw = f.read()
                                    dec = decode_bytes(raw, specified_encoding=encoding, errors=errors)
                                    text = dec['text']
                                    enc_used = dec['encoding']
                                except FileNotFoundError:
                                    raise
                            else:
                                text = data_or_path
                                if enc_used is None:
                                    enc_used = 'utf-8'
                        else:
                            # file-like?
                            if hasattr(data_or_path, 'read'):
                                raw = data_or_path.read()
                                if isinstance(raw, str):
                                    text = raw
                                    if enc_used is None:
                                        enc_used = 'utf-8'
                                else:
                                    dec = decode_bytes(raw, specified_encoding=encoding, errors=errors)
                                    text = dec['text']
                                    enc_used = dec['encoding']
                            else:
                                raise ValueError('Unsupported data_or_path type for read_delimited')
                    except Exception as e:
                        raise RuntimeError(f'Failed to prepare text for CSV/TSV reading: {e}')
        
                    # Determine delimiter
                    if delimiter and delimiter != 'auto':
                        delim = delimiter
                    else:
                        sample = text[:min(len(text), 5000)]
                        try:
                            sniff = csv_mod.Sniffer().sniff(sample, delimiters=[',', '\t', ';', '|'])
                            delim = sniff.delimiter
                        except Exception:
                            # Heuristic
                            counts = {
                                ',': sample.count(','),
                                '\t': sample.count('\t'),
                                ';': sample.count(';'),
                                '|': sample.count('|'),
                            }
                            delim = max(counts.items(), key=lambda kv: kv[1])[0] if counts else ','
                        # From extension hint
                        if is_path:
                            lower = data_or_path.lower()
                            if lower.endswith('.tsv') or lower.endswith('.tab'):
                                delim = '\t'
                            elif lower.endswith('.csv'):
                                delim = delim or ','
                        if not delim:
                            delim = ','
        
                    # Load data
                    num_rows = 0
                    reader_used = None
                    data = None
                    if pandas and pandas_prefer:
                        reader_used = 'pandas'
                        sio = io_mod.StringIO(text)
                        # Read with robust options
                        try:
                            df = pandas.read_csv(sio, sep=delim, engine='python', encoding=enc_used, on_bad_lines='skip')
                        except TypeError:
                            # For older pandas
                            try:
                                sio.seek(0)
                                df = pandas.read_csv(sio, sep=delim, engine='python', encoding=enc_used, error_bad_lines=False, warn_bad_lines=False)
                            except Exception as e:
                                warnings.append(f'pandas.read_csv failed: {e}; falling back to csv module')
                                reader_used = 'csv'
                                df = None
                        except Exception as e:
                            warnings.append(f'pandas.read_csv failed: {e}; falling back to csv module')
                            reader_used = 'csv'
                            df = None
                        if df is not None:
                            data = df
                            try:
                                num_rows = int(df.shape[0])
                            except Exception:
                                num_rows = 0
                    if data is None:
                        reader_used = 'csv'
                        sio = io_mod.StringIO(text)
                        try:
                            sample = text[:min(len(text), 5000)]
                            try:
                                has_header = csv_mod.Sniffer().has_header(sample)
                            except Exception:
                                has_header = True
                            if has_header:
                                reader = csv_mod.DictReader(sio, delimiter=delim)
                                rows = [row for row in reader]
                            else:
                                reader = csv_mod.reader(sio, delimiter=delim)
                                rows = [row for row in reader]
                            data = rows
                            num_rows = len(rows)
                        except Exception as e:
                            raise RuntimeError(f'csv reading failed: {e}')
        
                    return {'data': data, 'delimiter': delim, 'encoding': enc_used or 'utf-8', 'reader': reader_used, 'num_rows': num_rows}
        
                # Utility: HTTP download with retry/backoff/UA/timeout + caching
                def http_download(url, cache=None, ttl_seconds=None, timeout=30, max_retries=3, backoff_factor=0.8, max_backoff=10.0, headers=None, user_agent=None, use_conditional=True):
                    if not isinstance(url, str) or not url:
                        raise ValueError('url must be a non-empty string')
                    user_agent = user_agent or DEFAULT_UA
                    headers = dict(headers or {})
                    headers.setdefault('User-Agent', user_agent)
                    headers.setdefault('Accept', 'text/csv, text/plain, application/json;q=0.9, */*;q=0.8')
                    headers.setdefault('Accept-Encoding', 'gzip, deflate')
        
                    from_cache = False
                    final_status = None
                    response_headers = {}
                    data_bytes = None
                    enc_info = None
        
                    cache_obj = cache or FileCache(CACHE_DIR)
                    cache_info = cache_obj.get(url)
                    now_ts = time_mod.time()
                    # TTL short-circuit
                    if ttl_seconds is not None and cache_info['bytes'] is not None and cache_info['meta'] and isinstance(cache_info['meta'].get('timestamp'), (int, float)):
                        age = now_ts - float(cache_info['meta']['timestamp'])
                        if age <= float(ttl_seconds):
                            from_cache = True
                            final_status = cache_info['meta'].get('status') or 200
                            response_headers = cache_info['meta'].get('headers') or {}
                            data_bytes = cache_info['bytes']
                            enc_info = {'encoding': cache_info['meta'].get('encoding'), 'source': 'cache-meta', 'confidence': 1.0} if cache_info['meta'].get('encoding') else None
                            return {
                                'ok': True, 'status': final_status, 'from_cache': True, 'url': url,
                                'headers': response_headers, 'bytes': data_bytes, 'encoding_info': enc_info
                            }
        
                    # Conditional headers
                    if use_conditional and cache_info['meta']:
                        etag = cache_info['meta'].get('etag')
                        lm = cache_info['meta'].get('last_modified')
                        if etag:
                            headers['If-None-Match'] = etag
                        if lm:
                            headers['If-Modified-Since'] = lm
        
                    # Retry loop
                    attempt = 0
                    last_err = None
                    while attempt <= max_retries:
                        attempt += 1
                        try:
                            if requests:
                                sess = requests.Session()
                                resp = sess.get(url, headers=headers, timeout=timeout, stream=False)
                                final_status = resp.status_code
                                response_headers = dict(resp.headers or {})
                                if final_status == 304 and cache_info['bytes'] is not None:
                                    from_cache = True
                                    data_bytes = cache_info['bytes']
                                    cache_obj.update_meta_timestamp(url, new_ts=now_ts)
                                    break
                                elif final_status == 200:
                                    data_bytes = resp.content
                                    break
                                elif final_status in (429, 500, 502, 503, 504):
                                    raise RuntimeError(f'Transient HTTP status: {final_status}')
                                else:
                                    raise RuntimeError(f'HTTP error status: {final_status}')
                            else:
                                if not urllib_request:
                                    raise RuntimeError('Neither "requests" nor "urllib.request" available for HTTP')
                                req = urllib_request.Request(url, headers=headers, method='GET')
                                try:
                                    with urllib_request.urlopen(req, timeout=timeout) as resp:
                                        final_status = getattr(resp, 'status', 200)
                                        response_headers = dict(resp.headers) if hasattr(resp, 'headers') else {}
                                        data_bytes = resp.read()
                                        if final_status == 200:
                                            break
                                        elif final_status == 304 and cache_info['bytes'] is not None:
                                            from_cache = True
                                            data_bytes = cache_info['bytes']
                                            cache_obj.update_meta_timestamp(url, new_ts=now_ts)
                                            break
                                        elif final_status in (429, 500, 502, 503, 504):
                                            raise RuntimeError(f'Transient HTTP status: {final_status}')
                                        else:
                                            raise RuntimeError(f'HTTP error status: {final_status}')
                                except urllib_error.HTTPError as he:
                                    final_status = he.code
                                    if he.code == 304 and cache_info['bytes'] is not None:
                                        from_cache = True
                                        data_bytes = cache_info['bytes']
                                        cache_obj.update_meta_timestamp(url, new_ts=now_ts)
                                        break
                                    elif he.code in (429, 500, 502, 503, 504):
                                        raise RuntimeError(f'Transient HTTP status: {he.code}')
                                    else:
                                        raise RuntimeError(f'HTTP error status: {he.code}')
                        except Exception as e:
                            last_err = e
                            if attempt > max_retries:
                                break
                            # Backoff with jitter
                            backoff = min(max_backoff, (backoff_factor * (2 ** (attempt - 1))))
                            jitter = random_mod.uniform(0, backoff / 2.0)
                            sleep_s = backoff + jitter
                            try:
                                log_thought('retry', f'HTTP attempt {attempt}/{max_retries} failed: {e}; sleeping {sleep_s:.2f}s before retry.')
                            except Exception:
                                pass
                            time_mod.sleep(sleep_s)
                            continue
        
                    if data_bytes is None and not from_cache:
                        raise RuntimeError(f'HTTP download failed for {url}: {last_err or "Unknown error"}')
        
                    # Save to cache if not from cache
                    if not from_cache and data_bytes is not None:
                        enc_det = detect_encoding(data_bytes)
                        enc_info = enc_det
                        meta = {
                            'url': url,
                            'timestamp': float(time_mod.time()),
                            'status': int(final_status or 200),
                            'headers': response_headers,
                            'etag': response_headers.get('ETag'),
                            'last_modified': response_headers.get('Last-Modified'),
                            'encoding': enc_info.get('encoding')
                        }
                        try:
                            cache_obj.set(url, data_bytes, meta)
                        except Exception as e:
                            warnings.append(f'Failed to write cache: {e}')
        
                    return {
                        'ok': True, 'status': int(final_status or 200), 'from_cache': bool(from_cache), 'url': url,
                        'headers': response_headers, 'bytes': data_bytes, 'encoding_info': enc_info
                    }
        
                # Hypothesis-driven self-tests
                def self_test_utilities():
                    results: Dict[str, Any] = {'encoding_tests': {}, 'csv_tests': {}, 'http_test': {}}
                    # 1) Encoding detection hypothesis: detect UTF-8 and CP932 reasonably
                    try:
                        sample_text = 'テスト,値\nあ,1\nい,2\nう,3\n'
                        utf8_bytes = sample_text.encode('utf-8')
                        cp932_bytes = sample_text.encode('cp932', errors='ignore')
                        det_u = detect_encoding(utf8_bytes)
                        det_s = detect_encoding(cp932_bytes)
                        results['encoding_tests']['utf8'] = det_u
                        results['encoding_tests']['cp932'] = det_s
                        update_knowledge('encoding_detection_utf8', f'UTF-8 detected={det_u.get("encoding")} source={det_u.get("source")}', 0.9)
                        update_knowledge('encoding_detection_cp932', f'CP932 detected={det_s.get("encoding")} source={det_s.get("source")}', 0.7)
                    except Exception as e:
                        results['encoding_tests']['error'] = str(e)
                        try:
                            log_thought('error', f'Encoding detection test failed: {e}')
                        except Exception:
                            pass
        
                    # 2) CSV reading hypothesis: auto-delimiter works for comma and tab
                    try:
                        csv_text = 'col1,col2\n1,2\n3,4\n'
                        tsv_text = 'col1\tcol2\n1\t2\n3\t4\n'
                        r_csv = read_delimited(csv_text)
                        r_tsv = read_delimited(tsv_text)
                        results['csv_tests']['comma'] = {'delimiter': r_csv['delimiter'], 'rows': r_csv['num_rows'], 'reader': r_csv['reader']}
                        results['csv_tests']['tab'] = {'delimiter': r_tsv['delimiter'], 'rows': r_tsv['num_rows'], 'reader': r_tsv['reader']}
                        update_knowledge('csv_reader', f'Auto delimiter comma={r_csv["delimiter"]} tab={r_tsv["delimiter"]}', 0.8)
                    except Exception as e:
                        results['csv_tests']['error'] = str(e)
                        try:
                            log_thought('error', f'CSV reading test failed: {e}')
                        except Exception:
                            pass
        
                    # 3) HTTP download hypothesis: cache works and retries handled
                    try:
                        test_url = 'https://httpbin.org/etag/test-etag'
                        fc = FileCache(CACHE_DIR)
                        r1 = http_download(test_url, cache=fc, ttl_seconds=None, timeout=10, max_retries=2, backoff_factor=0.5, user_agent=DEFAULT_UA)
                        r2 = http_download(test_url, cache=fc, ttl_seconds=3600, timeout=10, max_retries=2, backoff_factor=0.5, user_agent=DEFAULT_UA)
                        results['http_test'] = {
                            'status1': r1.get('status'),
                            'from_cache1': r1.get('from_cache'),
                            'status2': r2.get('status'),
                            'from_cache2': r2.get('from_cache'),
                            'bytes_len': len(r1.get('bytes') or b'')
                        }
                        update_knowledge('http_cache', f'HTTP cache validated: first from_cache={r1.get("from_cache")} second from_cache={r2.get("from_cache")}', 0.85)
                    except Exception as e:
                        results['http_test'] = {'error': str(e)}
                        try:
                            log_thought('warning', f'HTTP test skipped or failed: {e}')
                        except Exception:
                            pass
        
                    return results
        
                # Summarize dependency availability
                deps = {
                    'requests': bool(requests),
                    'pandas': bool(pandas),
                    'chardet': bool(chardet),
                    'charset_normalizer': bool(charset_normalizer),
                    'urllib_request': bool(urllib_request),
                }
        
                for mod_name, present in deps.items():
                    if not present and mod_name in ('requests',):
                        warnings.append(f'Module "{mod_name}" not available. Falling back to urllib where possible.')
                    if not present and mod_name in ('pandas',):
                        warnings.append(f'Module "{mod_name}" not available. CSV will be parsed via Python csv module.')
                    if not present and mod_name in ('chardet', 'charset_normalizer'):
                        warnings.append('No advanced encoding detector available; using fallback heuristics.')
        
                # Execute self-tests and produce result
                try:
                    log_thought('plan', 'Implementing utilities: HTTP with retry/backoff/UA/timeout, encoding detection, robust CSV/TSV reading, file cache I/O.')
                except Exception:
                    pass
        
                test_outcomes = self_test_utilities()
        
                # Final result assembly
                result = {
                    'status': 'ok' if not errors else 'error',
                    'errors': errors,
                    'warnings': warnings,
                    'notes': notes,
                    'dependencies': deps,
                    'config': {
                        'data_dir': DATA_DIR,
                        'cache_dir': CACHE_DIR,
                        'user_agent': DEFAULT_UA
                    },
                    'utilities': {
                        'http_download': 'function',
                        'detect_encoding': 'function',
                        'decode_bytes': 'function',
                        'read_delimited': 'function',
                        'FileCache': 'class'
                    },
                    'tests': test_outcomes
                }
        
                # Persist any updates to knowledge DB (safe no-op if unchanged)
                try:
                    current_db = load_knowledge_db()
                    save_knowledge_db(current_db)
                    log_thought('result', f'Utilities implemented with tests. Status={result["status"]}')
                except Exception:
                    pass
        
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