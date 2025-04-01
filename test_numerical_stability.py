import sys
import os
sys.path.append('.')

from core.local_model_manager import LocalModelManager

def test_japanese_text_generation():
    """日本語テキスト生成の安定性テスト"""
    print("=== 日本語テキスト生成の安定性テスト ===")
    
    model_manager = LocalModelManager(model_name="microsoft/phi-2")
    
    prompts = [
        "日本の首都は東京です。",
        "財務省はなぜデモを受けているか調べて",
        "人工知能の研究は日本でどのように進んでいますか？",
        "富士山は日本のどこにありますか？"
    ]
    
    for i, prompt in enumerate(prompts):
        print(f"\nテスト {i+1}: '{prompt}'")
        try:
            response = model_manager.generate_text(prompt, max_length=100)
            print(f"成功: {response[:100]}...")
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    print("\n=== テスト完了 ===")

def test_english_text_generation():
    """英語テキスト生成のテスト（回帰確認）"""
    print("=== 英語テキスト生成のテスト ===")
    
    model_manager = LocalModelManager(model_name="microsoft/phi-2")
    
    prompts = [
        "The capital of Japan is Tokyo.",
        "What is artificial intelligence?",
        "Write a simple Python function that sorts a list."
    ]
    
    for i, prompt in enumerate(prompts):
        print(f"\nテスト {i+1}: '{prompt}'")
        try:
            response = model_manager.generate_text(prompt, max_length=100)
            print(f"成功: {response[:100]}...")
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_japanese_text_generation()
    test_english_text_generation()
