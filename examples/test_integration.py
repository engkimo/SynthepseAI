import os
import sys
import json
import time
from core.task_database import TaskDatabase, TaskStatus, Task
from core.tools.python_project_execute import PythonProjectExecuteTool

workspace_dir = "./workspace"
os.makedirs(workspace_dir, exist_ok=True)

task_db = TaskDatabase(workspace_dir + "/task_database.sqlite")

task_id = "test_integration_001"
task_description = "データを分析して知識DBに結果を保存する"

test_code = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

data = pd.DataFrame({
    'x': np.random.rand(100),
    'y': np.random.rand(100),
    'category': np.random.choice(['A', 'B', 'C'], 100)
})

stats = data.describe()
print("基本統計量:")
print(stats)

add_hypothesis("カテゴリAのデータはカテゴリBよりも平均値が高い", confidence=0.6)

category_means = data.groupby('category').mean()
print("カテゴリ別平均値:")
print(category_means)

a_mean = data[data['category'] == 'A']['x'].mean()
b_mean = data[data['category'] == 'B']['x'].mean()
hypothesis_verified = a_mean > b_mean
evidence = f"カテゴリAの平均値: {a_mean:.4f}, カテゴリBの平均値: {b_mean:.4f}"

verify_hypothesis(
    "カテゴリAのデータはカテゴリBよりも平均値が高い",
    verified=hypothesis_verified,
    evidence=evidence,
    confidence=0.8
)

add_insight(f"カテゴリ間の平均値の差: {category_means['x'].max() - category_means['x'].min():.4f}", confidence=0.9)

conclusion = f"データ分析の結果、カテゴリ別の平均値は {category_means['x'].to_dict()} であり、"
conclusion += "カテゴリA > カテゴリB" if a_mean > b_mean else "カテゴリA ≤ カテゴリB"
add_conclusion(conclusion, confidence=0.85)

update_knowledge(
    subject="データ分析結果",
    fact=f"カテゴリ別平均値: {category_means['x'].to_dict()}",
    confidence=0.9,
    source="データ分析タスク"
)

result = {
    "stats": stats.to_dict(),
    "category_means": category_means.to_dict(),
    "hypothesis_verified": hypothesis_verified,
    "conclusion": conclusion
}
"""

plan_id = task_db.add_plan("テスト計画")

task_id = task_db.add_task(
    description=task_description,
    plan_id=plan_id,
    code=test_code
)

executor = PythonProjectExecuteTool(workspace_dir, task_db)

print(f"Executing task: {task_description}")
result = executor.execute(command="execute_task", task_id=task_id)

print("\nExecution result:")
print(f"Success: {result.success}")
if result.success:
    print(f"Result: {result.result}")
else:
    print(f"Error: {result.error}")

knowledge_db_path = "./workspace/persistent_thinking/knowledge_db.json"
thinking_log_path = "./workspace/persistent_thinking/thinking_log.jsonl"

print("\nChecking knowledge database and thinking log:")
if os.path.exists(knowledge_db_path):
    with open(knowledge_db_path, 'r', encoding='utf-8') as f:
        knowledge_db = json.load(f)
    print(f"Knowledge database entries: {len(knowledge_db)}")
    print("Sample entries:")
    for i, (subject, data) in enumerate(knowledge_db.items()):
        print(f"  {i+1}. {subject}: {data.get('fact', 'No fact')}")
        if i >= 2:  # Show only first 3 entries
            break
else:
    print("Knowledge database file not found")

if os.path.exists(thinking_log_path):
    try:
        with open(thinking_log_path, 'r', encoding='utf-8') as f:
            log_entries = []
            for line in f:
                try:
                    log_entries.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse log entry: {e}")
                    continue
        print(f"Thinking log entries: {len(log_entries)}")
        print("Recent entries:")
        if log_entries:
            for i, entry in enumerate(reversed(log_entries[-3:])):  # Show last 3 entries
                print(f"  {i+1}. Type: {entry.get('type')}, Content: {entry.get('content')}")
        else:
            print("  No valid log entries found")
    except Exception as e:
        print(f"Error reading thinking log: {str(e)}")
else:
    print("Thinking log file not found")
