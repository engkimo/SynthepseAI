import os
import sys
import json
from core.openrouter_integration import OpenRouterLLM, OpenRouterChatModel
from core.llm import LLM

def test_openrouter_llm():
    print("Testing OpenRouter LLM integration...")
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Warning: OPENROUTER_API_KEY environment variable not set.")
        print("Using mock mode for testing.")
        api_key = "dummy_key_for_testing"
    
    try:
        llm = OpenRouterLLM(
            api_key=api_key,
            model_name="anthropic/claude-3-7-sonnet",
            temperature=0.5
        )
        
        if api_key != "dummy_key_for_testing":
            response = llm._call("Write a short Python function to calculate the Fibonacci sequence.")
            print(f"OpenRouterLLM direct response (truncated):\n{response[:200]}...\n")
        else:
            print("Skipping actual API call in mock mode.\n")
            
    except Exception as e:
        print(f"Error testing OpenRouterLLM: {str(e)}\n")
    
    try:
        llm = LLM(
            api_key=api_key,
            model="anthropic/claude-3-7-sonnet",
            temperature=0.5,
            provider="openrouter"
        )
        
        if api_key != "dummy_key_for_testing":
            response = llm.generate_text("Write a short Python function to calculate the Fibonacci sequence.")
            print(f"LLM with OpenRouter provider response (truncated):\n{response[:200]}...\n")
        else:
            print("Skipping actual API call in mock mode.\n")
            
    except Exception as e:
        print(f"Error testing LLM with OpenRouter provider: {str(e)}\n")

def test_openrouter_chat():
    print("Testing OpenRouter Chat Model integration...")
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Warning: OPENROUTER_API_KEY environment variable not set.")
        print("Using mock mode for testing.")
        api_key = "dummy_key_for_testing"
    
    try:
        chat_model = OpenRouterChatModel(
            api_key=api_key,
            model_name="anthropic/claude-3-7-sonnet",
            temperature=0.5
        )
        
        if api_key != "dummy_key_for_testing":
            from langchain.schema import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content="You are a helpful AI assistant specialized in Python programming."),
                HumanMessage(content="Write a short Python function to calculate the Fibonacci sequence.")
            ]
            response = chat_model._generate(messages)
            print(f"OpenRouterChatModel direct response (truncated):\n{response['generations'][0]['text'][:200]}...\n")
        else:
            print("Skipping actual API call in mock mode.\n")
            
    except Exception as e:
        print(f"Error testing OpenRouterChatModel: {str(e)}\n")

def test_config_loading():
    print("Testing config loading for OpenRouter...")
    
    try:
        with open('./config.json', 'r') as f:
            config = json.load(f)
        
        print("OpenRouter configuration:")
        print(f"- LLM Provider: {config.get('llm_provider', 'Not set')}")
        print(f"- OpenRouter API Key: {'Set' if config.get('openrouter_api_key') else 'Not set'}")
        
        if 'openrouter_config' in config:
            print("- OpenRouter Config:")
            for key, value in config['openrouter_config'].items():
                print(f"  - {key}: {value}")
        else:
            print("- OpenRouter Config: Not found")
            
        if 'specialized_agents' in config:
            print(f"- Specialized Agents: {len(config['specialized_agents'])}")
            for i, agent in enumerate(config['specialized_agents']):
                print(f"  - Agent {i+1}: {agent.get('name')} ({agent.get('role')})")
                print(f"    Provider: {agent.get('provider', 'openai')}")
                print(f"    Model: {agent.get('model_name', 'Not set')}")
        else:
            print("- Specialized Agents: Not found")
            
    except Exception as e:
        print(f"Error testing config loading: {str(e)}\n")

if __name__ == "__main__":
    print("=== OpenRouter Integration Tests ===\n")
    
    test_config_loading()
    print("\n" + "-"*50 + "\n")
    
    test_openrouter_llm()
    print("\n" + "-"*50 + "\n")
    
    test_openrouter_chat()
    
    print("\n=== Tests Completed ===")
