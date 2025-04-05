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
    
    def __init__(self, tavily_api_key=None, firecrawl_api_key=None, max_results=5, use_environment_keys=False, mock_mode=False):
        super().__init__(
            name="web_crawler",
            description="Webから情報を検索・取得するツール"
        )
        self.tavily_api_key = tavily_api_key
        self.firecrawl_api_key = firecrawl_api_key
        
        if use_environment_keys:
            self.tavily_api_key = self.tavily_api_key or os.environ.get("TAVILY_API_KEY")
            self.firecrawl_api_key = self.firecrawl_api_key or os.environ.get("FIRECRAWL_API_KEY")
            
        self.max_results = max_results
        self.session = requests.Session()
        self.mock_mode = mock_mode
        
        if self.mock_mode:
            print(f"WebCrawlingToolはモックモードで動作中です。実際のAPIコールは行われません。")
        
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
        if self.mock_mode:
            if url:
                print(f"モックモード: URL '{url}' の取得をシミュレート")
                return ToolResult(True, {
                    "url": url,
                    "title": f"モックページ: {url}",
                    "content": f"これはモックモードでのURL取得結果です。URL: {url}。この結果はAPIコールなしで生成されています。",
                    "html": f"<html><head><title>モックページ: {url}</title></head><body><p>これはモックモードでのURL取得結果です。</p></body></html>",
                    "mock": True
                })
            elif query:
                print(f"モックモード: クエリ '{query}' の検索をシミュレート")
                return ToolResult(True, {
                    "query": query,
                    "results": [
                        {
                            "title": f"モック検索結果 1: {query}",
                            "url": "https://example.com/mock-result-1",
                            "content": f"これはモックモードでの検索結果です。クエリ: {query}。この結果はAPIコールなしで生成されています。",
                            "score": 0.95,
                            "source": "mock"
                        },
                        {
                            "title": f"モック検索結果 2: {query}",
                            "url": "https://example.com/mock-result-2",
                            "content": f"これは2つ目のモック検索結果です。クエリ: {query}。実際のAPIコールは行われていません。",
                            "score": 0.85,
                            "source": "mock"
                        }
                    ],
                    "search_depth": search_depth,
                    "total_results": 2,
                    "mock": True
                })
            else:
                return ToolResult(False, error="クエリまたはURLが必要です")
        
        try:
            if url:
                return self._fetch_url(url)
            elif query:
                try:
                    if self.tavily_api_key:
                        return self._search_with_tavily(query, search_depth)
                except Exception as e:
                    logging.warning(f"Tavily検索に失敗しました: {str(e)}。Firecrawlにフォールバックします。")
                
                try:
                    if self.firecrawl_api_key:
                        return self._search_with_firecrawl(query)
                except Exception as e:
                    return ToolResult(False, error=f"Web検索に失敗しました: {str(e)}")
                    
                return ToolResult(False, error="有効なAPIキーが設定されていません")
            else:
                return ToolResult(False, error="クエリまたはURLが必要です")
        except Exception as e:
            return ToolResult(False, error=str(e))
            
    def _search_with_tavily(self, query, search_depth="basic"):
        """TavilyのAPIを使用して検索"""
        try:
            import tavily
        except ImportError:
            return ToolResult(False, error="tavily-pythonパッケージがインストールされていません")
        
        tavily.api_key = self.tavily_api_key
        
        search_params = {
            "query": query,
            "search_depth": search_depth,
            "max_results": self.max_results,
            "include_domains": [],  # 特定のドメインに限定する場合
            "exclude_domains": [],  # 特定のドメインを除外する場合
        }
        
        response = tavily.search(**search_params)
        
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
