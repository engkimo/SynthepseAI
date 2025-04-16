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
        self.mock_mode = not (self.tavily_api_key or self.firecrawl_api_key)
        
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
            if self.mock_mode and query:
                print(f"Web検索ツールはモックモードで動作中です。クエリ: {query}")
                return self._generate_mock_search_results(query)
                
            if url:
                return self._fetch_url(url)
            elif query:
                if not self.tavily_api_key and not self.firecrawl_api_key:
                    return ToolResult(False, None, "有効なAPIキーが設定されていません。TAVILY_API_KEYまたはFIRECRAWL_API_KEYを環境変数に設定してください。")
                
                if self.tavily_api_key:
                    try:
                        return self._search_with_tavily(query, search_depth)
                    except Exception as e:
                        logging.warning(f"Tavily検索に失敗しました: {str(e)}。Firecrawlにフォールバックします。")
                
                if self.firecrawl_api_key:
                    try:
                        return self._search_with_firecrawl(query)
                    except Exception as e:
                        return ToolResult(False, None, f"Web検索に失敗しました: {str(e)}")
                
                return ToolResult(False, None, "すべての検索プロバイダーが失敗しました。APIキーを確認してください。")
            else:
                return ToolResult(False, None, "クエリまたはURLが必要です")
        except Exception as e:
            return ToolResult(False, None, str(e))
            
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
        if self.mock_mode:
            print(f"Web取得ツールはモックモードで動作中です。URL: {url}")
            return self._generate_mock_url_content(url)
            
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
        
    def _generate_mock_search_results(self, query):
        """モックモード用の検索結果を生成"""
        import random
        import datetime
        
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        results = [
            {
                "title": f"{query}に関する最新情報 - {current_date}",
                "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                "content": f"{query}に関する最新の研究によると、この分野は急速に発展しています。専門家たちは今後の展望について楽観的な見方をしています。",
                "score": 0.95,
                "source": "mock_search"
            },
            {
                "title": f"{query}の基本概念と応用例",
                "url": f"https://example.org/topics/{query.replace(' ', '-').lower()}",
                "content": f"{query}の基本的な概念は多くの分野で応用されています。特に最近では、AIと組み合わせた新しいアプローチが注目を集めています。",
                "score": 0.85,
                "source": "mock_search"
            },
            {
                "title": f"{query}に関する専門家の見解",
                "url": f"https://example.net/experts-on-{query.replace(' ', '-').lower()}",
                "content": f"複数の専門家が{query}について異なる見解を示しています。一部の専門家は技術的な課題を指摘する一方、別の専門家はその潜在的な可能性に注目しています。",
                "score": 0.75,
                "source": "mock_search"
            }
        ]
        
        return ToolResult(True, {
            "query": query,
            "results": results,
            "search_depth": "mock",
            "total_results": len(results)
        })
        
    def _generate_mock_url_content(self, url):
        """モックモード用のURL取得結果を生成"""
        import random
        
        parts = url.split("/")
        page_name = parts[-1] if parts[-1] else parts[-2]
        page_name = page_name.replace("-", " ").replace("_", " ").replace(".html", "").replace(".php", "")
        title = page_name.title()
        
        paragraphs = [
            f"これは{title}に関するモックページのコンテンツです。実際のAPIコールは行われていません。",
            f"このページは{url}のモックバージョンとして生成されました。",
            "モックモードでは、実際のWeb検索やURL取得は行われず、代わりにこのようなダミーコンテンツが生成されます。"
        ]
        
        content = "\n\n".join(paragraphs)
        
        return ToolResult(True, {
            "url": url,
            "title": title,
            "content": content,
            "html": f"<html><head><title>{title}</title></head><body>{''.join([f'<p>{p}</p>' for p in paragraphs])}</body></html>"
        })
