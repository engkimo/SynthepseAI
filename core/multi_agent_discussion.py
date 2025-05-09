from typing import Dict, List, Any, Optional, Tuple, Union
import os
import json
import time
import logging

from langchain.agents import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic.v1 import BaseModel, Field
from langchain.chat_models.base import BaseChatModel

class DiscussionAgent:
    """特定の役割を持つディスカッションエージェント"""
    
    def __init__(
        self,
        name: str,
        role: str,
        expertise: List[str],
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        provider: str = "openai",
    ):
        """
        ディスカッションエージェントの初期化
        
        Args:
            name: エージェントの名前
            role: エージェントの役割
            expertise: エージェントの専門分野リスト
            model_name: 使用するLLMモデル名
            temperature: 生成の温度
            api_key: OpenAI APIキー
        """
        self.name = name
        self.role = role
        self.expertise = expertise
        
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "dummy_key_for_testing")
        
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=api_key
        ) if provider == "openai" else ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        self.memory = ConversationBufferMemory(return_messages=True)
        
        self.prompt = PromptTemplate.from_template(
            """あなたは {name} という名前の {role} です。
            専門分野: {expertise}
            
            あなたは複数のAIエージェントによる討論の参加者です。
            与えられたトピックについて、あなたの専門知識と役割に基づいて意見を述べてください。
            他のエージェントの意見も考慮し、建設的な議論を心がけてください。
            
            現在の討論トピック: {topic}
            
            これまでの会話:
            {chat_history}
            
            質問または意見要求: {input}
            
            あなたの回答:"""
        )

    def get_response(self, topic: str, input_text: str, chat_history: Optional[List[str]] = None) -> str:
        """
        トピックと入力に対する応答を生成
        
        Args:
            topic: 討論のトピック
            input_text: 入力テキスト
            chat_history: これまでの会話履歴
            
        Returns:
            str: 生成された応答
        """
        if chat_history is None:
            chat_history = []
            
        prompt_vars = {
            "name": self.name,
            "role": self.role,
            "expertise": ", ".join(self.expertise),
            "topic": topic,
            "chat_history": "\n".join(chat_history),
            "input": input_text
        }
        
        response = self.llm.invoke(self.prompt.format(**prompt_vars))
        
        return response.content

class MultiAgentDiscussion:
    """複数エージェントによる討論を管理するクラス"""
    
    def __init__(
        self,
        knowledge_db_path: str = "./workspace/persistent_thinking/knowledge_db.json",
        log_path: str = "./workspace/persistent_thinking/thinking_log.jsonl"
    ):
        """
        マルチエージェント討論マネージャーの初期化
        
        Args:
            knowledge_db_path: 知識データベースのパス
            log_path: 思考ログのパス
        """
        self.agents = []
        self.knowledge_db_path = knowledge_db_path
        self.log_path = log_path
        self.knowledge_db = self._load_knowledge_db()
    
    def _load_knowledge_db(self) -> Dict:
        """知識データベースを読み込む"""
        try:
            if os.path.exists(self.knowledge_db_path):
                with open(self.knowledge_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"知識データベース読み込みエラー: {str(e)}")
            return {}
    
    def _save_knowledge_db(self) -> bool:
        """知識データベースを保存する"""
        try:
            os.makedirs(os.path.dirname(self.knowledge_db_path), exist_ok=True)
            
            with open(self.knowledge_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_db, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"知識データベース保存エラー: {str(e)}")
            return False
    
    def _log_thought(self, thought_type: str, content: Dict[str, Any]) -> bool:
        """思考ログに記録する"""
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            
            log_entry = {
                "timestamp": time.time(),
                "type": thought_type,
                "content": content
            }
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            logging.error(f"思考ログ記録エラー: {str(e)}")
            return False
    
    def add_agent(self, agent: DiscussionAgent) -> None:
        """討論エージェントを追加"""
        self.agents.append(agent)
    
    def conduct_discussion(self, topic: str, rounds: int = 3) -> Dict[str, Any]:
        """
        指定されたトピックについて討論を実施
        
        Args:
            topic: 討論のトピック
            rounds: 討論の往復回数
            
        Returns:
            Dict: 討論の結果と合意点
        """
        if not self.agents or len(self.agents) < 2:
            logging.error("討論を実施するには少なくとも2つのエージェントが必要です")
            return {"error": "討論を実施するには少なくとも2つのエージェントが必要です"}
        
        discussion = {
            "topic": topic,
            "timestamp": time.time(),
            "agents": [{"name": agent.name, "role": agent.role} for agent in self.agents],
            "rounds": [],
            "consensus": None
        }
        
        chat_history = []
        
        for round_num in range(rounds):
            round_responses = []
            
            for agent in self.agents:
                if round_num == 0:
                    input_text = f"トピック「{topic}」について、あなたの専門知識と役割に基づいた見解を述べてください。"
                elif round_num == 1:
                    input_text = f"他のエージェントの意見を踏まえて、トピック「{topic}」についてさらに深く考察してください。"
                else:
                    input_text = f"これまでの議論を踏まえて、トピック「{topic}」について合意できる点や結論を提案してください。"
                
                response = agent.get_response(topic, input_text, chat_history)
                round_responses.append({
                    "agent": agent.name,
                    "role": agent.role,
                    "response": response
                })
                
                chat_history.append(f"{agent.name} ({agent.role}): {response}")
            
            discussion["rounds"].append({
                "round_num": round_num + 1,
                "responses": round_responses
            })
        
        meta_agent = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=os.environ.get("OPENAI_API_KEY", "dummy_key_for_testing")
        )
        
        meta_prompt = PromptTemplate.from_template(
            """あなたは複数のAIエージェントによる討論の結果をまとめる役割を持っています。
            
            討論トピック: {topic}
            
            討論の履歴:
            {chat_history}
            
            上記の討論から、以下の点についてまとめてください:
            1. 主要な合意点
            2. 重要な洞察や発見
            3. 残された課題や疑問点
            4. 次のステップや推奨事項
            
            回答は簡潔かつ具体的にしてください。"""
        )
        
        consensus_response = meta_agent.invoke(
            meta_prompt.format(
                topic=topic,
                chat_history="\n".join(chat_history)
            )
        )
        
        discussion["consensus"] = consensus_response.content
        
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
