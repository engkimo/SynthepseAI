
# 必要なライブラリのインポート
import matplotlib
import pyplot
import numpy
import typing
import Path
import warnings
import platform
import importlib
import os
import json
import time
import re
import datetime
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

task_info = {
    "task_id": "1f40bbe0-ca6a-4a4b-ad8f-83bbdbcc2656",
    "description": "必要なPythonライブラリをインポートし、ロギング・警告・乱数種・日本語フォント設定（例: Noto Sans CJK）を初期化する。ImportError時は不足ライブラリ名を明示して終了する。",
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
        
            "task_id": "1f40bbe0-ca6a-4a4b-ad8f-83bbdbcc2656",
            "description": "必要なPythonライブラリをインポートし、ロギング・警告・乱数種・日本語フォント設定（例: Noto Sans CJK）を初期化する。ImportError時は不足ライブラリ名を明示して終了する。",
            "plan_id": "e10bf2d3-25bb-4fb3-a073-49c8e45a434c"
        }
        
        task_description = task_info.get("description", "Unknown task")
        insights = []
        hypotheses = []
        conclusions = []
        
        
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
        
        def get_knowledge(query: str):
            """簡易検索: 件名またはfactにクエリ文字列を含むエントリを返す"""
            try:
                db = load_knowledge_db()
                results = []
                for subject, data in db.items():
                    fact = str(data.get("fact", ""))
                    if query in subject or query in fact:
                        entry = {"subject": subject}
                        entry.update(data)
                        results.append(entry)
                return results
            except Exception:
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
                result = None
                # Initialize result early
                result = {"success": False, "message": "Not started"}
        
                # Helper dynamic imports to avoid hard failures at top-level
                def _dyn_import(module_name):
                    try:
                        import importlib
                        return importlib.import_module(module_name)
                    except Exception:
                        return None
        
                def _now_ts():
                    try:
                        import datetime as _dt
                        return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        return "unknown-time"
        
                def _traceback_str():
                    try:
                        import traceback as _tb
                        return _tb.format_exc()
                    except Exception:
                        return "No traceback available"
        
                def _setup_logging():
                    import logging
                    import sys
                    from pathlib import Path
                    import time as _t
        
                    logger = logging.getLogger("init_env")
                    logger.setLevel(logging.DEBUG)
        
                    # Avoid duplicate handlers if re-run
                    if logger.handlers:
                        for h in list(logger.handlers):
                            logger.removeHandler(h)
        
                    log_dir = Path("logs")
                    try:
                        log_dir.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        pass
        
                    ts = _t.strftime("%Y%m%d-%H%M%S")
                    log_file = log_dir / f"init_{ts}.log"
        
                    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        
                    ch = logging.StreamHandler(stream=sys.stderr)
                    ch.setLevel(logging.INFO)
                    ch.setFormatter(fmt)
                    logger.addHandler(ch)
        
                    try:
                        import logging.handlers as handlers_mod
                        fh = handlers_mod.RotatingFileHandler(str(log_file), maxBytes=1_000_000, backupCount=3, encoding="utf-8")
                        fh.setLevel(logging.DEBUG)
                        fh.setFormatter(fmt)
                        logger.addHandler(fh)
                    except Exception:
                        # Fallback to FileHandler
                        try:
                            fh = logging.FileHandler(str(log_file), encoding="utf-8")
                            fh.setLevel(logging.DEBUG)
                            fh.setFormatter(fmt)
                            logger.addHandler(fh)
                        except Exception:
                            logger.warning("Failed to create log file; proceeding with console-only logging")
        
                    # Capture warnings
                    import warnings
                    warnings.simplefilter("default")
                    logging.captureWarnings(True)
        
                    return logger, str(log_file)
        
                def _env_fingerprint(mods):
                    import platform
                    import os as _os
                    import sys as _sys
        
                    info = {
                        "python_version": _sys.version.split()[0],
                        "platform": platform.platform(),
                        "machine": platform.machine(),
                        "processor": platform.processor(),
                        "python_build": platform.python_build(),
                        "python_implementation": platform.python_implementation(),
                        "env_time": _now_ts(),
                        "pid": _os.getpid(),
                    }
                    # Optional versions
                    for k in ("numpy", "pandas", "matplotlib", "seaborn"):
                        m = mods.get(k)
                        if m is not None:
                            info[f"{k}_version"] = getattr(m, "__version__", "unknown")
                    return info
        
                def _require_modules(logger):
                    # Define required and optional modules
                    std_required = ["logging", "warnings", "os", "sys", "pathlib", "platform", "datetime", "time", "traceback", "random", "json", "re", "io"]
                    third_required = ["numpy", "matplotlib"]  # keep essential only
                    third_optional = ["pandas", "seaborn"]
        
                    modules = {}
                    missing = []
        
                    # Import stdlib
                    for name in std_required:
                        try:
                            modules[name] = __import__(name)
                        except Exception:
                            missing.append(name)
        
                    # Import third-party required
                    for name in third_required:
                        m = _dyn_import(name)
                        if m is None:
                            missing.append(name)
                            modules[name] = None
                        else:
                            modules[name] = m
        
                    # Import third-party optional
                    for name in third_optional:
                        m = _dyn_import(name)
                        if m is None:
                            modules[name] = None
                        else:
                            modules[name] = m
        
                    # Matplotlib submodules as needed
                    if modules.get("matplotlib") is not None:
                        fm = _dyn_import("matplotlib.font_manager")
                        modules["matplotlib.font_manager"] = fm
        
                    if missing:
                        logger.error(f"Missing modules (some may be stdlib anomalies or third-party): {', '.join(missing)}")
                    return modules, missing
        
                def _set_global_seed(logger, modules):
                    os_mod = modules["os"]
                    random = modules["random"]
                    # Seed policy
                    env_seed = os_mod.environ.get("GLOBAL_SEED")
                    try:
                        seed = int(env_seed) if env_seed is not None else 2024
                    except Exception:
                        seed = 2024
        
                    # Hash seed for deterministic hashing
                    os_mod.environ["PYTHONHASHSEED"] = str(seed)
        
                    # Python random
                    try:
                        random.seed(seed)
                    except Exception as e:
                        logger.warning(f"Failed to seed random: {e}")
        
                    # NumPy RNG
                    np = modules.get("numpy")
                    if np is not None:
                        try:
                            np.random.seed(seed)
                        except Exception as e:
                            logger.warning(f"Failed to seed numpy: {e}")
        
                    # Log seed
                    logger.info(f"Global random seed set to {seed}")
                    return seed
        
                def _configure_matplotlib_and_font(logger, modules):
                    mplt = modules.get("matplotlib")
                    if mplt is None:
                        return None, False, "matplotlib missing"
        
                    # Set non-interactive backend before importing pyplot
                    try:
                        mplt.use("Agg", force=True)
                    except Exception as e:
                        logger.warning(f"Failed to set matplotlib backend to Agg: {e}")
        
                    # Now import pyplot
                    plt = _dyn_import("matplotlib.pyplot")
                    if plt is None:
                        return None, False, "matplotlib.pyplot missing"
        
                    fm = modules.get("matplotlib.font_manager")
                    if fm is None:
                        fm = _dyn_import("matplotlib.font_manager")
                        modules["matplotlib.font_manager"] = fm
        
                    # Candidate Japanese fonts
                    candidates = [
                        "Noto Sans CJK JP",
                        "Noto Sans JP",
                        "Source Han Sans",
                        "Source Han Sans JP",
                        "IPAexGothic",
                        "IPAGothic",
                        "Yu Gothic",
                        "YuGothic",
                        "Meiryo",
                        "MS Gothic",
                        "TakaoGothic",
                        "Hiragino Sans",
                        "Hiragino Kaku Gothic ProN",
                    ]
        
                    chosen = None
                    if fm is not None:
                        for fam in candidates:
                            try:
                                prop = fm.FontProperties(family=fam)
                                try:
                                    path = fm.findfont(prop, fallback_to_default=False)
                                except TypeError:
                                    path = fm.findfont(prop)
                                if path and isinstance(path, str):
                                    chosen = fam
                                    break
                            except Exception:
                                continue
        
                    if chosen:
                        try:
                            mplt.rcParams["font.family"] = chosen
                            mplt.rcParams["axes.unicode_minus"] = False
                            logger.info(f"Japanese font configured: {chosen}")
                        except Exception as e:
                            logger.warning(f"Failed to set Japanese font {chosen}: {e}")
                            chosen = None
                    else:
                        try:
                            mplt.rcParams["axes.unicode_minus"] = False
                        except Exception:
                            pass
                        logger.warning("No preferred Japanese font found. You may install 'Noto Sans CJK JP' for best results.")
        
                    # Test rendering with Japanese text
                    test_ok = False
                    test_message = "not tested"
                    try:
                        io = modules["io"]
                        buf = io.BytesIO()
                        fig, ax = plt.subplots(figsize=(3, 2), dpi=100)
                        ax.plot([0, 1, 2], [0, 1, 0])
                        ax.set_title("可視化テスト - 日本語")
                        ax.set_xlabel("時間")
                        ax.set_ylabel("値")
                        fig.tight_layout()
                        fig.savefig(buf, format="png")
                        plt.close(fig)
                        test_ok = True
                        test_message = "render success"
                        logger.info("Matplotlib Japanese rendering test: success")
                    except Exception as e:
                        test_message = f"render failed: {e}"
                        logger.warning(f"Matplotlib Japanese rendering test failed: {e}")
        
                    return chosen, test_ok, test_message
        
                def _configure_seaborn(logger, modules, font_family):
                    sns = modules.get("seaborn")
                    if sns is None:
                        logger.info("Seaborn not available; skipping seaborn theme configuration")
                        return False
                    try:
                        if font_family:
                            sns.set_theme(style="whitegrid", font=font_family, rc={"axes.unicode_minus": False})
                        else:
                            sns.set_theme(style="whitegrid", rc={"axes.unicode_minus": False})
                        logger.info("Seaborn theme configured")
                        return True
                    except Exception as e:
                        logger.warning(f"Failed to configure seaborn: {e}")
                        return False
        
                    global result
        
                    # Initialize logging first
                    logger, log_file = _setup_logging()
                    try:
                        # Knowledge DB interactions
                        kb = None
                        try:
                            kb = load_knowledge_db()
                        except Exception:
                            pass
        
                        log_thought("plan", "Starting environment initialization for data analysis and visualization")
                        update_knowledge("initialization", "Centralized init with logging, warnings, RNG seed, and font setup is critical", 0.9)
        
                        # Retrieve prior insights (safe)
                        try:
                            prior = get_knowledge("マルチエージェント討論") or []
                            log_thought("retrieval", f"Retrieved prior insights count: {len(prior)}")
                        except Exception:
                            log_thought("retrieval", "No prior insights retrieved")
        
                        # Import and verify modules
                        modules, missing = _require_modules(logger)
        
                        # Fail fast on required missing third-party modules
                        required_missing = [m for m in ("numpy", "matplotlib") if modules.get(m) is None]
                        if required_missing:
                            msg = "Missing required modules: " + ", ".join(required_missing)
                            hint = "Please install: pip install " + " ".join(required_missing)
                            logger.error(msg + " | " + hint)
                            log_thought("error", msg)
                            update_knowledge("dependency", f"Missing required: {', '.join(required_missing)}", 0.8)
                            if kb is not None:
                                try:
                                    save_knowledge_db(kb)
                                except Exception:
                                    pass
                            result = {
                                "success": False,
                                "message": msg,
                                "hint": hint,
                                "log_file": log_file,
                            }
                            return result
        
                        # Proceed with initialization
                        seed = _set_global_seed(logger, modules)
        
                        # Environment fingerprint
                        env = _env_fingerprint(modules)
                        logger.info(f"Environment: {env}")
                        update_knowledge("environment_fingerprint", str(env), 0.7)
        
                        # Configure matplotlib and Japanese font
                        font_family, render_ok, render_msg = _configure_matplotlib_and_font(logger, modules)
                        if font_family:
                            update_knowledge("japanese_font", f"Using font: {font_family}", 0.85)
                        else:
                            update_knowledge("japanese_font", "No preferred Japanese font found; fallback to default", 0.6)
        
                        update_knowledge("render_test", f"Matplotlib render test: {render_msg}", 0.75)
        
                        # Configure seaborn if available
                        seaborn_ok = _configure_seaborn(logger, modules, font_family)
        
                        # Hypothesis and test recording
                        log_thought("hypothesis", "If 'Noto Sans CJK JP' is present, Japanese glyphs render correctly without tofu boxes")
                        if render_ok:
                            log_thought("result", "Rendering test passed; hypothesis supported")
                            update_knowledge("hypothesis_result", "Japanese glyph rendering succeeded", 0.9)
                        else:
                            log_thought("result", "Rendering test failed; hypothesis not supported; alternative fonts or installation needed")
                            update_knowledge("hypothesis_result", "Japanese glyph rendering failed; install CJK font", 0.9)
        
                        # Summarize module availability
                        modules_summary = {
                            "numpy": modules.get("numpy") is not None,
                            "pandas": modules.get("pandas") is not None,
                            "matplotlib": modules.get("matplotlib") is not None,
                            "seaborn": modules.get("seaborn") is not None,
                        }
        
                        # Save knowledge DB state
                        if kb is not None:
                            try:
                                save_knowledge_db(kb)
                            except Exception:
                                pass
        
                        status_msg = "Initialization completed successfully"
                        logger.info(status_msg)
                        log_thought("decision", "Initialization finished; environment ready for data analysis")
                        result = {
                            "success": True,
                            "message": status_msg,
                            "log_file": log_file,
                            "modules": modules_summary,
                            "seed": seed,
                            "font_family": font_family,
                            "render_test_ok": render_ok,
                            "env": env,
                            "seaborn_configured": seaborn_ok,
                        }
                        return result
        
                    except Exception as e:
                        err = f"Initialization failed: {e}"
                        try:
                            import logging as _logging
                            _logging.getLogger("init_env").exception(err)
                        except Exception:
                            pass
                        log_thought("error", err)
                        update_knowledge("initialization_error", _traceback_str(), 0.6)
                        result = {
                            "success": False,
                            "message": err,
                            "traceback": _traceback_str(),
                        }
                        return result
        
                # Execute main
                result = main()
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