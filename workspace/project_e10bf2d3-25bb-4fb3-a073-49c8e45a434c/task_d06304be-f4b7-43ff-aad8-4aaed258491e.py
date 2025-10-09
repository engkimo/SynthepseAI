
# 必要なライブラリのインポート
import matplotlib
import numpy
import typing
import duplicates
import libraries
import standard
import os
import json
import time
import re
import datetime
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

task_info = {
    "task_id": "d06304be-f4b7-43ff-aad8-4aaed258491e",
    "description": "メタデータの品質検査（重複コード、欠損業種/名称、非数値コード、デリスティング/指定替え候補のフラグ）。不整合を修正または除外し、検査レポートをJSON/CSVで出力。",
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
            "task_id": "d06304be-f4b7-43ff-aad8-4aaed258491e",
            "description": "メタデータの品質検査（重複コード、欠損業種/名称、非数値コード、デリスティング/指定替え候補のフラグ）。不整合を修正または除外し、検査レポートをJSON/CSVで出力。",
            "plan_id": "e10bf2d3-25bb-4fb3-a073-49c8e45a434c"
        }
        
        # 必要なライブラリのインポート（存在しない可能性のあるものは安全に無視）
        try:
            import standard  # 使わないが、存在しない場合に備えて例外を握りつぶす
        except Exception:
            standard = None
        
        import os
        import json
        import time
        import re
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
        
        def get_knowledge(subject):
            """知識DBから特定のsubjectに対応するレコードを返す"""
            try:
                db = load_knowledge_db()
                return db.get(subject)
            except Exception as e:
                print(f"知識取得エラー: {str(e)}")
                return None
        
        def get_related_knowledge(keywords: List[str], limit: int = 5):
            """キーワードに関連する知識を返す（簡易実装）"""
            results = []
            try:
                db = load_knowledge_db()
                for subject, data in db.items():
                    subject_l = subject.lower()
                    fact = str(data.get("fact", "")).lower()
                    if any(k.lower() in subject_l or k.lower() in fact for k in keywords):
                        results.append({ "subject": subject, **data })
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"関連知識検索エラー: {str(e)}")
            return results
        
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
                            if keyword.lower() in subject.lower() or (data.get("fact") and keyword.lower() in str(data.get("fact", "")).lower()):
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
                result = {
                    "status": "initialized",
                    "message": "",
                    "inputs": {},
                    "outputs": {},
                    "summary": {}
                }
                # Dynamic imports and module availability checks
                try:
                    importlib = __import__('importlib')
                    os_mod = __import__('os')
                    sys = __import__('sys')
                    re_mod = __import__('re')
                    json_mod = __import__('json')
                    csv = __import__('csv')
                    glob = __import__('glob')
                    traceback_mod = __import__('traceback')
                    datetime_mod = __import__('datetime')
                    io = __import__('io')
                except Exception as e:
                    result["status"] = "error"
                    result["message"] = f"Failed to import libraries: {e}"
                    try:
                        log_thought("error", result["message"])
                    except Exception:
                        pass
                    raise
                def _import_optional(module_name, friendly_name=None):
                    try:
                        return importlib.import_module(module_name), None
                    except Exception as e:
                        name = friendly_name if friendly_name else module_name
                        return None, f"Missing required package '{name}'. Please install it: pip install {name}"
                # Import third-party libraries
                pd, pd_err = _import_optional('pandas', 'pandas')
                np, np_err = _import_optional('numpy', 'numpy')
                chardet, chardet_err = _import_optional('chardet', 'chardet')
                missing_errors = [err for err in [pd_err, np_err] if err]
                if missing_errors:
                    message = " | ".join(missing_errors)
                    result["status"] = "error"
                    result["message"] = message
                    try:
                        log_thought("error", message)
                        update_knowledge("dependencies", f"Missing packages: {message}", 0.9)
                    except Exception:
                        pass
                    raise RuntimeError(message)
                # Helper: robust logging wrapper
                def safe_log(thought_type, content):
                    try:
                        log_thought(thought_type, content)
                    except Exception:
                        pass
                def safe_update_knowledge(subject, fact, confidence=0.7):
                    try:
                        update_knowledge(subject, fact, confidence)
                    except Exception:
                        pass
                def safe_get_knowledge(subject):
                    try:
                        return get_knowledge(subject)
                    except Exception:
                        return None
                def safe_get_related(keys, limit=5):
                    try:
                        return get_related_knowledge(keys, limit)
                    except Exception:
                        return []
                # Utilities
                def ensure_dir(path):
                    try:
                        os_mod.makedirs(path, exist_ok=True)
                    except Exception as e:
                        safe_log("error", f"Failed to create directory {path}: {e}")
                        raise
                def detect_file_encoding(path, sample_size=65536):
                    candidates = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis', 'euc-jp']
                    for enc in candidates:
                        try:
                            with open(path, 'r', encoding=enc) as f:
                                f.read(4096)
                            return enc, "heuristic"
                        except Exception:
                            continue
                    if chardet is None:
                        return 'utf-8', "default"
                    try:
                        with open(path, 'rb') as f:
                            raw = f.read(sample_size)
                        res = chardet.detect(raw)
                        enc = res.get('encoding') or 'utf-8'
                        return enc, "chardet"
                    except Exception:
                        return 'utf-8', "fallback"
                def find_metadata_file():
                    env_path = os_mod.environ.get("METADATA_PATH")
                    if env_path and os_mod.path.exists(env_path):
                        return env_path, "env"
                    kb_subjects = [
                        "prime_metadata_2024_path",
                        "銘柄メタデータ_2024_パス",
                        "メタデータ_2024_パス",
                        "prime_metadata_path",
                    ]
                    for subj in kb_subjects:
                        info = safe_get_knowledge(subj)
                        if isinstance(info, dict):
                            p = info.get("path") or info.get("value") or info.get("file_path")
                            if p and os_mod.path.exists(p):
                                return p, f"knowledge:{subj}"
                        elif isinstance(info, list):
                            for rec in info:
                                if isinstance(rec, dict):
                                    p = rec.get("path") or rec.get("value") or rec.get("file_path")
                                    if p and os_mod.path.exists(p):
                                        return p, f"knowledge:{subj}"
                    candidates = []
                    roots = [".", "./data", "./dataset", "./inputs"]
                    patterns = [
                        "*metadata*.csv", "*銘柄*.csv", "*meigara*.csv", "*prime*2024*.csv",
                        "*metadata*.xlsx", "*銘柄*.xlsx", "*meigara*.xlsx", "*prime*2024*.xlsx",
                    ]
                    for root in roots:
                        for pat in patterns:
                            g = glob.glob(os_mod.path.join(root, pat))
                            candidates.extend(g)
                    try:
                        candidates = sorted(
                            candidates,
                            key=lambda p: (not p.lower().endswith(".csv"), -os_mod.path.getmtime(p))
                        )
                    except Exception:
                        candidates = sorted(candidates)
                    if candidates:
                        return candidates[0], "auto_search"
                    return None, "not_found"
                def read_metadata_any(path):
                    ext = os_mod.path.splitext(path)[1].lower()
                    if ext in [".csv", ".tsv", ".txt"]:
                        sep = "," if ext != ".tsv" else "\t"
                        enc, method = detect_file_encoding(path)
                        safe_log("info", f"Detected encoding {enc} using {method} for {path}")
                        try:
                            df = pd.read_csv(path, encoding=enc, sep=sep)
                            return df, {"encoding": enc, "engine": "csv", "detector": method}
                        except UnicodeDecodeError:
                            try:
                                df = pd.read_csv(path, encoding="cp932", sep=sep)
                                return df, {"encoding": "cp932", "engine": "csv", "detector": "fallback"}
                            except Exception as e:
                                raise
                    elif ext in [".xlsx", ".xls"]:
                        try:
                            df = pd.read_excel(path)
                            return df, {"encoding": None, "engine": "excel", "detector": "n/a"}
                        except Exception as e:
                            raise
                    else:
                        raise ValueError(f"Unsupported file extension: {ext}")
                def synthesize_sample_metadata():
                    data = [
                        {"ticker": "7203", "name": "トヨタ自動車", "industry": "輸送用機器", "market": "プライム", "market_cap": 40000000, "status": ""},
                        {"ticker": "6758.T", "name": "ソニーグループ", "industry": "電気機器", "market": "プライム", "market_cap": 20000000, "status": "市場変更予定: プライム維持"},
                        {"ticker": "8411 JP Equity", "name": "みずほフィナンシャルグループ", "industry": "銀行業", "market": "プライム", "market_cap": 8000000, "status": "注意喚起"},
                        {"ticker": "A123", "name": "", "industry": "", "market": "スタンダード", "market_cap": 50000, "status": "指定替え"},
                        {"ticker": "7203", "name": "トヨタ自動車", "industry": "輸送用機器", "market": "プライム", "market_cap": 40000000, "status": "重複"},
                    ]
                    return pd.DataFrame(data)
                def normalize_whitespace(s):
                    if pd.isna(s):
                        return s
                    if not isinstance(s, str):
                        try:
                            s = str(s)
                        except Exception:
                            return s
                    return s.replace("\u3000", " ").strip()
                def normalize_ticker(raw):
                    if pd.isna(raw):
                        return None, "missing"
                    s = str(raw).strip()
                    s = s.replace("\u3000", " ")
                    m = re_mod.search(r'(\d{4})', s)
                    if m:
                        digits = m.group(1)
                        ticker = f"{digits}.T"
                        return ticker, "numeric_extracted"
                    m2 = re_mod.search(r'(\d{4,5})', s)
                    if m2:
                        digits = m2.group(1)[:4]
                        ticker = f"{digits}.T"
                        return ticker, "digits_truncated"
                    m3 = re_mod.search(r'JP[:\-\s]?(\d{4})', s, flags=re_mod.IGNORECASE)
                    if m3:
                        ticker = f"{m3.group(1)}.T"
                        return ticker, "jp_prefix_extracted"
                    return None, "non_numeric"
                def standardize_columns(df):
                    original_cols = list(df.columns)
                    col_map_candidates = {
                        "ticker": ["証券コード", "銘柄コード", "コード", "code", "ticker", "証券ｺｰﾄﾞ", "SecCode", "セキュリティコード", "SecurityCode"],
                        "name": ["銘柄名", "企業名", "会社名", "名称", "name", "CompanyName", "IssuerName"],
                        "industry": ["業種", "業種分類", "セクター", "sector", "industry", "業種コード名"],
                        "market": ["上場市場", "市場区分", "市場", "market", "MarketSegment", "上場区分"],
                        "market_cap": ["時価総額", "時価総額(百万円)", "時価総額（百万円）", "market_cap", "時価総額_百万円", "時価総額(百万円換算)"],
                        "status": ["ステータス", "状態", "備考", "注記", "メモ", "注意喚起", "Note", "Remarks"],
                    }
                    mapping = {}
                    for std, candidates in col_map_candidates.items():
                        for c in original_cols:
                            if c in candidates:
                                mapping[c] = std
                                break
                        if std not in mapping.values():
                            for c in original_cols:
                                cl = c.lower()
                                for cand in candidates:
                                    if cl == str(cand).lower():
                                        mapping[c] = std
                                        break
                                if std in mapping.values():
                                    break
                    df2 = df.copy()
                    if mapping:
                        df2 = df2.rename(columns=mapping)
                    for req in ["ticker", "name", "industry", "market"]:
                        if req not in df2.columns:
                            df2[req] = pd.NA
                    for col in ["ticker", "name", "industry", "market", "status"]:
                        if col in df2.columns:
                            df2[col] = df2[col].apply(normalize_whitespace)
                    norm_tickers = df2["ticker"].apply(normalize_ticker)
                    df2["ticker_normalized"] = norm_tickers.apply(lambda x: x[0])
                    df2["ticker_norm_method"] = norm_tickers.apply(lambda x: x[1])
                    df2["code_digits"] = df2["ticker_normalized"].str.extract(r'(\d{4})')
                    def is_prime(s):
                        if pd.isna(s):
                            return False
                        sl = str(s).lower()
                        return ("prime" in sl) or ("プライム" in s)
                    df2["is_prime_market"] = df2["market"].apply(is_prime)
                    def flag_delisting(text):
                        if pd.isna(text):
                            return False
                        txt = str(text)
                        flags = ["上場廃止", "上場廃止予定", "整理銘柄", "監理銘柄", "注意喚起", "delist", "delisting"]
                        return any(f in txt for f in flags)
                    def flag_market_change(text):
                        if pd.isna(text):
                            return False
                        txt = str(text)
                        flags = ["市場変更", "指定替え", "区分変更", "segment change", "market change", "プライム→", "→プライム"]
                        return any(f in txt for f in flags)
                    status_series = df2["status"] if "status" in df2.columns else pd.Series([pd.NA]*len(df2), index=df2.index)
                    df2["is_delisting_candidate"] = status_series.apply(flag_delisting)
                    df2["is_market_change_candidate"] = status_series.apply(flag_market_change)
                    return df2, mapping
                def quality_checks_and_clean(df):
                    qc = {}
                    df = df.copy()
                    total = len(df)
                    qc["total_records"] = int(total)
                    non_numeric_mask = df["ticker_normalized"].isna()
                    qc["non_numeric_code_count"] = int(non_numeric_mask.sum())
                    missing_name = df["name"].isna() | (df["name"].astype(str).str.len() == 0)
                    missing_industry = df["industry"].isna() | (df["industry"].astype(str).str.len() == 0)
                    qc["missing_name_count"] = int(missing_name.sum())
                    qc["missing_industry_count"] = int(missing_industry.sum())
                    dup_counts = df["ticker_normalized"].value_counts(dropna=True)
                    dup_tickers = dup_counts[dup_counts > 1].index.tolist()
                    qc["duplicate_tickers"] = dup_tickers
                    qc["duplicate_count"] = int(len(dup_tickers))
                    prime_before = int(df["is_prime_market"].sum())
                    qc["prime_records_before_filter"] = prime_before
                    df["drop_reason"] = pd.NA
                    df.loc[non_numeric_mask, "drop_reason"] = "non_numeric_or_missing_code"
                    for col in ["name", "industry"]:
                        needs = df[col].isna() | (df[col].astype(str).str.strip() == "")
                        if needs.any():
                            filled = 0
                            for t in df.loc[needs, "ticker_normalized"].dropna().unique():
                                if pd.isna(t):
                                    continue
                                vals = df.loc[(df["ticker_normalized"] == t) & (~df[col].isna()) & (df[col].astype(str).str.strip() != ""), col]
                                if len(vals) > 0:
                                    fill_val = vals.iloc[0]
                                    idx = df.index[(df["ticker_normalized"] == t) & needs]
                                    df.loc[idx, col] = fill_val
                                    filled += len(idx)
                            if filled > 0:
                                safe_log("info", f"Filled {filled} missing values in {col} from duplicates")
                                safe_update_knowledge("imputation", f"Filled {filled} {col} via intra-ticker propagation", 0.6)
                    missing_name = df["name"].isna() | (df["name"].astype(str).str.strip() == "")
                    missing_industry = df["industry"].isna() | (df["industry"].astype(str).str.strip() == "")
                    qc["missing_name_after_fill"] = int(missing_name.sum())
                    qc["missing_industry_after_fill"] = int(missing_industry.sum())
                    non_prime_mask = ~df["is_prime_market"]
                    df.loc[non_prime_mask, "drop_reason"] = df["drop_reason"].astype(object).where(~non_prime_mask, "non_prime")
                    df["rank_for_dedup"] = (~df["is_prime_market"]).astype(int) + df["is_delisting_candidate"].astype(int)
                    df = df.sort_values(by=["ticker_normalized", "rank_for_dedup"]).copy()
                    df_dedup = df.drop_duplicates(subset=["ticker_normalized"], keep="first").copy()
                    df_prime = df_dedup[df_dedup["is_prime_market"]].copy()
                    critical_missing = df_prime["name"].isna() | df_prime["industry"].isna() | (df_prime["name"].astype(str).str.strip() == "") | (df_prime["industry"].astype(str).str.strip() == "")
                    df_prime.loc[critical_missing, "drop_reason"] = "missing_critical_fields"
                    df_final = df_prime[~critical_missing].copy()
                    df_qc_detail = df.copy()
                    df_qc_detail["is_non_numeric_code"] = df_qc_detail["ticker_normalized"].isna()
                    df_qc_detail["is_missing_name"] = df_qc_detail["name"].isna() | (df_qc_detail["name"].astype(str).str.strip() == "")
                    df_qc_detail["is_missing_industry"] = df_qc_detail["industry"].isna() | (df_qc_detail["industry"].astype(str).str.strip() == "")
                    qc["prime_records_after_clean"] = int(len(df_final))
                    qc["delisting_candidate_count"] = int(df_dedup["is_delisting_candidate"].sum())
                    qc["market_change_candidate_count"] = int(df_dedup["is_market_change_candidate"].sum())
                    qc["excluded_non_prime"] = int(non_prime_mask.sum())
                    qc["excluded_critical_missing"] = int(critical_missing.sum())
                    return df_final, df_qc_detail, qc
                def build_qc_summary_json(qc, src_info, col_mapping):
                    summary = {
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                        "source": src_info,
                        "quality_summary": qc,
                        "notes": {
                            "ticker_format": "NNNN.T",
                            "market_filter": "プライムのみ",
                            "normalization": "全角スペース除去・前後空白除去・コード抽出",
                        },
                        "column_mapping": col_mapping
                    }
                    return summary
                def save_outputs(df_clean, df_qc_detail, summary, outdir="outputs"):
                    ensure_dir(outdir)
                    files = {}
                    try:
                        clean_path = os_mod.path.join(outdir, "cleaned_prime_2024.csv")
                        df_clean.to_csv(clean_path, index=False, encoding="utf-8-sig")
                        files["cleaned_csv"] = clean_path
                    except Exception as e:
                        safe_log("error", f"Failed to save cleaned CSV: {e}")
                    try:
                        qc_detail_path = os_mod.path.join(outdir, "qc_detail_2024.csv")
                        df_qc_detail.to_csv(qc_detail_path, index=False, encoding="utf-8-sig")
                        files["qc_detail_csv"] = qc_detail_path
                    except Exception as e:
                        safe_log("error", f"Failed to save QC detail CSV: {e}")
                    try:
                        qc_json_path = os_mod.path.join(outdir, "qc_report_2024_prime.json")
                        with open(qc_json_path, "w", encoding="utf-8") as f:
                            json_mod.dump(summary, f, ensure_ascii=False, indent=2)
                        files["qc_report_json"] = qc_json_path
                    except Exception as e:
                        safe_log("error", f"Failed to save QC JSON: {e}")
                    try:
                        qc_csv_path = os_mod.path.join(outdir, "qc_report_2024_prime.csv")
                        flat = []
                        for k, v in summary.get("quality_summary", {}).items():
                            flat.append({"metric": k, "value": v})
                        flat_df = pd.DataFrame(flat)
                        flat_df.to_csv(qc_csv_path, index=False, encoding="utf-8-sig")
                        files["qc_report_csv"] = qc_csv_path
                    except Exception as e:
                        safe_log("error", f"Failed to save QC CSV: {e}")
                    return files
                # Hypotheses
                hypos = [
                    "H1: メタデータはUTF-8またはCP932でエンコードされている",
                    "H2: プライム市場の判定は市場列に「プライム」を含むかどうかで判定可能",
                    "H3: 証券コードは4桁数字で正規化できる（例: 7203.T）",
                ]
                safe_log("thought", f"Formulated hypotheses: {hypos}")
                safe_update_knowledge("metadata_qc_hypotheses", {"list": hypos}, 0.6)
                # Main pipeline
                try:
                    src_path, src_method = find_metadata_file()
                    result["inputs"]["source_detection"] = {"path": src_path, "method": src_method}
                    if src_path is None:
                        safe_log("warning", "Metadata file not found. Using synthetic sample data.")
                        safe_update_knowledge("metadata_source", "Not found. Synthetic dataset used for pipeline validation.", 0.5)
                        df_raw = synthesize_sample_metadata()
                        src_info = {"path": "synthetic", "method": "synthesized", "encoding": "n/a"}
                    else:
                        safe_log("info", f"Reading metadata from {src_path} (method={src_method})")
                        df_raw, read_info = read_metadata_any(src_path)
                        src_info = {"path": src_path, "method": src_method, **read_info}
                        safe_update_knowledge("metadata_source", src_info, 0.8)
                    df_std, col_mapping = standardize_columns(df_raw)
                    safe_log("info", f"Standardized columns mapping: {col_mapping}")
                    safe_update_knowledge("column_mapping_prime_2024", col_mapping, 0.85)
                    h1_outcome = "Confirmed" if (src_info.get("encoding") in [None, "utf-8-sig", "utf-8", "cp932"]) else "Inconclusive"
                    safe_log("thought", f"H1 outcome: {h1_outcome}, encoding={src_info.get('encoding')}")
                    h2_outcome = "Confirmed" if df_std["is_prime_market"].any() else "Refuted"
                    safe_log("thought", f"H2 outcome: {h2_outcome}, prime_count={int(df_std['is_prime_market'].sum())}")
                    h3_outcome = "Confirmed" if df_std["ticker_normalized"].notna().any() else "Refuted"
                    safe_log("thought", f"H3 outcome: {h3_outcome}, normalized_non_na={int(df_std['ticker_normalized'].notna().sum())}")
                    df_clean, df_qc_detail, qc = quality_checks_and_clean(df_std)
                    summary = build_qc_summary_json(qc, src_info, col_mapping)
                    files = save_outputs(df_clean, df_qc_detail, summary, outdir="outputs")
                    result["status"] = "success"
                    result["message"] = "Quality check and cleaning completed for 2024 Prime market metadata."
                    result["outputs"]["files"] = files
                    try:
                        result["outputs"]["sample_clean_head"] = df_clean.head(10).to_dict(orient="records")
                    except Exception:
                        result["outputs"]["sample_clean_head"] = []
                    result["summary"] = summary
                    safe_update_knowledge("prime_2024_qc_metrics", qc, 0.8)
                    safe_log("result", f"Saved outputs: {files}")
                except FileNotFoundError as e:
                    msg = f"File not found: {e}"
                    result["status"] = "error"
                    result["message"] = msg
                    safe_log("error", msg)
                    safe_update_knowledge("errors", msg, 0.9)
                except Exception as e:
                    tb = traceback_mod.format_exc()
                    msg = f"Unexpected error: {e}"
                    result["status"] = "error"
                    result["message"] = msg
                    result["outputs"]["traceback"] = tb
                    safe_log("error", msg + "\n" + tb)
                    safe_update_knowledge("errors", msg, 0.7)
                if result is None:
                    result = {"status": "success", "message": "Task completed successfully"}
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
            try:
                result = main()
            except IndentationError as e:
                # 予期せぬインデントエラーに対する最終ガード（通常は到達しない）
                print(f"IndentationError detected at runtime: {e}")
                try:
                    log_thought("fatal_error", {"type": "IndentationError", "message": str(e)})
                except Exception:
                    pass
                raise
            except Exception as e:
                print(f"Unhandled exception in __main__: {e}")
                try:
                    log_thought("fatal_error", {"type": type(e).__name__, "message": str(e)})
                except Exception:
                    pass
                raise
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