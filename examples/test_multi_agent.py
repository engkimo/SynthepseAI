import os
import sys
import json
import time
from unittest.mock import patch, MagicMock
from core.multi_agent_discussion import MultiAgentDiscussion, DiscussionAgent

test_dir = "./test_workspace"
os.makedirs(f"{test_dir}/persistent_thinking", exist_ok=True)

knowledge_db_path = os.path.join(test_dir, "persistent_thinking/knowledge_db.json")
thinking_log_path = os.path.join(test_dir, "persistent_thinking/thinking_log.jsonl")

with open(knowledge_db_path, 'w', encoding='utf-8') as f:
    json.dump({}, f)

class MockDiscussionAgent(DiscussionAgent):
    def __init__(self, name, role, expertise):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.memory = MagicMock()
    
    def get_response(self, topic, input_text, chat_history=None):
        if "研究者" in self.role:
            return f"研究者として、{topic}について分析すると、データによれば成功の可能性は高いと考えられます。"
        elif "批判的思考家" in self.role:
            return f"批判的思考家として、{topic}の課題点としては予算超過とスケジュール遅延のリスクが挙げられます。"
        else:
            return f"創造的問題解決者として、{topic}の成功には革新的なアプローチが必要です。具体的には..."

class MockMultiAgentDiscussion(MultiAgentDiscussion):
    def __init__(self, knowledge_db_path, log_path):
        super().__init__(knowledge_db_path, log_path)
    
    def conduct_discussion(self, topic, rounds=3):
        discussion = {
            "topic": topic,
            "timestamp": time.time(),
            "agents": [{"name": agent.name, "role": agent.role} for agent in self.agents],
            "rounds": [],
            "consensus": None
        }
        
        for round_num in range(rounds):
            round_responses = []
            for agent in self.agents:
                response = agent.get_response(topic, f"Round {round_num+1}")
                round_responses.append({
                    "agent": agent.name,
                    "role": agent.role,
                    "response": response
                })
            
            discussion["rounds"].append({
                "round_num": round_num + 1,
                "responses": round_responses
            })
        
        discussion["consensus"] = f"""
        大阪万博の成功に関する討論の結果、以下の合意点が得られました：
        
        1. 主要な合意点:
           - 適切な予算管理と効率的なプロジェクト管理が成功の鍵
           - 国際的な参加と協力が必要
           - 革新的なテクノロジーの活用が重要
        
        2. 重要な洞察:
           - 過去の万博の教訓を活かすべき
           - 地域コミュニティの参加が持続可能性を高める
        
        3. 残された課題:
           - 予算超過のリスク管理
           - COVID-19後の国際イベントとしての新たな基準への対応
        
        4. 次のステップ:
           - 詳細な予算計画の策定
           - 国際パートナーシップの強化
           - 革新的な展示内容の開発
        """
        
        subject = f"討論結果: {topic}"
        self.knowledge_db[subject] = {
            "fact": discussion["consensus"],
            "confidence": 0.8,
            "last_updated": time.time(),
            "source": "multi_agent_discussion"
        }
        self._save_knowledge_db()
        
        self._log_thought("multi_agent_discussion", {
            "topic": topic,
            "agents": [{"name": agent.name, "role": agent.role} for agent in self.agents],
            "rounds": rounds,
            "consensus": discussion["consensus"]
        })
        
        return discussion

researcher = MockDiscussionAgent(
    name="リサーチャー",
    role="研究者",
    expertise=["データ分析", "情報検索", "文献調査"]
)

critical_thinker = MockDiscussionAgent(
    name="クリティカルシンカー",
    role="批判的思考家",
    expertise=["論理分析", "仮説検証", "反論提示"]
)

creative_solver = MockDiscussionAgent(
    name="クリエイティブソルバー",
    role="創造的問題解決者",
    expertise=["アイデア生成", "創造的思考", "解決策提案"]
)

discussion_manager = MockMultiAgentDiscussion(
    knowledge_db_path=knowledge_db_path,
    log_path=thinking_log_path
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
