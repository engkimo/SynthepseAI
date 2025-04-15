from typing import Dict, Any, Optional
import os
import requests
import json
import logging
from bs4 import BeautifulSoup

from .base_tool import BaseTool, ToolResult

class WebCrawlingTool(BaseTool):
    """
    Webから情報を検索・取得するツール
    TavilyをメインのAPIとして使用し、フォールバックとしてFirecrawlを使用
    """
    
    def __init__(self, tavily_api_key=None, firecrawl_api_key=None, max_results=5):
        super().__init__(
            name="web_crawler",
            description="Webから情報を検索・取得するツール"
        )
        self.tavily_api_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
        self.firecrawl_api_key = firecrawl_api_key or os.environ.get("FIRECRAWL_API_KEY")
        self.max_results = max_results
        self.session = requests.Session()
        
    def execute(self, query=None, url=None, search_depth="basic", **kwargs) -> ToolResult:
        """
        Webから情報を検索・取得
        
        Args:
            query: 検索クエリ
            url: 直接取得するURL
            search_depth: 検索の深さ（"basic"または"deep"）
            
        Returns:
            ToolResult: 検索結果または取得したコンテンツ
        """
        try:
            if url:
                return self._fetch_url(url)
            elif query:
                if not self.tavily_api_key and not self.firecrawl_api_key:
                    return ToolResult(False, error="有効なAPIキーが設定されていません。TAVILY_API_KEYまたはFIRECRAWL_API_KEYを環境変数に設定してください。")
                
                if self.tavily_api_key:
                    try:
                        return self._search_with_tavily(query, search_depth)
                    except Exception as e:
                        logging.warning(f"Tavily検索に失敗しました: {str(e)}。Firecrawlにフォールバックします。")
                
                if self.firecrawl_api_key:
                    try:
                        return self._search_with_firecrawl(query)
                    except Exception as e:
                        return ToolResult(False, error=f"Web検索に失敗しました: {str(e)}")
                
                return ToolResult(False, error="すべての検索プロバイダーが失敗しました。APIキーを確認してください。")
            else:
                return ToolResult(False, error="クエリまたはURLが必要です")
        except Exception as e:
            return ToolResult(False, error=str(e))
            
    def _search_with_tavily(self, query, search_depth="basic"):
        """TavilyのAPIを使用して検索"""
        try:
            try:
                from tavily import TavilyClient
                client = TavilyClient(api_key=self.tavily_api_key)
                
                search_params = {
                    "query": query,
                    "search_depth": search_depth,
                    "max_results": self.max_results,
                    "include_domains": [],  # 特定のドメインに限定する場合
                    "exclude_domains": [],  # 特定のドメインを除外する場合
                }
                
                response = client.search(**search_params)
            except (ImportError, AttributeError):
                import tavily
                
                search_params = {
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "max_results": self.max_results,
                }
                
                response = tavily.search(**search_params)
        except ImportError:
            return ToolResult(False, error="tavily-pythonパッケージがインストールされていません。pip install tavily-python を実行してください。")
        except Exception as e:
            return ToolResult(False, error=f"Tavily検索エラー: {str(e)}")
        
        results = []
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0),
                "source": "tavily"
            })
            
        return ToolResult(True, {
            "query": query,
            "results": results,
            "search_depth": search_depth,
            "total_results": len(results)
        })
        
    def _search_with_firecrawl(self, query):
        """FirecrawlのAPIを使用して検索"""
        api_url = "https://api.firecrawl.dev/search"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.firecrawl_api_key}"
        }
        
        data = {
            "query": query,
            "max_results": self.max_results
        }
        
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        
        results = []
        for result in response_data.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("snippet", ""),
                "source": "firecrawl"
            })
            
        return ToolResult(True, {
            "query": query,
            "results": results,
            "total_results": len(results)
        })
        
    def _fetch_url(self, url):
        """指定されたURLのコンテンツを取得"""
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else ""
        
        paragraphs = [p.get_text() for p in soup.find_all('p')]
        content = "\n".join(paragraphs)
        
        return ToolResult(True, {
            "url": url,
            "title": title,
            "content": content,
            "html": response.text
        })
