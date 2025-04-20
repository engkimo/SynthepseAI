import typing
import Dict
import os
import json
import time
import re
import datetime
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple


def get_related_knowledge(keywords, limit=5):
    """
    キーワードに関連する知識を取得

    Args:
        keywords: 検索キーワードのリスト
        limit: 取得する最大件数

    Returns:
        関連知識のリスト
    """
    try:
        knowledge_db = load_knowledge_db()
        related = []

        for subject, data in knowledge_db.items():
            for keyword in keywords:
                if keyword.lower() in subject.lower() or (
                    data.get("fact") and keyword.lower() in data.get("fact", "").lower()
                ):
                    related.append(
                        {
                            "subject": subject,
                            "fact": data.get("fact"),
                            "confidence": data.get("confidence", 0),
                            "last_updated": data.get("last_updated"),
                            "source": data.get("source"),
                        }
                    )
                    break

        related.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return related[:limit]
    except Exception as e:
        print(f"関連知識取得エラー: {str(e)}")
        return []


task_description = ""
insights = []
hypotheses = []
conclusions = []

KNOWLEDGE_DB_PATH = "./workspace/persistent_thinking/knowledge_db.json"
THINKING_LOG_PATH = "./workspace/persistent_thinking/thinking_log.jsonl"


def load_knowledge_db():
    try:
        if os.path.exists(KNOWLEDGE_DB_PATH):
            with open(KNOWLEDGE_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"知識データベース読み込みエラー: {str(e)}")
        return {}


def save_knowledge_db(knowledge_db):
    try:
        os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
        with open(KNOWLEDGE_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(knowledge_db, fp=f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"知識データベース保存エラー: {str(e)}")
        return False


def log_thought(thought_type, content):
    try:
        os.makedirs(os.path.dirname(THINKING_LOG_PATH), exist_ok=True)
        log_entry = {"timestamp": time.time(), "type": thought_type, "content": content}
        with open(THINKING_LOG_PATH, "a", encoding="utf-8") as f:
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
            log_thought(
                "knowledge_update_rejected",
                {
                    "subject": subject,
                    "existing_fact": original_fact,
                    "new_fact": fact,
                    "existing_confidence": existing_confidence,
                    "new_confidence": confidence,
                    "reason": "新しい情報の確信度が既存の情報より低いため更新を拒否",
                },
            )
            return False

        knowledge_db[subject]["fact"] = fact
        knowledge_db[subject]["confidence"] = confidence
        knowledge_db[subject]["last_updated"] = time.time()

        if source:
            knowledge_db[subject]["source"] = source

        save_success = save_knowledge_db(knowledge_db)

        log_thought(
            "knowledge_update",
            {
                "subject": subject,
                "original_fact": original_fact,
                "new_fact": fact,
                "confidence": confidence,
                "source": source,
                "success": save_success,
            },
        )

        return save_success
    except Exception as e:
        print(f"知識更新エラー: {str(e)}")
        return False


def add_insight(insight, confidence=0.7):
    global insights
    insights.append(
        {"content": insight, "confidence": confidence, "timestamp": time.time()}
    )

    log_thought(
        "task_insight",
        {"task": task_description, "insight": insight, "confidence": confidence},
    )


def add_hypothesis(hypothesis, confidence=0.6):
    global hypotheses
    hypotheses.append(
        {
            "content": hypothesis,
            "confidence": confidence,
            "timestamp": time.time(),
            "verified": False,
        }
    )

    log_thought(
        "task_hypothesis",
        {"task": task_description, "hypothesis": hypothesis, "confidence": confidence},
    )


def verify_hypothesis(hypothesis, verified, evidence, confidence=0.7):
    global hypotheses

    for h in hypotheses:
        if h["content"] == hypothesis:
            h["verified"] = verified
            h["evidence"] = evidence
            h["verification_confidence"] = confidence
            h["verification_time"] = time.time()
            break

    log_thought(
        "hypothesis_verification",
        {
            "task": task_description,
            "hypothesis": hypothesis,
            "verified": verified,
            "evidence": evidence,
            "confidence": confidence,
        },
    )

    if verified and confidence > 0.7:
        update_knowledge(
            f"検証済み仮説: {hypothesis[:50]}...",
            f"検証結果: {evidence}",
            confidence,
            "hypothesis_verification",
        )


def verify_hypothesis_with_simulation(hypothesis, simulation_code):
    global task_description

    result = {
        "hypothesis": hypothesis,
        "verified": False,
        "confidence": 0.0,
        "evidence": [],
        "timestamp": time.time(),
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

            log_thought(
                "hypothesis_simulation",
                {
                    "task": task_description,
                    "hypothesis": hypothesis,
                    "verified": result["verified"],
                    "confidence": result["confidence"],
                    "evidence": result["evidence"],
                },
            )

            if result["verified"] and result["confidence"] > 0.7:
                subject = f"検証済み仮説: {hypothesis[:50]}..."
                fact = f"検証結果: {result['simulation_result']}"
                update_knowledge(
                    subject, fact, result["confidence"], "hypothesis_simulation"
                )
        else:
            log_thought(
                "hypothesis_simulation_warning",
                {
                    "task": task_description,
                    "hypothesis": hypothesis,
                    "warning": "シミュレーション結果が取得できませんでした",
                },
            )
    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        log_thought(
            "hypothesis_simulation_error",
            {
                "task": task_description,
                "hypothesis": hypothesis,
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )

    return result


def add_conclusion(conclusion, confidence=0.8):
    global conclusions
    conclusions.append(
        {"content": conclusion, "confidence": confidence, "timestamp": time.time()}
    )

    log_thought(
        "task_conclusion",
        {"task": task_description, "conclusion": conclusion, "confidence": confidence},
    )

    if confidence > 0.7:
        update_knowledge(
            f"タスク結論: {task_description[:50]}...",
            conclusion,
            confidence,
            "task_conclusion",
        )


def request_multi_agent_discussion(topic):
    try:
        log_thought(
            "multi_agent_discussion_request", {"topic": topic, "timestamp": time.time()}
        )

        update_knowledge(
            f"討論リクエスト: {topic[:50]}...",
            f"マルチエージェント討論がリクエストされました: {topic}",
            confidence=0.9,
            source="multi_agent_discussion_request",
        )

        add_insight(f"マルチエージェント討論の結果を待機中: {topic}", confidence=0.8)

        return {"topic": topic, "requested": True, "timestamp": time.time()}
    except Exception as e:
        print(f"マルチエージェント討論リクエストエラー: {str(e)}")
        return {}


def main():
    global task_description, insights, hypotheses, conclusions

    try:
        task_info = globals().get("task_info", {})
        task_description = task_info.get("description", "Unknown task")
        task_start_time = time.time()

        log_thought(
            "task_execution_start",
            {
                "task": task_description,
                "timestamp_readable": datetime.datetime.now().isoformat(),
            },
        )

        keywords = [word for word in task_description.lower().split() if len(word) > 3]

        related_knowledge = []
        try:
            knowledge_db = load_knowledge_db()
            for subject, data in knowledge_db.items():
                for keyword in keywords:
                    if keyword.lower() in subject.lower() or (
                        data.get("fact")
                        and keyword.lower() in data.get("fact", "").lower()
                    ):
                        related_knowledge.append(
                            {
                                "subject": subject,
                                "fact": data.get("fact"),
                                "confidence": data.get("confidence", 0),
                                "last_updated": data.get("last_updated"),
                                "source": data.get("source"),
                            }
                        )
                        break

            error_patterns = []
            thinking_log_path = THINKING_LOG_PATH
            if os.path.exists(thinking_log_path):
                with open(thinking_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get("type") == "task_execution_error":
                                content = entry.get("content", {})
                                error_patterns.append(
                                    {
                                        "error_type": content.get(
                                            "error_type", "unknown"
                                        ),
                                        "error_message": content.get(
                                            "error_message", ""
                                        ),
                                    }
                                )
                        except:
                            continue

            if error_patterns:
                add_insight(
                    f"過去のエラーパターン {len(error_patterns)} 件を分析し、同様のエラーを回避します",
                    confidence=0.8,
                )
                for pattern in error_patterns[-3:]:  # 最新の3つのエラーパターンを考慮
                    add_hypothesis(
                        f"エラー '{pattern['error_type']}' を回避するため、適切な対策が必要",
                        confidence=0.7,
                    )
        except Exception as e:
            print(f"関連知識取得エラー: {str(e)}")

        if related_knowledge:
            print(
                f"タスク '{task_description}' に関連する既存知識が {len(related_knowledge)} 件見つかりました:"
            )
            for i, knowledge in enumerate(related_knowledge):
                print(
                    f"  {i+1}. {knowledge['subject']}: {knowledge['fact']} (確信度: {knowledge['confidence']:.2f})"
                )

            if len(related_knowledge) >= 2:
                hypothesis = f"タスク '{task_description}' は {related_knowledge[0]['subject']} と {related_knowledge[1]['subject']} に関連している可能性がある"
                add_hypothesis(hypothesis, confidence=0.6)

                for i in range(min(len(related_knowledge), 3)):
                    for j in range(i + 1, min(len(related_knowledge), 4)):
                        if i != j:
                            insight = f"{related_knowledge[i]['subject']}と{related_knowledge[j]['subject']}を組み合わせることで、新しい視点が得られるかもしれない"
                            add_insight(insight, confidence=0.65)
        else:
            print(
                f"タスク '{task_description}' に関連する既存知識は見つかりませんでした。"
            )
            add_insight(
                "このタスクに関連する既存知識がないため、新しい知識の獲得が必要"
            )

            discussion_request = request_multi_agent_discussion(
                f"「{task_description}」に関する基礎知識と仮説"
            )
            if discussion_request:
                add_insight(
                    f"複数エージェントによる討論をリクエストしました: {task_description}",
                    confidence=0.8,
                )

        from typing import Dict, List, Tuple, Any, Optional, Union
        import os
        import json
        import time
        import re
        import datetime
        import traceback

        task_info = {
            "task_id": "b237e708-22e6-4e2d-aaea-86591eb0d3f9",
            "description": "Import all necessary libraries for data analysis and visualization",
            "plan_id": "107d79ce-697c-48a0-8a97-f9c5163daed5",
        }

        def get_related_knowledge(keywords, limit=5):
            try:
                knowledge_db = load_knowledge_db()
                related = []

                for subject, data in knowledge_db.items():
                    for keyword in keywords:
                        if keyword.lower() in subject.lower() or (
                            data.get("fact")
                            and keyword.lower() in data.get("fact", "").lower()
                        ):
                            related.append(
                                {
                                    "subject": subject,
                                    "fact": data.get("fact"),
                                    "confidence": data.get("confidence", 0),
                                    "last_updated": data.get("last_updated"),
                                    "source": data.get("source"),
                                }
                            )
                            break

                related.sort(key=lambda x: x.get("confidence", 0), reverse=True)
                return related[:limit]
            except Exception as e:
                print(f"関連知識取得エラー: {str(e)}")
                return []

        task_description = ""
        insights = []
        hypotheses = []
        conclusions = []

        KNOWLEDGE_DB_PATH = "./workspace/persistent_thinking/knowledge_db.json"
        THINKING_LOG_PATH = "./workspace/persistent_thinking/thinking_log.jsonl"

        def load_knowledge_db():
            try:
                if os.path.exists(KNOWLEDGE_DB_PATH):
                    with open(KNOWLEDGE_DB_PATH, "r", encoding="utf-8") as f:
                        return json.load(f)
                return {}
            except Exception as e:
                print(f"知識データベース読み込みエラー: {str(e)}")
                return {}

        def save_knowledge_db(knowledge_db):
            try:
                os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
                with open(KNOWLEDGE_DB_PATH, "w", encoding="utf-8") as f:
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
                    "content": content,
                }
                with open(THINKING_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
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
                    log_thought(
                        "knowledge_update_rejected",
                        {
                            "subject": subject,
                            "existing_fact": original_fact,
                            "new_fact": fact,
                            "existing_confidence": existing_confidence,
                            "new_confidence": confidence,
                            "reason": "新しい情報の確信度が既存の情報より低いため更新を拒否",
                        },
                    )
                    return False

                knowledge_db[subject]["fact"] = fact
                knowledge_db[subject]["confidence"] = confidence
                knowledge_db[subject]["last_updated"] = time.time()

                if source:
                    knowledge_db[subject]["source"] = source

                save_success = save_knowledge_db(knowledge_db)

                log_thought(
                    "knowledge_update",
                    {
                        "subject": subject,
                        "original_fact": original_fact,
                        "new_fact": fact,
                        "confidence": confidence,
                        "source": source,
                        "success": save_success,
                    },
                )

                return save_success
            except Exception as e:
                print(f"知識更新エラー: {str(e)}")
                return False

        def add_insight(insight, confidence=0.7):
            global insights
            insights.append(
                {"content": insight, "confidence": confidence, "timestamp": time.time()}
            )

            log_thought(
                "task_insight",
                {
                    "task": task_description,
                    "insight": insight,
                    "confidence": confidence,
                },
            )

        def add_hypothesis(hypothesis, confidence=0.6):
            global hypotheses
            hypotheses.append(
                {
                    "content": hypothesis,
                    "confidence": confidence,
                    "timestamp": time.time(),
                    "verified": False,
                }
            )

            log_thought(
                "task_hypothesis",
                {
                    "task": task_description,
                    "hypothesis": hypothesis,
                    "confidence": confidence,
                },
            )

        def verify_hypothesis(hypothesis, verified, evidence, confidence=0.7):
            global hypotheses

            for h in hypotheses:
                if h["content"] == hypothesis:
                    h["verified"] = verified
                    h["evidence"] = evidence
                    h["verification_confidence"] = confidence
                    h["verification_time"] = time.time()
                    break

            log_thought(
                "hypothesis_verification",
                {
                    "task": task_description,
                    "hypothesis": hypothesis,
                    "verified": verified,
                    "evidence": evidence,
                    "confidence": confidence,
                },
            )

            if verified and confidence > 0.7:
                update_knowledge(
                    f"検証済み仮説: {hypothesis[:50]}...",
                    f"検証結果: {evidence}",
                    confidence,
                    "hypothesis_verification",
                )

        def verify_hypothesis_with_simulation(hypothesis, simulation_code):
            global task_description

            result = {
                "hypothesis": hypothesis,
                "verified": False,
                "confidence": 0.0,
                "evidence": [],
                "timestamp": time.time(),
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

                    log_thought(
                        "hypothesis_simulation",
                        {
                            "task": task_description,
                            "hypothesis": hypothesis,
                            "verified": result["verified"],
                            "confidence": result["confidence"],
                            "evidence": result["evidence"],
                        },
                    )

                    if result["verified"] and result["confidence"] > 0.7:
                        subject = f"検証済み仮説: {hypothesis[:50]}..."
                        fact = f"検証結果: {result['simulation_result']}"
                        update_knowledge(
                            subject, fact, result["confidence"], "hypothesis_simulation"
                        )
                else:
                    log_thought(
                        "hypothesis_simulation_warning",
                        {
                            "task": task_description,
                            "hypothesis": hypothesis,
                            "warning": "シミュレーション結果が取得できませんでした",
                        },
                    )
            except Exception as e:
                result["error"] = str(e)
                result["traceback"] = traceback.format_exc()
                log_thought(
                    "hypothesis_simulation_error",
                    {
                        "task": task_description,
                        "hypothesis": hypothesis,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    },
                )

            return result

        def add_conclusion(conclusion, confidence=0.8):
            global conclusions
            conclusions.append(
                {
                    "content": conclusion,
                    "confidence": confidence,
                    "timestamp": time.time(),
                }
            )

            log_thought(
                "task_conclusion",
                {
                    "task": task_description,
                    "conclusion": conclusion,
                    "confidence": confidence,
                },
            )

            if confidence > 0.7:
                update_knowledge(
                    f"タスク結論: {task_description[:50]}...",
                    conclusion,
                    confidence,
                    "task_conclusion",
                )

        def request_multi_agent_discussion(topic):
            try:
                log_thought(
                    "multi_agent_discussion_request",
                    {"topic": topic, "timestamp": time.time()},
                )

                update_knowledge(
                    f"討論リクエスト: {topic[:50]}...",
                    f"マルチエージェント討論がリクエストされました: {topic}",
                    confidence=0.9,
                    source="multi_agent_discussion_request",
                )

                add_insight(
                    f"マルチエージェント討論の結果を待機中: {topic}", confidence=0.8
                )

                return {"topic": topic, "requested": True, "timestamp": time.time()}
            except Exception as e:
                print(f"マルチエージェント討論リクエストエラー: {str(e)}")
                return {}

        def main():
            global task_description, insights, hypotheses, conclusions

            try:
                task_info = globals().get("task_info", {})
                task_description = task_info.get("description", "Unknown task")
                task_start_time = time.time()

                log_thought(
                    "task_execution_start",
                    {
                        "task": task_description,
                        "timestamp_readable": datetime.datetime.now().isoformat(),
                    },
                )

                keywords = [
                    word for word in task_description.lower().split() if len(word) > 3
                ]

                related_knowledge = []
                try:
                    knowledge_db = load_knowledge_db()
                    for subject, data in knowledge_db.items():
                        for keyword in keywords:
                            if keyword.lower() in subject.lower() or (
                                data.get("fact")
                                and keyword.lower() in data.get("fact", "").lower()
                            ):
                                related_knowledge.append(
                                    {
                                        "subject": subject,
                                        "fact": data.get("fact"),
                                        "confidence": data.get("confidence", 0),
                                        "last_updated": data.get("last_updated"),
                                        "source": data.get("source"),
                                    }
                                )
                                break

                    error_patterns = []
                    thinking_log_path = THINKING_LOG_PATH
                    if os.path.exists(thinking_log_path):
                        with open(thinking_log_path, "r", encoding="utf-8") as f:
                            for line in f:
                                try:
                                    entry = json.loads(line.strip())
                                    if entry.get("type") == "task_execution_error":
                                        content = entry.get("content", {})
                                        error_patterns.append(
                                            {
                                                "error_type": content.get(
                                                    "error_type", "unknown"
                                                ),
                                                "error_message": content.get(
                                                    "error_message", ""
                                                ),
                                            }
                                        )
                                except:
                                    continue

                    if error_patterns:
                        add_insight(
                            f"過去のエラーパターン {len(error_patterns)} 件を分析し、同様のエラーを回避します",
                            confidence=0.8,
                        )
                        for pattern in error_patterns[-3:]:
                            add_hypothesis(
                                f"エラー '{pattern['error_type']}' を回避するため、適切な対策が必要",
                                confidence=0.7,
                            )
                except Exception as e:
                    print(f"関連知識取得エラー: {str(e)}")

                if related_knowledge:
                    print(
                        f"タスク '{task_description}' に関連する既存知識が {len(related_knowledge)} 件見つかりました:"
                    )
                    for i, knowledge in enumerate(related_knowledge):
                        print(
                            f"  {i+1}. {knowledge['subject']}: {knowledge['fact']} (確信度: {knowledge['confidence']:.2f})"
                        )

                    if len(related_knowledge) >= 2:
                        hypothesis = f"タスク '{task_description}' は {related_knowledge[0]['subject']} と {related_knowledge[1]['subject']} に関連している可能性がある"
                        add_hypothesis(hypothesis, confidence=0.6)

                        for i in range(min(len(related_knowledge), 3)):
                            for j in range(i + 1, min(len(related_knowledge), 4)):
                                if i != j:
                                    insight = f"{related_knowledge[i]['subject']}と{related_knowledge[j]['subject']}を組み合わせることで、新しい視点が得られるかもしれない"
                                    add_insight(insight, confidence=0.65)
                else:
                    print(
                        f"タスク '{task_description}' に関連する既存知識は見つかりませんでした。"
                    )
                    add_insight(
                        "このタスクに関連する既存知識がないため、新しい知識の獲得が必要"
                    )

                    discussion_request = request_multi_agent_discussion(
                        f"「{task_description}」に関する基礎知識と仮説"
                    )
                    if discussion_request:
                        add_insight(
                            f"複数エージェントによる討論をリクエストしました: {task_description}",
                            confidence=0.8,
                        )

                log_thought(
                    "task_execution_complete",
                    {
                        "task": task_description,
                        "execution_time": time.time() - task_start_time,
                        "insights_count": len(insights),
                        "hypotheses_count": len(hypotheses),
                        "conclusions_count": len(conclusions),
                    },
                )

                return "Task completed successfully"

            except ImportError as e:
                missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
                error_msg = f"エラー: 必要なモジュール '{missing_module}' がインストールされていません。"
                print(error_msg)
                print(
                    f"次のコマンドでインストールしてください: pip install {missing_module}"
                )

                try:
                    log_thought(
                        "task_execution_error",
                        {
                            "task": task_description,
                            "error_type": "ImportError",
                            "error_message": error_msg,
                        },
                    )
                except:
                    pass

                return error_msg

            except Exception as e:
                error_details = traceback.format_exc()
                error_msg = f"エラー: {str(e)}"
                print(error_msg)
                print(error_details)

                try:
                    log_thought(
                        "task_execution_error",
                        {
                            "task": task_description,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "traceback": error_details,
                        },
                    )

                    update_knowledge(
                        f"エラーパターン: {type(e).__name__}",
                        f"タスク実行中に発生: {str(e)}",
                        confidence=0.7,
                    )
                except:
                    pass

                return error_msg

        if __name__ == "__main__":
            result = main()

        log_thought(
            "task_execution_complete",
            {
                "task": task_description,
                "execution_time": time.time() - task_start_time,
                "insights_count": len(insights),
                "hypotheses_count": len(hypotheses),
                "conclusions_count": len(conclusions),
            },
        )

        return result if "result" in locals() else "Task completed successfully"

    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        error_msg = f"エラー: 必要なモジュール '{missing_module}' がインストールされていません。"
        print(error_msg)
        print(f"次のコマンドでインストールしてください: pip install {missing_module}")

        try:
            log_thought(
                "task_execution_error",
                {
                    "task": task_description,
                    "error_type": "ImportError",
                    "error_message": error_msg,
                },
            )
        except:
            pass

        return error_msg

    except Exception as e:
        error_details = traceback.format_exc()
        error_msg = f"エラー: {str(e)}"
        print(error_msg)
        print(error_details)

        try:
            log_thought(
                "task_execution_error",
                {
                    "task": task_description,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": error_details,
                },
            )

            update_knowledge(
                f"エラーパターン: {type(e).__name__}",
                f"タスク実行中に発生: {str(e)}",
                confidence=0.7,
            )
        except:
            pass

        return error_msg


if __name__ == "__main__":
    result = main()
