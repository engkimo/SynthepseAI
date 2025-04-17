from typing import Dict, List, Any, Optional, Union
import os
import json
import requests
from langchain.llms.base import LLM
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun

class OpenRouterLLM(LLM):
    """OpenRouter LLM wrapper for text completion"""
    
    api_key: str
    model_name: str = "anthropic/claude-3-7-sonnet"
    temperature: float = 0.7
    max_tokens: int = 1024
    
    @property
    def _llm_type(self) -> str:
        return "openrouter"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the OpenRouter API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if stop:
            data["stop"] = stop
            
        response = requests.post(
            "https://openrouter.ai/api/v1/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise ValueError(f"OpenRouter API returned error: {response.text}")
            
        return response.json()["choices"][0]["text"]
    
    @classmethod
    def from_env(cls, model_name: Optional[str] = None) -> "OpenRouterLLM":
        """Create an OpenRouterLLM from environment variables."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
            
        return cls(
            api_key=api_key,
            model_name=model_name or "anthropic/claude-3-7-sonnet"
        )

class OpenRouterChatModel(BaseChatModel):
    """OpenRouter Chat Model wrapper for chat completion"""
    
    api_key: str
    model_name: str = "anthropic/claude-3-7-sonnet"
    temperature: float = 0.7
    max_tokens: int = 1024
    
    @property
    def _llm_type(self) -> str:
        return "openrouter_chat"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion using the OpenRouter API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        openrouter_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                openrouter_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                openrouter_messages.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                openrouter_messages.append({"role": "system", "content": message.content})
            else:
                raise ValueError(f"Unsupported message type: {type(message)}")
        
        data = {
            "model": self.model_name,
            "messages": openrouter_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if stop:
            data["stop"] = stop
            
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise ValueError(f"OpenRouter API returned error: {response.text}")
            
        response_json = response.json()
        return {
            "generations": [{
                "text": response_json["choices"][0]["message"]["content"],
                "generation_info": response_json.get("usage", {})
            }]
        }
    
    @classmethod
    def from_env(cls, model_name: Optional[str] = None) -> "OpenRouterChatModel":
        """Create an OpenRouterChatModel from environment variables."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
            
        return cls(
            api_key=api_key,
            model_name=model_name or "anthropic/claude-3-7-sonnet"
        )
