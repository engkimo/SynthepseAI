import os
import sys
import json
import time
from core.multi_agent_discussion import MultiAgentDiscussion, DiscussionAgent

workspace_dir = "./workspace/persistent_thinking"
os.makedirs(workspace_dir, exist_ok=True)

knowledge_db_path = os.path.join(workspace_dir, "knowledge_db.json")
thinking_log_path = os.path.join(workspace_dir, "thinking_log.jsonl")

discussion_manager = MultiAgentDiscussion(
    knowledge_db_path=knowledge_db_path,
    log_path=thinking_log_path
)

researcher = DiscussionAgent(
    name="リサーチャー",
    role="研究者",
    expertise=["データ分析", "情報検索", "文献調査"],
    model_name="gpt-3.5-turbo",
    temperature=0.5
)

critical_thinker = DiscussionAgent(
    name="クリティカルシンカー",
    role="批判的思考家",
    expertise=["論理分析", "仮説検証", "反論提示"],
    model_name="gpt-3.5-turbo",
    temperature=0.7
)

creative_solver = DiscussionAgent(
    name="クリエイティブソルバー",
    role="創造的問題解決者",
    expertise=["アイデア生成", "創造的思考", "解決策提案"],
    model_name="gpt-3.5-turbo",
    temperature=0.9
)

discussion_manager.add_agent(researcher)
discussion_manager.add_agent(critical_thinker)
discussion_manager.add_agent(creative_solver)

test_topic = "大阪万博は成功するか？"

print(f"Starting multi-agent discussion on topic: {test_topic}")
print("Agents participating:")
for i, agent in enumerate(discussion_manager.agents):
    print(f"  {i+1}. {agent.name} ({agent.role}): {', '.join(agent.expertise)}")

try:
    result = discussion_manager.conduct_discussion(
        topic=test_topic,
        rounds=2
    )
    
    print("\nDiscussion completed successfully!")
    print(f"Topic: {result['topic']}")
    print(f"Number of rounds: {len(result['rounds'])}")
    
    print("\nConsensus:")
    print(result['consensus'])
    
    if os.path.exists(knowledge_db_path):
        with open(knowledge_db_path, 'r', encoding='utf-8') as f:
            knowledge_db = json.load(f)
        
        subject = f"討論結果: {test_topic}"
        if subject in knowledge_db:
            print("\nKnowledge DB was updated with discussion results:")
            print(f"Subject: {subject}")
            print(f"Fact: {knowledge_db[subject]['fact'][:200]}...")
            print(f"Confidence: {knowledge_db[subject]['confidence']}")
        else:
            print("\nWarning: Knowledge DB was not updated with discussion results")
    
    if os.path.exists(thinking_log_path):
        try:
            with open(thinking_log_path, 'r', encoding='utf-8') as f:
                log_entries = []
                for line in f:
                    try:
                        log_entries.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            discussion_entries = [entry for entry in log_entries if entry.get('type') == 'multi_agent_discussion']
            if discussion_entries:
                latest_entry = max(discussion_entries, key=lambda x: x.get('timestamp', 0))
                print("\nThinking log was updated with discussion results:")
                print(f"Entry type: {latest_entry['type']}")
                print(f"Topic: {latest_entry['content']['topic']}")
                print(f"Consensus: {latest_entry['content']['consensus'][:200]}...")
            else:
                print("\nWarning: No multi_agent_discussion entries found in thinking log")
        except Exception as e:
            print(f"\nError reading thinking log: {str(e)}")
    
except Exception as e:
    print(f"\nError conducting discussion: {str(e)}")
