
# 必要なライブラリのインポート
import pandas
import to
import matplotlib
import numpy
import typing
import duplicates
import os
import json
import time
import re
import datetime
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

task_info = {
    "task_id": "f804db97-f79f-4435-8f81-a00a3d9ca99f",
    "description": "クリーニング済みの銘柄メタデータを永続化（CSVとParquet）し、解析で使用する最終リストを確定する。",
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
            "task_id": "f804db97-f79f-4435-8f81-a00a3d9ca99f",
            "description": "クリーニング済みの銘柄メタデータを永続化（CSVとParquet）し、解析で使用する最終リストを確定する。",
            "plan_id": "e10bf2d3-25bb-4fb3-a073-49c8e45a434c"
        }
        
        # 必要なライブラリのインポート
        import os
        import json
        import time
        import re
        import datetime
        import traceback
        import glob
        from typing import Dict, List, Any, Optional, Union, Tuple
        
        # Optional globals to prevent NameError when optional imports fail later
        pyarrow = None
        fastparquet = None
        pd = None
        np = None
        
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
                import numpy as np  # local import to avoid global dependency
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
                    json.dump(knowledge_db, fp=f, ensure_ascii=False, indent=2)
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
        
        
        def get_related_knowledge(keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
            """
            簡易的に知識DBからキーワードに関連するエントリを抽出
            """
            try:
                db = load_knowledge_db()
                results = []
                kws = [str(k).lower() for k in keywords if k]
                for subject, data in db.items():
                    text = f"{subject} {data.get('fact', '')}".lower()
                    if any(k in text for k in kws):
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
                log_thought("warning", f"get_related_knowledge failed: {e}")
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
        
                def _safe_import(module_name, alias=None, pip_name=None, required=True, thoughts_label=None):
                    try:
                        module = __import__(module_name)
                        if alias:
                            globals()[alias] = module
                        else:
                            globals()[module_name] = module
                        return module, None
                    except Exception as e:
                        msg = f"Missing required module '{module_name}'. Please install it"
                        if pip_name:
                            msg += f" via: pip install {pip_name}"
                        msg += f". Error: {str(e)}"
                        try:
                            log_thought("error", msg)
                        except Exception:
                            pass
                        if required:
                            return None, msg
                        else:
                            return None, None
        
                # Import core modules using __import__
                _os, err_os = _safe_import("os", alias="os", required=True)
                _sys, err_sys = _safe_import("sys", alias="sys", required=True)
                _json, err_json = _safe_import("json", alias="json", required=True)
                _re, err_re = _safe_import("re", alias="re", required=True)
                _glob, err_glob = _safe_import("glob", alias="glob", required=True)
                _traceback, err_tb = _safe_import("traceback", alias="traceback", required=True)
                _datetime_mod, err_dt = _safe_import("datetime", alias="datetime", required=True)
                _pathlib, err_pl = _safe_import("pathlib", alias="pathlib", required=True)
                _shutil, err_shutil = _safe_import("shutil", alias="shutil", required=False)
        
                # Import data stack
                _pd, err_pd = _safe_import("pandas", alias="pd", pip_name="pandas>=1.5", required=True)
                _np, err_np = _safe_import("numpy", alias="np", pip_name="numpy", required=False)
                _pa, err_pa = _safe_import("pyarrow", alias="pyarrow", pip_name="pyarrow", required=False)
                _fp, err_fp = _safe_import("fastparquet", alias="fastparquet", pip_name="fastparquet", required=False)
        
                _errors = [e for e in [err_os, err_sys, err_json, err_re, err_glob, err_tb, err_dt, err_pl, err_pd] if e]
                if _errors:
                    result = {"status": "failed", "message": " | ".join(_errors)}
                else:
                    try:
                        # Initialize
                        now_iso = datetime.datetime.now().isoformat()
                        task_subject = "prime_2024_metadata"
                        output_dir_candidates = [
                            os.environ.get("ANALYSIS_OUTPUT_DIR"),
                            "./artifacts/prime_2024",
                            "./output/prime_2024",
                            "./outputs/prime_2024"
                        ]
                        output_dir = next((d for d in output_dir_candidates if d), "./artifacts/prime_2024")
                        import pathlib as _pathlib_local
                        _pathlib_local.Path(output_dir).mkdir(parents=True, exist_ok=True)
        
                        # Thought logging and knowledge retrieval
                        log_thought("plan", "Attempt to load cleaned 2024 Prime market metadata, validate quality, and persist final list to CSV/Parquet with a quality report.")
                        kb = None
                        try:
                            kb = load_knowledge_db()
                        except Exception as e:
                            log_thought("warning", f"Could not load knowledge DB: {e}")
        
                        prior_knowledge = []
                        try:
                            prior_knowledge = get_related_knowledge(["prime", "プライム", "2024", "metadata", "銘柄", "上場"], limit=10) or []
                        except Exception as e:
                            log_thought("warning", f"Could not retrieve related knowledge: {e}")
        
                        # Hypothesis
                        log_thought("hypothesis", "A cleaned metadata file exists in common data directories or is referenced in knowledge DB; it includes code, name, sector, and market columns to filter for Prime.")
        
                        # Discover input files
                        def _candidate_files():
                            candidates = []
                            search_dirs = [
                                ".", "./data", "./dataset", "./datasets", "./input", "./inputs", "./workspace", "./workspace/data"
                            ]
                            patterns = [
                                "*prime*2024*.csv",
                                "*Prime*2024*.csv",
                                "*metadata*2024*.csv",
                                "*meta*2024*.csv",
                                "*prime*2024*.parquet",
                                "*Prime*2024*.parquet",
                                "*metadata*2024*.parquet",
                                "*meta*2024*.parquet",
                                "*jp*prime*2024*.*",
                                "*tokyo*prime*2024*.*",
                                "*clean*prime*2024*.*",
                                "*銘柄*2024*.*",
                                "*プライム*2024*.*"
                            ]
                            # From knowledge DB
                            for item in prior_knowledge:
                                try:
                                    text = json.dumps(item, ensure_ascii=False)
                                except Exception:
                                    text = str(item)
                                m = re.findall(r'((?:\.{0,2}/)?[\w\-/\\\.]*\.(?:csv|parquet))', text, flags=re.IGNORECASE)
                                for path in m:
                                    if os.path.isfile(path) and path not in candidates:
                                        candidates.append(path)
        
                            # Environment variable direct path
                            env_path = os.environ.get("PRIME_2024_METADATA_PATH")
                            if env_path and os.path.isfile(env_path) and env_path not in candidates:
                                candidates.append(env_path)
        
                            # Search filesystem
                            for d in search_dirs:
                                if not os.path.isdir(d):
                                    continue
                                for p in patterns:
                                    for f in glob.glob(os.path.join(d, p)):
                                        if os.path.isfile(f) and f not in candidates:
                                            candidates.append(f)
                            return candidates
        
                        candidates = _candidate_files()
                        log_thought("observation", f"Discovered {len(candidates)} candidate files.")
        
                        # Read helpers
                        def _read_dataframe(path):
                            ext = os.path.splitext(path)[1].lower()
                            if ext == ".csv":
                                # Try common encodings used in JP datasets
                                for enc in ["utf-8", "utf-8-sig", "cp932", "shift_jis", "euc_jp"]:
                                    try:
                                        df = pd.read_csv(path, dtype=str, encoding=enc)
                                        return df, {"encoding": enc, "format": "csv"}
                                    except Exception:
                                        continue
                                raise RuntimeError(f"Failed to read CSV with common encodings: {path}")
                            elif ext == ".parquet":
                                # Use available parquet engine if present
                                engine = None
                                if pyarrow is not None:
                                    engine = "pyarrow"
                                elif fastparquet is not None:
                                    engine = "fastparquet"
                                if engine is None:
                                    raise RuntimeError("No parquet engine available (pyarrow/fastparquet).")
                                df = pd.read_parquet(path, engine=engine)
                                # Ensure all are str where feasible
                                for c in df.columns:
                                    try:
                                        df[c] = df[c].astype(str)
                                    except Exception:
                                        pass
                                return df, {"encoding": None, "format": "parquet", "engine": engine}
                            else:
                                raise RuntimeError(f"Unsupported file extension: {ext}")
        
                        # Column normalization
                        def _normalize_columns(df):
                            colmap = {
                                "証券コード": "code",
                                "コード番号": "code",
                                "コード": "code",
                                "銘柄コード": "code",
                                "SecuritiesCode": "code",
                                "銘柄名": "name",
                                "銘柄": "name",
                                "CompanyName": "name",
                                "会社名": "name",
                                "名称": "name",
                                "業種": "sector",
                                "業種名": "sector",
                                "セクター": "sector",
                                "Sector": "sector",
                                "33業種区分": "sector33",
                                "17業種区分": "sector17",
                                "業種（TOPIX-17）": "sector17",
                                "市場": "market",
                                "市場区分": "market",
                                "市場・商品区分": "market",
                                "Market": "market",
                                "ステータス": "status",
                                "Status": "status",
                                "上場区分": "listing",
                                "上場廃止日": "delist_date",
                                "上場日": "list_date",
                                "基準日": "as_of",
                                "基準日付": "as_of",
                                "Date": "as_of",
                                "市場変更予定": "reassignment_flag",
                                "指定替え": "reassignment_flag",
                                "監理": "watch_flag",
                                "整理": "liquidation_flag",
                                "整理銘柄": "liquidation_flag",
                                "note": "note",
                                "備考": "note",
                            }
                            rename = {}
                            for c in df.columns:
                                if c in colmap:
                                    rename[c] = colmap[c]
                                else:
                                    # Try strip spaces and case-insensitive match
                                    c_clean = re.sub(r"\s+", "", c).lower()
                                    if c_clean in ["code", "ticker", "securitycode", "securitiescode"]:
                                        rename[c] = "code"
                                    elif c_clean in ["name", "companyname", "brandname", "issuername"]:
                                        rename[c] = "name"
                                    elif c_clean in ["sector", "industry", "gyoushu", "gyōshu"]:
                                        rename[c] = "sector"
                                    elif c_clean in ["market", "marketsegment", "ichiba", "marketdivision"]:
                                        rename[c] = "market"
                                    elif c_clean in ["status", "listingstatus"]:
                                        rename[c] = "status"
                            df = df.rename(columns=rename)
                            return df
        
                        # Heuristic: identify best candidate
                        best_df = None
                        read_meta = None
                        selected_path = None
                        reason = None
                        for path in candidates:
                            try:
                                df, meta = _read_dataframe(path)
                                df = _normalize_columns(df)
                                has_code = "code" in df.columns
                                has_name = "name" in df.columns
                                has_sector = "sector" in df.columns or "sector33" in df.columns or "sector17" in df.columns
                                has_market = "market" in df.columns
                                score = sum([has_code, has_name, has_sector, has_market]) + (1 if df.shape[0] > 50 else 0)
                                if has_code and score >= 3:
                                    best_df = df
                                    read_meta = meta
                                    selected_path = path
                                    reason = f"Score={score}, rows={df.shape[0]}"
                                    break
                            except Exception as e:
                                log_thought("warning", f"Failed to read candidate {path}: {e}")
        
                        if best_df is None:
                            msg = "No suitable cleaned metadata file found. Provide a CSV/Parquet with at least code,name,sector,(market) for 2024 Prime."
                            log_thought("error", msg)
                            result = {"status": "failed", "message": msg, "candidates_checked": len(candidates)}
                        else:
                            log_thought("decision", f"Selected input file: {selected_path} ({reason}); meta={read_meta}")
        
                            df_raw = best_df.copy()
        
                            # Data cleanup
                            issues = []
        
                            def add_issue(code, issue_type, detail, severity="info"):
                                issues.append({
                                    "code": code,
                                    "issue_type": issue_type,
                                    "detail": detail,
                                    "severity": severity
                                })
        
                            # Normalize code
                            if "code" not in df_raw.columns:
                                raise RuntimeError("Required column 'code' not found after normalization.")
                            df_raw["code"] = df_raw["code"].astype(str).str.strip()
                            # Extract 4+ digit numeric part if mixed
                            extracted = df_raw["code"].str.extract(r"(\d{4,6})", expand=False)
                            fixed_code_count = int((~extracted.isna() & (extracted != df_raw["code"])).sum())
                            df_raw["code"] = extracted.fillna(df_raw["code"])
                            if fixed_code_count > 0:
                                add_issue(None, "code_fixed", f"Codes normalized using digit extraction for {fixed_code_count} rows.", "warning")
        
                            # Normalize code (keep 4-6 digit strings)
                            def _normalize_code(c):
                                if isinstance(c, str) and c.isdigit():
                                    if len(c) >= 4:
                                        return c
                                return c
        
                            df_raw["code"] = df_raw["code"].apply(_normalize_code)
        
                            # Remove rows without valid numeric code
                            invalid_mask = ~df_raw["code"].astype(str).str.fullmatch(r"\d{4,6}")
                            invalid_count = int(invalid_mask.sum())
                            if invalid_count > 0:
                                add_issue(None, "invalid_code_removed", f"Removed {invalid_count} rows with invalid code.", "error")
                            df_raw = df_raw[~invalid_mask].copy()
        
                            # Attempt fill name/sector from duplicates of same code
                            for col in ["name", "sector"]:
                                if col in df_raw.columns:
                                    df_raw[col] = df_raw.groupby("code")[col].transform(lambda s: s.ffill().bfill())
        
                            # Drop exact duplicates
                            pre = df_raw.shape[0]
                            df_raw = df_raw.drop_duplicates(subset=["code"], keep="first")
                            dropped_dup = pre - df_raw.shape[0]
                            if dropped_dup > 0:
                                add_issue(None, "duplicate_codes_dropped", f"Dropped {dropped_dup} duplicate code rows.", "warning")
        
                            # Market filtering for Prime
                            def _is_prime(val):
                                if val is None:
                                    return False
                                s = str(val).lower()
                                return ("prime" in s) or ("プライム" in s)
        
                            if "market" in df_raw.columns:
                                prime_mask = df_raw["market"].apply(_is_prime)
                                prime_count = int(prime_mask.sum())
                                non_prime_count = int((~prime_mask).sum())
                                if prime_count == 0:
                                    add_issue(None, "market_filter", "No rows labeled as Prime; keeping all rows but logging warning.", "warning")
                                    df_prime = df_raw.copy()
                                else:
                                    df_prime = df_raw[prime_mask].copy()
                                    add_issue(None, "market_filter", f"Filtered to Prime market: kept {prime_count}, excluded {non_prime_count}.", "info")
                            else:
                                add_issue(None, "market_missing", "Market column missing; cannot filter by Prime. Keeping all rows.", "warning")
                                df_prime = df_raw.copy()
        
                            # Status-based exclusions: delisted or liquidation flags
                            excluded_reasons = []
                            if "status" in df_prime.columns:
                                delist_mask = df_prime["status"].astype(str).str.contains("上場廃止|delist|整理", case=False, na=False)
                                count = int(delist_mask.sum())
                                if count > 0:
                                    excluded_reasons.append(("delisted_status", count))
                                    df_prime = df_prime[~delist_mask].copy()
                            if "liquidation_flag" in df_prime.columns:
                                liq_mask = df_prime["liquidation_flag"].astype(str).str.contains("(^1$)|true|有|あり|Yes|yes", case=False, na=False)
                                count = int(liq_mask.sum())
                                if count > 0:
                                    excluded_reasons.append(("liquidation_flag", count))
                                    df_prime = df_prime[~liq_mask].copy()
                            for r, c in excluded_reasons:
                                add_issue(None, "status_exclusion", f"Excluded {c} rows due to {r}.", "warning")
        
                            # Missing name/sector handling
                            missing_name = int(df_prime["name"].isna().sum()) if "name" in df_prime.columns else 0
                            missing_sector = None
                            if "sector" in df_prime.columns:
                                missing_sector = int(df_prime["sector"].isna().sum())
                            elif "sector33" in df_prime.columns:
                                df_prime["sector"] = df_prime["sector33"]
                                missing_sector = int(df_prime["sector"].isna().sum())
                            elif "sector17" in df_prime.columns:
                                df_prime["sector"] = df_prime["sector17"]
                                missing_sector = int(df_prime["sector"].isna().sum())
                            else:
                                add_issue(None, "sector_missing", "No sector column available. Proceeding without sector.", "warning")
                            if missing_name and missing_name > 0:
                                add_issue(None, "missing_name", f"{missing_name} rows have missing name.", "warning")
                            if missing_sector is not None and missing_sector > 0:
                                add_issue(None, "missing_sector", f"{missing_sector} rows have missing sector.", "warning")
        
                            # Reassignment flag: mark but do not exclude by default
                            if "reassignment_flag" in df_prime.columns:
                                reassign_true = df_prime["reassignment_flag"].astype(str).str.contains("(^1$)|true|有|あり|予定|Yes|yes", case=False, na=False).sum()
                                if reassign_true > 0:
                                    add_issue(None, "reassignment_flag", f"{int(reassign_true)} rows flagged for market change; retained but flagged.", "info")
        
                            # Finalize minimal schema
                            keep_cols = []
                            for col in ["code", "name", "sector", "market", "status", "as_of", "list_date", "delist_date", "reassignment_flag"]:
                                if col in df_prime.columns:
                                    keep_cols.append(col)
                            df_final = df_prime[keep_cols].copy()
        
                            # Infer as_of if missing
                            if "as_of" not in df_final.columns:
                                df_final["as_of"] = "2024-12-31"
                                add_issue(None, "as_of_inferred", "Missing as_of; defaulted to 2024-12-31.", "info")
                            else:
                                # Normalize date text to YYYY-MM-DD if possible
                                def _norm_date(x):
                                    s = str(x)
                                    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
                                    if m:
                                        y, mo, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
                                        return f"{y}-{mo}-{d}"
                                    m2 = re.search(r"(\d{4})(\d{2})(\d{2})", s)
                                    if m2:
                                        return f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"
                                    return s
        
                                df_final["as_of"] = df_final["as_of"].apply(_norm_date)
        
                            # Types and ordering
                            df_final["code"] = df_final["code"].astype(str)
                            if "name" in df_final.columns:
                                df_final["name"] = df_final["name"].astype(str)
                            if "sector" in df_final.columns:
                                df_final["sector"] = df_final["sector"].astype(str)
                            if "market" in df_final.columns:
                                df_final["market"] = df_final["market"].astype(str)
        
                            df_final = df_final.drop_duplicates(subset=["code"]).reset_index(drop=True)
        
                            # Summary counts
                            summary = {
                                "timestamp": now_iso,
                                "input_path": selected_path,
                                "input_rows": int(best_df.shape[0]),
                                "final_rows": int(df_final.shape[0]),
                                "columns": list(df_final.columns),
                            }
        
                            # Quality report artifacts
                            import pandas as _pd_local  # ensure pd is available
                            issues_df = _pd_local.DataFrame(issues)
                            report_json_path = os.path.join(output_dir, "prime_2024_quality_report.json")
                            report_csv_path = os.path.join(output_dir, "prime_2024_quality_report.csv")
                            final_csv_path = os.path.join(output_dir, "prime_2024_final_list.csv")
                            final_parquet_path = os.path.join(output_dir, "prime_2024_final_list.parquet")
                            manifest_path = os.path.join(output_dir, "prime_2024_manifest.json")
        
                            # Persist CSV
                            try:
                                df_final.to_csv(final_csv_path, index=False, encoding="utf-8-sig")
                                log_thought("result", f"Saved final CSV: {final_csv_path}")
                                csv_saved = True
                            except Exception as e:
                                log_thought("error", f"CSV save failed: {e}")
                                csv_saved = False
        
                            # Persist Parquet
                            parquet_saved = False
                            parquet_engine = None
                            if pyarrow is None and fastparquet is None:
                                add_issue(None, "parquet_engine_missing", "pyarrow/fastparquet not available; Parquet not saved.", "warning")
                            else:
                                try:
                                    if pyarrow is not None:
                                        df_final.to_parquet(final_parquet_path, engine="pyarrow", index=False)
                                        parquet_engine = "pyarrow"
                                        parquet_saved = True
                                    else:
                                        df_final.to_parquet(final_parquet_path, engine="fastparquet", index=False)
                                        parquet_engine = "fastparquet"
                                        parquet_saved = True
                                    log_thought("result", f"Saved final Parquet using {parquet_engine}: {final_parquet_path}")
                                except Exception as e:
                                    add_issue(None, "parquet_save_failed", f"Parquet save failed: {e}", "error")
                                    parquet_saved = False
        
                            # Persist quality report
                            report_payload = {
                                "summary": summary,
                                "issues": issues,
                            }
                            try:
                                with open(report_json_path, "w", encoding="utf-8") as f:
                                    json.dump(report_payload, f, ensure_ascii=False, indent=2)
                            except Exception as e:
                                log_thought("error", f"Failed to save quality report JSON: {e}")
                            try:
                                if not issues_df.empty:
                                    issues_df.to_csv(report_csv_path, index=False, encoding="utf-8-sig")
                                else:
                                    # create an empty placeholder with headers
                                    _pd_local.DataFrame([{"issue_type": "", "detail": "", "severity": ""}]).head(0).to_csv(report_csv_path, index=False, encoding="utf-8-sig")
                            except Exception as e:
                                log_thought("error", f"Failed to save quality report CSV: {e}")
        
                            # Persist manifest
                            manifest = {
                                "generated_at": now_iso,
                                "input": {
                                    "path": selected_path,
                                    "meta": read_meta
                                },
                                "output": {
                                    "csv": final_csv_path if csv_saved else None,
                                    "parquet": final_parquet_path if parquet_saved else None,
                                    "parquet_engine": parquet_engine,
                                    "quality_report_json": report_json_path,
                                    "quality_report_csv": report_csv_path
                                },
                                "summary": summary,
                                "schema": {
                                    "columns": {c: str(df_final[c].dtype) for c in df_final.columns}
                                }
                            }
                            try:
                                with open(manifest_path, "w", encoding="utf-8") as f:
                                    json.dump(manifest, f, ensure_ascii=False, indent=2)
                            except Exception as e:
                                log_thought("error", f"Failed to save manifest: {e}")
        
                            # Update knowledge DB with outputs
                            try:
                                update_knowledge(task_subject, json.dumps({
                                    "final_list_csv": final_csv_path if csv_saved else None,
                                    "final_list_parquet": final_parquet_path if parquet_saved else None,
                                    "quality_report_json": report_json_path,
                                    "quality_report_csv": report_csv_path,
                                    "manifest": manifest_path,
                                    "rows": int(df_final.shape[0]),
                                }, ensure_ascii=False), 0.9)
                                if parquet_saved:
                                    update_knowledge("parquet_engine_preference", f"Used {parquet_engine} successfully on {now_iso}", 0.7)
                            except Exception as e:
                                log_thought("warning", f"Failed to update knowledge DB: {e}")
        
                            # Hypothesis testing: Expect final row count > 1000 for JP Prime 2024
                            expected_min = 1000
                            hypothesis = f"Final Prime 2024 list should contain at least {expected_min} entries."
                            log_thought("hypothesis", hypothesis)
                            test_passed = int(df_final.shape[0]) >= expected_min
                            log_thought("result", f"Hypothesis {'passed' if test_passed else 'failed'} with {df_final.shape[0]} rows.")
                            try:
                                update_knowledge("prime_2024_rowcount", f"{df_final.shape[0]} rows; hypothesis {'passed' if test_passed else 'failed'}", 0.6)
                            except Exception:
                                pass
        
                            status = "success" if (csv_saved or parquet_saved) else "partial"
                            message = "Final list saved." if (csv_saved or parquet_saved) else "Processing finished but saving failed."
                            result = {
                                "status": status,
                                "message": message,
                                "input_path": selected_path,
                                "final_count": int(df_final.shape[0]),
                                "output": manifest["output"],
                                "summary": summary,
                                "notes": {
                                    "csv_saved": csv_saved,
                                    "parquet_saved": parquet_saved,
                                    "parquet_engine": parquet_engine,
                                }
                            }
                    except Exception as e:
                        err_msg = f"Unhandled error: {e}"
                        try:
                            log_thought("error", err_msg + "\n" + traceback.format_exc())
                        except Exception:
                            pass
                        result = {"status": "failed", "message": err_msg}
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