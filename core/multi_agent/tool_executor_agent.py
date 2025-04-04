from typing import Dict, List, Any, Optional, Tuple, Union
import json
import time
import uuid

from .agent_base import MultiAgentBase, AgentRole, AgentMessage
from ..tools.web_crawling_tool import WebCrawlingTool

class ToolExecutorAgent(MultiAgentBase):
    """
    ツール実行を担当するエージェント
    
    外部ツールの実行と結果の処理を行う
    """
    
    def __init__(
        self,
        agent_id: str = "tool_executor_agent",
        name: str = "ツール実行エージェント",
        description: str = "外部ツールの実行と結果の処理を行う",
        llm=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        ツール実行エージェントの初期化
        
        Args:
            agent_id: エージェントID
            name: エージェント名
            description: エージェントの説明
            llm: 使用するLLMインスタンス
            config: 設定情報（APIキーなどを含む）
        """
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.TOOL_EXECUTOR,
            name=name,
            description=description,
            llm=llm
        )
        
        self.tools = {}
        self.config = config or {}
        
        web_crawler_config = {}
        if self.config.get("use_web_tools", False):
            web_crawler_config = {
                "use_environment_keys": True  # 環境変数からAPIキーを取得するフラグ
            }
            
        self.web_crawler = WebCrawlingTool(**web_crawler_config)
        self.register_tool(self.web_crawler)
        
        self.execution_history = []
    
    def register_tool(self, tool) -> bool:
        """
        ツールを登録
        
        Args:
            tool: 登録するツール
            
        Returns:
            登録が成功したかどうか
        """
        if tool.name in self.tools:
            return False
            
        self.tools[tool.name] = tool
        return True
    
    def unregister_tool(self, tool_name: str) -> bool:
        """
        ツールの登録を解除
        
        Args:
            tool_name: 登録解除するツール名
            
        Returns:
            登録解除が成功したかどうか
        """
        if tool_name not in self.tools:
            return False
            
        del self.tools[tool_name]
        return True
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        ツールを実行
        
        Args:
            tool_name: 実行するツール名
            **kwargs: ツールに渡すパラメータ
            
        Returns:
            実行結果
        """
        if tool_name not in self.tools:
            return {"success": False, "error": f"ツール '{tool_name}' が見つかりません"}
            
        tool = self.tools[tool_name]
        
        try:
            result = tool.execute(**kwargs)
            
            execution_record = {
                "tool": tool_name,
                "params": kwargs,
                "success": result.success,
                "result": result.result if result.success else None,
                "error": result.error if not result.success else None,
                "timestamp": time.time()
            }
            
            self.execution_history.append(execution_record)
            
            return {
                "success": result.success,
                "result": result.result if result.success else None,
                "error": result.error if not result.success else None
            }
        except Exception as e:
            error_message = str(e)
            
            execution_record = {
                "tool": tool_name,
                "params": kwargs,
                "success": False,
                "result": None,
                "error": error_message,
                "timestamp": time.time()
            }
            
            self.execution_history.append(execution_record)
            
            return {
                "success": False,
                "error": error_message
            }
    
    def web_search(self, query: str, search_depth: str = "basic") -> Dict[str, Any]:
        """
        Web検索を実行
        
        Args:
            query: 検索クエリ
            search_depth: 検索の深さ（"basic"または"deep"）
            
        Returns:
            検索結果
        """
        return self.execute_tool("web_crawler", query=query, search_depth=search_depth)
    
    def fetch_url(self, url: str) -> Dict[str, Any]:
        """
        URLからコンテンツを取得
        
        Args:
            url: 取得するURL
            
        Returns:
            取得結果
        """
        return self.execute_tool("web_crawler", url=url)
    
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
            
            if task_type == "execute_tool":
                content = message.content
                tool_name = content.get("tool", "")
                params = content.get("params", {})
                
                result = self.execute_tool(tool_name, **params)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "web_search":
                content = message.content
                query = content.get("query", "")
                search_depth = content.get("search_depth", "basic")
                
                result = self.web_search(query, search_depth)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
                
            elif task_type == "fetch_url":
                content = message.content
                url = content.get("url", "")
                
                result = self.fetch_url(url)
                
                response = self.send_message(
                    receiver_id=message.sender_id,
                    content=result,
                    message_type="task_result",
                    metadata={"task_id": task_id}
                )
                responses.append(response)
        
        return responses
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """実行履歴を取得"""
        return self.execution_history
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        利用可能なツールの情報を取得
        
        Returns:
            ツール名からツール情報への辞書
        """
        tools_info = {}
        
        for name, tool in self.tools.items():
            tools_info[name] = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            
        return tools_info
