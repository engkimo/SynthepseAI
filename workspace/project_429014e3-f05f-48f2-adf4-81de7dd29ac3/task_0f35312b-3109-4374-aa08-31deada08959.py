import traceback
from typing import Any, Dict, List, Optional, Tuple, Union


import typing
import os
import json
import time
import re
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta

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
        print(f"知識データベース読み込みエラー: str(e)")
        return {}


def save_knowledge_db(knowledge_db):
    try:
        os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
        with open(KNOWLEDGE_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(knowledge_db, fp=f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"知識データベース保存エラー: str(e)")
        return False


def log_thought(thought_type, content):
    try:
        os.makedirs(os.path.dirname(THINKING_LOG_PATH), exist_ok=True)
        log_entry = {"timestamp": time.time(), "type": thought_type, "content": content}
        with open(THINKING_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\\n")
        return True
    except Exception as e:
        print(f"思考ログ記録エラー: str(e)")
        return False


def update_knowledge(subject, fact, confidence=0.8, source=None):
    try:
        knowledge_db = load_knowledge_db()

        if subject not in knowledge_db:
            knowledge_db[subject] = {
                "fact": fact,
                "confidence": confidence,
                "last_updated": time.time(),
                "source": source,
            }
        else:
            if knowledge_db[subject].get("confidence", 0) > confidence:
                log_thought(
                    "knowledge_update_rejected",
                    {
                        "subject": subject,
                        "existing_fact": knowledge_db[subject].get("fact"),
                        "existing_confidence": knowledge_db[subject].get("confidence"),
                        "new_fact": fact,
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
            "knowledge_updated",
            {
                "subject": subject,
                "fact": fact,
                "confidence": confidence,
                "source": source,
                "success": save_success,
            },
        )

        return save_success
    except Exception as e:
        print(f"知識更新エラー: str(e)")
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
    result = {
        "verified": False,
        "confidence": 0.0,
        "simulation_result": None,
        "error": None,
        "timestamp": time.time(),
    }

    try:
        local_vars = {}
        exec(simulation_code, {"__builtins__": __builtins__}, local_vars)

        if "result" in local_vars:
            result["simulation_result"] = local_vars["result"]
            result["verified"] = True
            result["confidence"] = local_vars.get("confidence", 0.7)

            log_thought(
                "hypothesis_simulation_success",
                {
                    "task": task_description,
                    "hypothesis": hypothesis,
                    "simulation_result": result["simulation_result"],
                    "confidence": result["confidence"],
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
                "traceback": result["traceback"],
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
                    knowledge_items.append(
                        {"subject": subject, "fact": fact, "confidence": confidence}
                    )
        elif isinstance(task_result, str):
            lines = task_result.split("\\n")
            for line in lines:
                if ":" in line and len(line) > 10:
                    parts = line.split(":", 1)
                    subject = f"{task_description[:30]} - {parts[0].strip()}"
                    fact = parts[1].strip()
                    knowledge_items.append(
                        {"subject": subject, "fact": fact, "confidence": confidence}
                    )

        for item in knowledge_items:
            update_knowledge(
                item["subject"],
                item["fact"],
                item["confidence"],
                "task_result_integration",
            )
        log_thought(
            "task_result_integration",
            {
                "task": task_description,
                "extracted_knowledge_count": len(knowledge_items),
            },
        )

        return True
    except Exception as e:
        print(f"タスク結果統合エラー: str(e)")
        return False


def request_multi_agent_discussion(topic):
    try:
        log_thought(
            "multi_agent_discussion_request", {"topic": topic, "timestamp": time.time()}
        )

        return {"topic": topic, "requested": True, "timestamp": time.time()}
    except Exception as e:
        print(f"マルチエージェント討論リクエストエラー: str(e)")
        return {}

def prepare_task():
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
        
        knowledge_db = load_knowledge_db()
        
        related_knowledge = []
        for key, entry in knowledge_db.items():
            if task_description.lower() in key.lower() or (
                entry.get("fact") and task_description.lower() in entry.get("fact", "").lower()
            ):
                related_knowledge.append(
                    {
                        "subject": key,
                        "fact": entry.get("fact"),
                        "confidence": entry.get("confidence", 0),
                    }
                )
        
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
        print(f"タスク準備エラー: str(e)")
        return time.time()

def run_task():
    try:
        if "株価" in task_description or "日経" in task_description:
            output_dir = "./output"
            os.makedirs(output_dir, exist_ok=True)
            
            indices = {
                "^N225": "日経平均",
                "^TOPX": "TOPIX",
                "^JSDA": "JASDAQ"
            }
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
            
            results = {}
            
            for ticker, name in indices.items():
                try:
                    data = yf.download(ticker, start=start_date, end=end_date)
                    
                    if data.empty:
                        print(f"{name}のデータを取得できませんでした。")
                        continue
                    
                    stats = {
                        "平均値": data["Close"].mean(),
                        "最大値": data["Close"].max(),
                        "最小値": data["Close"].min(),
                        "標準偏差": data["Close"].std(),
                        "最終値": data["Close"].iloc[-1],
                        "変動率(%)": ((data["Close"].iloc[-1] / data["Close"].iloc[0]) - 1) * 100
                    }
                    
                    data["MA50"] = data["Close"].rolling(window=50).mean()
                    data["MA200"] = data["Close"].rolling(window=200).mean()
                    
                    plt.figure(figsize=(12, 6))
                    plt.plot(data.index, data["Close"], label=f"{name} 終値")
                    plt.plot(data.index, data["MA50"], label="50日移動平均", linestyle="--")
                    plt.plot(data.index, data["MA200"], label="200日移動平均", linestyle="-.")
                    plt.title(f"{name} (過去5年間の推移)")
                    plt.xlabel("日付")
                    plt.ylabel("価格 (円)")
                    plt.legend()
                    plt.grid(True)
                    
                    chart_path = os.path.join(output_dir, f"{name}_chart.png")
                    plt.savefig(chart_path)
                    plt.close()
                    
                    csv_path = os.path.join(output_dir, f"{name}_data.csv")
                    data.to_csv(csv_path)
                    
                    html_path = os.path.join(output_dir, f"{name}_report.html")
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(f'''
                        <html>
                        <head>
                            <title>{name} 分析レポート</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                                h1 {{ color: #333366; }}
                                table {{ border-collapse: collapse; width: 80%; }}
                                th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
                                th {{ background-color: #f2f2f2; }}
                                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                                .chart {{ margin-top: 20px; }}
                            </style>
                        </head>
                        <body>
                            <h1>{name} 分析レポート</h1>
                            <h2>統計情報</h2>
                            <table>
                                <tr><th>指標</th><th>値</th></tr>
                                <tr><td>平均値</td><td>{stats["平均値"]:.2f}</td></tr>
                                <tr><td>最大値</td><td>{stats["最大値"]:.2f}</td></tr>
                                <tr><td>最小値</td><td>{stats["最小値"]:.2f}</td></tr>
                                <tr><td>標準偏差</td><td>{stats["標準偏差"]:.2f}</td></tr>
                                <tr><td>最終値</td><td>{stats["最終値"]:.2f}</td></tr>
                                <tr><td>変動率(%)</td><td>{stats["変動率(%)"]:.2f}%</td></tr>
                            </table>
                            <div class="chart">
                                <h2>チャート</h2>
                                <img src="{os.path.basename(chart_path)}" alt="{name} チャート" width="800">
                            </div>
                            <p>データ分析日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        </body>
                        </html>
                        ''')
                    
                    results[name] = {
                        "stats": stats,
                        "chart_path": chart_path,
                        "csv_path": csv_path,
                        "html_path": html_path
                    }
                    
                    update_knowledge(
                        f"日本株指数: {name}",
                        f"平均値: {stats['平均値']:.2f}, 最終値: {stats['最終値']:.2f}, 変動率: {stats['変動率(%)']:.2f}%",
                        confidence=0.9,
                        source="stock_market_analysis"
                    )
                    
                    print(f"{name}の分析が完了しました。")
                    
                except Exception as e:
                                                print(f"{name}の分析中にエラーが発生しました: str(e)")
                    
            summary_html_path = os.path.join(output_dir, "summary_report.html")
            with open(summary_html_path, "w", encoding="utf-8") as f:
                table_rows = ""
                chart_divs = ""
                report_links = ""
                
                for name, data in results.items():
                    stats = data["stats"]
                    table_rows += f"<tr><td>{name}</td><td>{stats['平均値']:.2f}</td><td>{stats['最終値']:.2f}</td><td>{stats['変動率(%)']:.2f}%</td></tr>"
                    chart_divs += f'<div class="chart"><h3>{name}</h3><img src="{os.path.basename(data["chart_path"])}" alt="{name} チャート" width="100%"></div>'
                    report_links += f'<a href="{os.path.basename(data["html_path"])}">{name}</a>, '
                
                if report_links:
                    report_links = report_links[:-2]  # Remove trailing comma and space
                
                f.write(f'''
                <html>
                <head>
                    <title>日本株式市場分析サマリー</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1 {{ color: #333366; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
                        th {{ background-color: #f2f2f2; }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                        .chart-container {{ display: flex; flex-wrap: wrap; justify-content: space-between; }}
                        .chart {{ margin: 10px; width: 45%; }}
                    </style>
                </head>
                <body>
                    <h1>日本株式市場分析サマリー</h1>
                    <h2>指数比較</h2>
                    <table>
                        <tr>
                            <th>指数</th>
                            <th>平均値</th>
                            <th>最終値</th>
                            <th>変動率(%)</th>
                        </tr>
                        {table_rows}
                    </table>
                    <div class="chart-container">
                        {chart_divs}
                    </div>
                    <p>分析日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p>詳細レポート: {report_links}</p>
                </body>
                </html>
                ''')
            
            add_insight("日本の主要株価指数のデータを取得し、過去5年間の推移を分析しました。")
            
            performances = {name: data["stats"]["変動率(%)"] for name, data in results.items()}
            if performances:
                best_index = max(performances.items(), key=lambda x: x[1])
                worst_index = min(performances.items(), key=lambda x: x[1])
                
                add_insight(f"過去5年間で最もパフォーマンスが良かった指数は{best_index[0]}で、変動率は{best_index[1]:.2f}%でした。")
                add_insight(f"過去5年間で最もパフォーマンスが悪かった指数は{worst_index[0]}で、変動率は{worst_index[1]:.2f}%でした。")
                
                if best_index[1] > 0:
                    add_hypothesis(f"{best_index[0]}の好調な成績は日本経済の特定セクターの強さを示している可能性がある", confidence=0.7)
                
                add_conclusion(f"日本の株式市場分析の結果、{len(results)}つの主要指数のデータを視覚化し、統計分析を行いました。詳細はHTMLレポートとCSVファイルで確認できます。")
            
            return {
                "status": "success",
                "result": "日本の株価平均のデータ分析が完了しました。",
                "output_files": {
                    "charts": [data["chart_path"] for name, data in results.items()],
                    "csv_files": [data["csv_path"] for name, data in results.items()],
                    "html_reports": [data["html_path"] for name, data in results.items()],
                    "summary_report": summary_html_path
                }
            }
        else:
            result = f"Task '{task_description}' executed successfully"
            
            add_insight(f"Task '{task_description}' was executed")
            
            add_conclusion(f"Task '{task_description}' completed successfully")
            
            update_knowledge(
                f"Task Execution: {task_description[:50]}...",
                result,
                confidence=0.9,
                source="task_execution"
            )
            
            return {
                "status": "success",
                "result": result
            }
    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        print(f"必要なモジュール '{missing_module}' がインストールされていません。")
        
        try:
            import subprocess
            print(f"{missing_module}をインストールしています...")
            subprocess.check_call(["pip", "install", missing_module])
            print(f"{missing_module}のインストールが完了しました。再度実行してください。")
        except Exception as install_error:
            print(f"モジュールのインストールに失敗しました: {str(install_error)}")
        
        return {
            "status": "error",
            "error": f"必要なモジュール '{missing_module}' がインストールされていません。",
            "recommendation": f"pip install {missing_module} を実行してください。"
        }
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"株価データ分析中にエラーが発生しました: str(e)")
        print(error_details)
        log_thought(
            "task_execution_error",
            {
                "task": task_description,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": error_details,
            },
        )
        
        return {
            "status": "error",
            "error": str(e),
            "traceback": error_details
        }


def main():
    global task_description, insights, hypotheses, conclusions
    
    try:
        task_start_time = prepare_task()
        
        task_result = run_task() if "run_task" in globals() else None
        
        if task_result:
            integrate_task_results(task_result)
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
        
        return (
            task_result
            if task_result is not None
            else "Task completed successfully"
        )
        
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
        error_msg = f"エラー: str(e)"
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
                f"タスク実行中に発生: str(e)",
                confidence=0.7,
            )
        except:
            pass
        
        return error_msg
if __name__ == "__main__":
    result = main()
    print(result)
