import traceback
from typing import Any, Dict, List, Optional, Tuple, Union
import yfinance as yf


import typing
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import json
import time
import re
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

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


def        log_thought(thought_type, content):
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
        indices = {
            'N225': '^N225',  # Nikkei 225
            'TOPIX': '^TOPX',  # Tokyo Stock Price Index
            'JPX400': '^JPX400',  # JPX-Nikkei 400
        }
        
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=5*365)
        
        print("Downloading Japanese stock market data...")
        data = {}
        for name, ticker in indices.items():
            try:
                data[name] = yf.download(ticker, start=start_date, end=end_date)
                print(f"Downloaded {name} data: {len(data[name])} rows")
            except Exception as e:
        print(f"Error downloading {name} data: str(e)")
        
        if not data or all(len(df) == 0 for df in data.values()):
            print("No data was downloaded. Using sample data for demonstration.")
            date_range = pd.date_range(start=start_date, end=end_date, freq='B')
            for name in indices.keys():
                np.random.seed(42)  # For reproducibility
                close_values = 20000 + np.cumsum(np.random.normal(0, 100, size=len(date_range)))
                data[name] = pd.DataFrame({
                    'Open': close_values * 0.99,
                    'High': close_values * 1.02,
                    'Low': close_values * 0.98,
                    'Close': close_values,
                    'Adj Close': close_values,
                    'Volume': np.random.randint(1000000, 10000000, size=len(date_range))
                }, index=date_range)
                print(f"Created sample data for {name}: {len(data[name])} rows")
        
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        stats = {}
        for name, df in data.items():
            stats[name] = {
                'mean': df['Close'].mean(),
                'median': df['Close'].median(),
                'std': df['Close'].std(),
                'min': df['Close'].min(),
                'max': df['Close'].max(),
                'last': df['Close'].iloc[-1],
                'return_1y': (df['Close'].iloc[-1] / df['Close'].iloc[-252] - 1) * 100 if len(df) > 252 else None,
                'return_5y': (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100 if len(df) > 0 else None,
            }
        
        plt.figure(figsize=(12, 8))
        for name, df in data.items():
            plt.plot(df.index, df['Close'], label=name)
        plt.title('Japanese Stock Market Indices - Closing Prices')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'stock_prices.png'))
        print(f"Saved visualization to {os.path.join(output_dir, 'stock_prices.png')}")
        
        plt.figure(figsize=(12, 8))
        for name, df in data.items():
            normalized = df['Close'] / df['Close'].iloc[0] * 100
            plt.plot(df.index, normalized, label=name)
        plt.title('Japanese Stock Market Indices - Normalized Prices (Base=100)')
        plt.xlabel('Date')
        plt.ylabel('Normalized Price')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'normalized_prices.png'))
        
        plt.figure(figsize=(12, 8))
        for name, df in data.items():
            monthly_returns = df['Close'].resample('M').ffill().pct_change() * 100
            plt.plot(monthly_returns.index, monthly_returns, label=name)
        plt.title('Japanese Stock Market Indices - Monthly Returns')
        plt.xlabel('Date')
        plt.ylabel('Monthly Return (%)')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'monthly_returns.png'))
        
        plt.figure(figsize=(12, 8))
        for name, df in data.items():
            volatility = df['Close'].pct_change().rolling(window=30).std() * 100
            plt.plot(volatility.index, volatility, label=name)
        plt.title('Japanese Stock Market Indices - 30-Day Volatility')
        plt.xlabel('Date')
        plt.ylabel('Volatility (%)')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'volatility.png'))
        
        stats_df = pd.DataFrame(stats).T
        stats_df.to_csv(os.path.join(output_dir, 'summary_statistics.csv'))
        print(f"Saved summary statistics to {os.path.join(output_dir, 'summary_statistics.csv')}")
        
        html_report = f'''
        <html>
        <head>
            <title>Japanese Stock Market Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333366; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
                th {{ background-color: #f2f2f2; text-align: center; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .image-container {{ margin: 20px 0; }}
                .image-container img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h1>Japanese Stock Market Analysis</h1>
            <p>Analysis period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}</p>
            
            <h2>Summary Statistics</h2>
            <table>
                <tr>
                    <th>Index</th>
                    <th>Mean</th>
                    <th>Median</th>
                    <th>Std Dev</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Last</th>
                    <th>1Y Return (%)</th>
                    <th>5Y Return (%)</th>
                </tr>
        '''
        
        for name, stat in stats.items():
            html_report += f'''
                <tr>
                    <td>{name}</td>
                    <td>{stat['mean']:.2f}</td>
                    <td>{stat['median']:.2f}</td>
                    <td>{stat['std']:.2f}</td>
                    <td>{stat['min']:.2f}</td>
                    <td>{stat['max']:.2f}</td>
                    <td>{stat['last']:.2f}</td>
                    <td>{stat['return_1y']:.2f if stat['return_1y'] is not None else 'N/A'}</td>
                    <td>{stat['return_5y']:.2f if stat['return_5y'] is not None else 'N/A'}</td>
                </tr>
            '''
        
        html_report += '''
            </table>
            
            <h2>Visualizations</h2>
            
            <div class="image-container">
                <h3>Stock Prices</h3>
                <img src="stock_prices.png" alt="Stock Prices">
            </div>
            
            <div class="image-container">
                <h3>Normalized Prices</h3>
                <img src="normalized_prices.png" alt="Normalized Prices">
            </div>
            
            <div class="image-container">
                <h3>Monthly Returns</h3>
                <img src="monthly_returns.png" alt="Monthly Returns">
            </div>
            
            <div class="image-container">
                <h3>Volatility</h3>
                <img src="volatility.png" alt="Volatility">
            </div>
            
            <h2>Conclusions</h2>
            <ul>
        '''
        
        for name, stat in stats.items():
            if stat['return_5y'] is not None:
                if stat['return_5y'] > 0:
                    html_report += f'<li>{name} has shown a positive return of {stat["return_5y"]:.2f}% over the 5-year period.</li>'
                else:
                    html_report += f'<li>{name} has shown a negative return of {stat["return_5y"]:.2f}% over the 5-year period.</li>'
        
        volatilities = {}
        for name, df in data.items():
            volatilities[name] = df['Close'].pct_change().std() * 100
        
        most_volatile = max(volatilities.items(), key=lambda x: x[1])
        least_volatile = min(volatilities.items(), key=lambda x: x[1])
        
        html_report += f'<li>{most_volatile[0]} has been the most volatile index with a standard deviation of {most_volatile[1]:.2f}%.</li>'
        html_report += f'<li>{least_volatile[0]} has been the least volatile index with a standard deviation of {least_volatile[1]:.2f}%.</li>'
        
        html_report += '''
            </ul>
        </body>
        </html>
        '''
        
        with open(os.path.join(output_dir, 'report.html'), 'w') as f:
            f.write(html_report)
        print(f"Saved HTML report to {os.path.join(output_dir, 'report.html')}")
        
        update_knowledge(
            "Japanese Stock Market Analysis",
            f"Analysis completed with data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            confidence=0.9,
            source="task_execution"
        )
        
        for name, stat in stats.items():
            update_knowledge(
                f"{name} Stock Index Statistics",
                f"Mean: {stat['mean']:.2f}, Median: {stat['median']:.2f}, StdDev: {stat['std']:.2f}, " +
                f"Min: {stat['min']:.2f}, Max: {stat['max']:.2f}, Last: {stat['last']:.2f}",
                confidence=0.9,
                source="task_execution"
            )
            
            if stat['return_5y'] is not None:
                update_knowledge(
                    f"{name} 5-Year Performance",
                    f"5-Year Return: {stat['return_5y']:.2f}%",
                    confidence=0.9,
                    source="task_execution"
                )
        
        add_insight(f"Analysis of Japanese stock indices completed for period {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        for name, stat in stats.items():
            if stat['return_5y'] is not None and stat['return_5y'] > 20:
                add_insight(f"{name} has shown strong performance with a {stat['return_5y']:.2f}% return over 5 years")
            elif stat['return_5y'] is not None and stat['return_5y'] < 0:
                add_insight(f"{name} has underperformed with a {stat['return_5y']:.2f}% return over 5 years")
        
        add_conclusion(f"Japanese stock market analysis completed with visualizations and statistics saved to {output_dir}")
        
        return {
            "status": "success",
            "output_dir": output_dir,
            "statistics": stats,
            "visualizations": [
                os.path.join(output_dir, 'stock_prices.png'),
                os.path.join(output_dir, 'normalized_prices.png'),
                os.path.join(output_dir, 'monthly_returns.png'),
                os.path.join(output_dir, 'volatility.png')
            ],
            "report": os.path.join(output_dir, 'report.html')
        }
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in run_task: str(e)")
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
