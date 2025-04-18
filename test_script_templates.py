import os
import sys
import json
import time
import datetime
from core.script_templates import get_template_for_task

global task_description, insights, hypotheses, conclusions
task_description = "テストタスク：データ分析と仮説検証"
insights = []
hypotheses = []
conclusions = []

def load_knowledge_db():
    """知識データベースを読み込む"""
    try:
        knowledge_db_path = "./workspace/persistent_thinking/knowledge_db.json"
        if os.path.exists(knowledge_db_path):
            with open(knowledge_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"知識データベース読み込みエラー: {str(e)}")
        return {}

def save_knowledge_db(knowledge_db):
    """知識データベースを保存する"""
    try:
        knowledge_db_path = "./workspace/persistent_thinking/knowledge_db.json"
        os.makedirs(os.path.dirname(knowledge_db_path), exist_ok=True)
        
        with open(knowledge_db_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_db, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"知識データベース保存エラー: {str(e)}")
        return False

def log_thought(thought_type, content):
    """思考ログに記録する"""
    try:
        log_path = "./workspace/persistent_thinking/thinking_log.jsonl"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        log_entry = {
            "timestamp": time.time(),
            "type": thought_type,
            "content": content
        }
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"思考ログ記録エラー: {str(e)}")
        return False

def update_knowledge(subject, fact, confidence=0.8, source=None):
    """知識を更新する"""
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

def verify_hypothesis(hypothesis, verified, evidence, confidence=0.7):
    """仮説の検証結果を記録"""
    global hypotheses, task_description
    
    found = False
    for h in hypotheses:
        if h["content"] == hypothesis:
            found = True
            h["verified"] = verified
            h["evidence"] = evidence
            h["verification_confidence"] = confidence
            h["verification_time"] = time.time()
            break
    
    if not found:
        hypotheses.append({
            "content": hypothesis,
            "verified": verified,
            "evidence": evidence,
            "verification_confidence": confidence,
            "verification_time": time.time()
        })
    
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
    """仮説をシミュレーションで検証する"""
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
        import traceback
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        log_thought("hypothesis_simulation_error", {
            "task": task_description,
            "hypothesis": hypothesis,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        
    return result

def request_multi_agent_discussion(topic):
    """マルチエージェント討論を要求する"""
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

test_dir = "./test_workspace"
os.makedirs(test_dir, exist_ok=True)
os.makedirs(f"{test_dir}/persistent_thinking", exist_ok=True)


def test_knowledge_db():
    print("\n=== テスト1: 知識DBの更新と読み込み ===")
    
    update_result = update_knowledge(
        subject="テスト主題",
        fact="これはテスト用の事実です",
        confidence=0.85,
        source="テストスクリプト"
    )
    
    print(f"知識更新結果: {update_result}")
    
    knowledge_db = load_knowledge_db()
    print(f"知識DB内のエントリ数: {len(knowledge_db)}")
    
    if "テスト主題" in knowledge_db:
        print(f"テスト主題の内容: {knowledge_db['テスト主題']}")
    else:
        print("エラー: テスト主題が知識DBに見つかりません")
    
    return update_result and "テスト主題" in knowledge_db

def test_thinking_log():
    print("\n=== テスト2: 思考ログの記録 ===")
    
    log_result = log_thought("test_thought", {
        "task": task_description,
        "content": "これはテスト用の思考です",
        "test_value": 123
    })
    
    print(f"思考ログ記録結果: {log_result}")
    
    log_path = "./workspace/persistent_thinking/thinking_log.jsonl"
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"思考ログのエントリ数: {len(lines)}")
            if lines:
                last_entry = json.loads(lines[-1])
                print(f"最新のログエントリ: {last_entry}")
    else:
        print(f"警告: 思考ログファイルが見つかりません: {log_path}")
    
    return log_result

def test_hypothesis_verification():
    print("\n=== テスト3: 仮説検証 ===")
    
    hypothesis = "これはテスト用の仮説です"
    
    verify_hypothesis(
        hypothesis=hypothesis,
        verified=True,
        evidence="テストによる検証",
        confidence=0.9
    )
    
    for h in hypotheses:
        if h["content"] == hypothesis:
            print(f"仮説検証結果: {h}")
            return h["verified"] == True
    
    print("エラー: 仮説が見つかりません")
    return False

def test_hypothesis_simulation():
    print("\n=== テスト4: シミュレーションによる仮説検証 ===")
    
    hypothesis = "データセットの平均値は5より大きい"
    
    simulation_code = """
import numpy as np

data = np.random.normal(loc=7, scale=2, size=100)

mean_value = data.mean()
verified = mean_value > 5
confidence = 0.9 if abs(mean_value - 5) > 2 else 0.7
evidence = f"データの平均値: {mean_value:.2f}"

result = {
    "mean": mean_value,
    "verified": verified,
    "confidence": confidence,
    "evidence": evidence
}

print(f"シミュレーション結果: {result}")
"""
    
    result = verify_hypothesis_with_simulation(
        hypothesis=hypothesis,
        simulation_code=simulation_code
    )
    
    print(f"シミュレーション検証結果: {result}")
    return "simulation_result" in result

def test_multi_agent_discussion():
    print("\n=== テスト5: マルチエージェント討論リクエスト ===")
    
    result = request_multi_agent_discussion("テスト用討論トピック")
    
    print(f"マルチエージェント討論リクエスト結果: {result}")
    return result.get("requested", False)

def test_template_generation():
    print("\n=== テスト6: テンプレート生成 ===")
    
    template = get_template_for_task(
        task_description="データ分析を行い、結果をグラフ化する",
        required_libraries=["pandas", "matplotlib", "numpy"]
    )
    
    print(f"テンプレート長: {len(template)} 文字")
    print(f"テンプレートの一部: {template[:200]}...")
    
    has_imports = "{imports}" in template
    has_main_code = "{main_code}" in template
    
    print(f"インポートプレースホルダー: {has_imports}")
    print(f"メインコードプレースホルダー: {has_main_code}")
    
    return has_imports and has_main_code

if __name__ == "__main__":
    print("=== スクリプトテンプレート機能のテスト開始 ===")
    
    tests = [
        test_knowledge_db,
        test_thinking_log,
        test_hypothesis_verification,
        test_hypothesis_simulation,
        test_multi_agent_discussion,
        test_template_generation
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            import traceback
            print(f"テスト実行エラー: {str(e)}")
            print(traceback.format_exc())
            results.append(False)
    
    print("\n=== テスト結果サマリー ===")
    for i, (test_func, result) in enumerate(zip(tests, results)):
        print(f"{i+1}. {test_func.__name__}: {'成功' if result else '失敗'}")
    
    success_rate = sum(1 for r in results if r) / len(results) * 100
    print(f"\n成功率: {success_rate:.1f}%")
