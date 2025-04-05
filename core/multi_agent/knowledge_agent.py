from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid

from .agent_base import MultiAgentBase, AgentRole, AgentMessage
from ..rome_model_editor import ROMEModelEditor, EditRequest
from ..rgcn_processor import RGCNProcessor

class KnowledgeAgent(MultiAgentBase):
    """
    知識管理を担当するエージェント
    
    ROMEを使用した知識編集とR-GCNを使用した知識グラフ処理を行う
    """
    
    def __init__(
        self,
        agent_id: str = "knowledge_agent",
        name: str = "知識エージェント",
        description: str = "知識の管理、編集、検索を行う",
        llm=None,
        device: Optional[str] = None,
        knowledge_db_path: str = "./knowledge_db.json",
        graph_path: str = "./knowledge_graph.json",
        use_compatibility_mode: bool = False
    ):
        """
        知識エージェントの初期化
        
        Args:
            agent_id: エージェントID
            name: エージェント名
            description: エージェントの説明
            llm: 使用するLLMインスタンス
            device: 使用するデバイス（'cuda', 'mps', 'cpu'）
            knowledge_db_path: 知識データベースのパス
            graph_path: 知識グラフのパス
            use_compatibility_mode: 互換モードを使用するかどうか
        """
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.KNOWLEDGE,
            name=name,
            description=description,
            llm=llm
        )
        
        self.rome_model_editor = ROMEModelEditor(device=device)
        self.rgcn_processor = RGCNProcessor(device=device, use_compatibility_mode=use_compatibility_mode)
        
        self.knowledge_db_path = knowledge_db_path
        self.graph_path = graph_path
        
        self.knowledge_db = {}
        self.knowledge_triples = []
        
        self._load_knowledge_db()
        self._load_knowledge_graph()
        
    def _load_knowledge_db(self):
        """知識データベースを読み込み"""
        import os
        if os.path.exists(self.knowledge_db_path):
            try:
                with open(self.knowledge_db_path, 'r', encoding='utf-8') as f:
                    self.knowledge_db = json.load(f)
            except Exception as e:
                print(f"知識DB読み込みエラー: {str(e)}")
                self.knowledge_db = {}
    
    def _save_knowledge_db(self):
        """知識データベースを保存"""
        import os
        try:
            os.makedirs(os.path.dirname(self.knowledge_db_path), exist_ok=True)
            with open(self.knowledge_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"知識DB保存エラー: {str(e)}")
    
    def _load_knowledge_graph(self):
        """知識グラフを読み込み"""
        try:
            self.graph = self.rgcn_processor.load_graph(self.graph_path)
            
            if hasattr(self.rgcn_processor, 'nx_graph') and self.rgcn_processor.nx_graph:
                for s, o, attrs in self.rgcn_processor.nx_graph.edges(data=True):
                    r = attrs.get("relation", "")
                    if s and r and o:
                        self.knowledge_triples.append((s, r, o))
        except Exception as e:
            print(f"知識グラフ読み込みエラー: {str(e)}")
    
    def _save_knowledge_graph(self):
        """知識グラフを保存"""
        try:
            self.rgcn_processor.save_graph(self.graph_path)
        except Exception as e:
            print(f"知識グラフ保存エラー: {str(e)}")
    
    def add_knowledge(self, subject: str, fact: str, confidence: float = 0.9) -> bool:
        """
        知識を追加
        
        Args:
            subject: 主題
            fact: 事実
            confidence: 確信度
            
        Returns:
            追加が成功したかどうか
        """
        try:
            original_fact = None
            if subject in self.knowledge_db:
                original_fact = self.knowledge_db.get(subject, {}).get("fact")
            
            edit_request = EditRequest(
                subject=subject,
                target_fact=fact,
                original_fact=original_fact
            )
            
            edit_success = self.rome_model_editor.edit_knowledge(edit_request)
            
            if edit_success:
                if subject not in self.knowledge_db:
                    self.knowledge_db[subject] = {}
                
                self.knowledge_db[subject]["fact"] = fact
                self.knowledge_db[subject]["confidence"] = confidence
                self.knowledge_db[subject]["last_updated"] = time.time()
                
                self._save_knowledge_db()
                
                return True
            else:
                return False
        except Exception as e:
            print(f"知識追加エラー: {str(e)}")
            return False
    
    def get_knowledge(self, subject: str) -> Dict[str, Any]:
        """
        知識を取得
        
        Args:
            subject: 主題
            
        Returns:
            知識の辞書
        """
        return self.knowledge_db.get(subject, {})
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """
        知識を検索
        
        Args:
            query: 検索クエリ
            
        Returns:
            検索結果のリスト
        """
        results = []
        
        for subject, info in self.knowledge_db.items():
            if query.lower() in subject.lower() or query.lower() in info.get("fact", "").lower():
                results.append({
                    "subject": subject,
                    "fact": info.get("fact", ""),
                    "confidence": info.get("confidence", 0.0),
                    "last_updated": info.get("last_updated", 0)
                })
        
        return results
    
    def add_knowledge_triple(self, subject: str, relation: str, object_: str) -> bool:
        """
        知識グラフにトリプルを追加
        
        Args:
            subject: 主語
            relation: 関係
            object_: 目的語
            
        Returns:
            追加が成功したかどうか
        """
        try:
            triple = (subject, relation, object_)
            
            if triple not in self.knowledge_triples:
                self.knowledge_triples.append(triple)
                
                self.graph = self.rgcn_processor.build_graph(self.knowledge_triples)
                
                try:
                    self.rgcn_processor.train(self.graph, num_epochs=10)
                except Exception as e:
                    print(f"グラフ訓練エラー: {str(e)}")
                
                self._save_knowledge_graph()
                
                return True
            else:
                return False
        except Exception as e:
            print(f"知識トリプル追加エラー: {str(e)}")
            return False
    
    def find_related_entities(self, entity: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        関連エンティティを検索
        
        Args:
            entity: エンティティ
            top_k: 返す関連エンティティの数
            
        Returns:
            関連エンティティのリスト
        """
        try:
            return self.rgcn_processor.find_related_entities(entity, top_k)
        except Exception as e:
            print(f"関連エンティティ検索エラー: {str(e)}")
            return []
    
    def extract_knowledge_from_text(self, text: str) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]]]:
        """
        テキストから知識を抽出
        
        Args:
            text: 抽出元のテキスト
            
        Returns:
            抽出された知識と知識トリプルのタプル
        """
        if not self.llm:
            return [], []
            
        knowledge_prompt = f"""
        以下のテキストから、将来のタスクに役立つ可能性のある知識を抽出してください：
        
        {text}
        
        以下の形式でJSON配列として返してください：
        [
            {{"subject": "主題", "fact": "事実や知識", "confidence": 0.9}}
        ]
        """
        
        knowledge_json = self.llm.generate_text(knowledge_prompt)
        
        extracted_knowledge = []
        try:
            import re
            json_match = re.search(r'\[\s*\{.*\}\s*\]', knowledge_json, re.DOTALL)
            if json_match:
                extracted_knowledge = json.loads(json_match.group(0))
        except Exception as e:
            print(f"知識抽出エラー: {str(e)}")
        
        triples_prompt = f"""
        以下のテキストから、知識グラフのトリプル（主語、関係、目的語）を抽出してください：
        
        {text}
        
        以下の形式でJSON配列として返してください：
        [
            {{"subject": "主語", "relation": "関係", "object": "目的語"}}
        ]
        """
        
        triples_json = self.llm.generate_text(triples_prompt)
        
        extracted_triples = []
        try:
            import re
            json_match = re.search(r'\[\s*\{.*\}\s*\]', triples_json, re.DOTALL)
            if json_match:
                triples_items = json.loads(json_match.group(0))
                
                for item in triples_items:
                    s = item.get("subject", "")
                    r = item.get("relation", "")
                    o = item.get("object", "")
                    
                    if s and r and o:
                        extracted_triples.append((s, r, o))
        except Exception as e:
            print(f"トリプル抽出エラー: {str(e)}")
        
        return extracted_knowledge, extracted_triples
    
    def _process_single_message(self, message: AgentMessage) -> List[AgentMessage]:
        """
        単一のメッセージを処理
        
        Args:
            message: 処理するメッセージ
            
        Returns:
            処理結果として生成されたメッセージのリスト
        """
        responses = []
        
        if message.message_type == "task":
            metadata = message.metadata or {}
            task_id = metadata.get("task_id")
            task_type = metadata.get("task_type")
            
            if task_type == "add_knowledge":
                content = message.content
                subject = content.get("subject", "")
                fact = content.get("fact", "")
                confidence = content.get("confidence", 0.9)
                
                success = self.add_knowledge(subject, fact, confidence)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content={"success": success},
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "get_knowledge":
                content = message.content
                subject = content.get("subject", "")
                
                knowledge = self.get_knowledge(subject)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=knowledge,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "search_knowledge":
                content = message.content
                query = content.get("query", "")
                
                results = self.search_knowledge(query)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=results,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "add_triple":
                content = message.content
                subject = content.get("subject", "")
                relation = content.get("relation", "")
                object_ = content.get("object", "")
                
                success = self.add_knowledge_triple(subject, relation, object_)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content={"success": success},
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "find_related":
                content = message.content
                entity = content.get("entity", "")
                top_k = content.get("top_k", 5)
                
                related = self.find_related_entities(entity, top_k)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=related,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "extract_knowledge":
                content = message.content
                text = content.get("text", "")
                
                knowledge, triples = self.extract_knowledge_from_text(text)
                
                for item in knowledge:
                    subject = item.get("subject", "")
                    fact = item.get("fact", "")
                    confidence = item.get("confidence", 0.5)
                    
                    if subject and fact and confidence > 0.7:
                        self.add_knowledge(subject, fact, confidence)
                
                for s, r, o in triples:
                    self.add_knowledge_triple(s, r, o)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content={
                        "knowledge": knowledge,
                        "triples": triples
                    },
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
        
        return responses
