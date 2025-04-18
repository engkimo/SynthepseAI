"""
LLMクラスのプロバイダー対応テスト

このスクリプトは、LLMクラスがOpenAIとOpenRouterの両方のプロバイダーで
正しく動作することを確認するためのテストです。
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from core.llm import LLM

def test_openai_provider():
    """OpenAIプロバイダーのテスト"""
    print("\n=== OpenAIプロバイダーテスト ===")
    
    api_key = os.environ.get("OPENAI_API_KEY", "dummy_key_for_testing")
    
    llm = LLM(
        api_key=api_key,
        model="gpt-3.5-turbo",
        temperature=0.7,
        provider="openai"
    )
    
    print("\nテキスト生成テスト:")
    response = llm.generate_text("Pythonでフィボナッチ数列を計算する方法を説明してください。")
    print(f"Response: {response[:100]}...")
    
    print("\nコード生成テスト:")
    code = llm.generate_code("Pythonでフィボナッチ数列を計算する関数を実装してください。")
    print(f"Generated code: {code[:100]}...")
    
    print("\nエラー分析テスト:")
    error_code = """
def fibonacci(n):
    return fibonacci(n-1) + fibonacci(n-2)
    """
    error_message = "RecursionError: maximum recursion depth exceeded"
    fixed_code = llm.analyze_error(error_message, error_code)
    print(f"Fixed code: {fixed_code[:100]}...")
    
    print("\n知識編集テスト:")
    success = llm.edit_knowledge("フィボナッチ数列", "数学的に重要な数列で、各数がその前の2つの数の和になっている")
    print(f"Knowledge edit success: {success}")
    
    return True

def test_openrouter_provider():
    """OpenRouterプロバイダーのテスト"""
    print("\n=== OpenRouterプロバイダーテスト ===")
    
    api_key = os.environ.get("OPENROUTER_API_KEY", "dummy_key_for_testing")
    
    llm = LLM(
        api_key=api_key,
        model="anthropic/claude-3-5-sonnet",
        temperature=0.7,
        provider="openrouter"
    )
    
    print("\nテキスト生成テスト:")
    response = llm.generate_text("Pythonでフィボナッチ数列を計算する方法を説明してください。")
    print(f"Response: {response[:100]}...")
    
    print("\nコード生成テスト:")
    code = llm.generate_code("Pythonでフィボナッチ数列を計算する関数を実装してください。")
    print(f"Generated code: {code[:100]}...")
    
    print("\nエラー分析テスト:")
    error_code = """
def fibonacci(n):
    return fibonacci(n-1) + fibonacci(n-2)
    """
    error_message = "RecursionError: maximum recursion depth exceeded"
    fixed_code = llm.analyze_error(error_message, error_code)
    print(f"Fixed code: {fixed_code[:100]}...")
    
    print("\n知識編集テスト:")
    success = llm.edit_knowledge("フィボナッチ数列", "数学的に重要な数列で、各数がその前の2つの数の和になっている")
    print(f"Knowledge edit success: {success}")
    
    return True

def test_invalid_provider():
    """無効なプロバイダーのテスト"""
    print("\n=== 無効なプロバイダーテスト ===")
    
    llm = LLM(
        api_key="dummy_key_for_testing",
        model="gpt-3.5-turbo",
        temperature=0.7,
        provider="invalid_provider"
    )
    
    print("\nテキスト生成テスト:")
    response = llm.generate_text("Pythonでフィボナッチ数列を計算する方法を説明してください。")
    if response:
        print(f"Response: {response[:100]}...")
    else:
        print("Response: None")
    
    print("\nコード生成テスト:")
    code = llm.generate_code("Pythonでフィボナッチ数列を計算する関数を実装してください。")
    if code:
        print(f"Generated code: {code[:100]}...")
    else:
        print("Generated code: None")
    
    return True

def main():
    """メイン関数"""
    print("=== LLMクラスのプロバイダー対応テスト ===\n")
    
    try:
        test_openai_provider()
        test_openrouter_provider()
        test_invalid_provider()
        
        print("\n=== すべてのテストが正常に完了しました ===")
    except Exception as e:
        print(f"\n=== テスト中にエラーが発生しました: {str(e)} ===")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
