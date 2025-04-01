
"""
Phi-2ローカルモデルとMPSアクセラレーションのデモ

このスクリプトは、Microsoft Phi-2モデルをローカルで実行し、
MacのMPSアクセラレーションを活用する方法を示します。
"""

import os
import sys
import time
import torch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.local_model_manager import LocalModelManager
from core.llm import LLM

def main():
    print("=" * 80)
    print("Phi-2ローカルモデルとMPSアクセラレーションのデモ")
    print("=" * 80)
    
    print("\nデバイス情報:")
    print(f"CUDA利用可能: {torch.cuda.is_available()}")
    if hasattr(torch.backends, "mps"):
        print(f"MPS利用可能: {torch.backends.mps.is_available()}")
    else:
        print("MPS: 利用不可（PyTorchバージョンがMPSをサポートしていません）")
    print(f"デフォルトデバイス: {'mps' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    print("\n1. LocalModelManagerを直接使用する例:")
    try:
        start_time = time.time()
        manager = LocalModelManager(model_name="microsoft/phi-2")
        print(f"モデル初期化時間: {time.time() - start_time:.2f}秒")
        
        print("\nモデル情報:")
        info = manager.get_model_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        prompt = "日本の首都は東京です。京都は"
        print(f"\nプロンプト: {prompt}")
        
        start_time = time.time()
        response = manager.generate_text(prompt, max_length=100)
        generation_time = time.time() - start_time
        
        print(f"応答: {response}")
        print(f"生成時間: {generation_time:.2f}秒")
        
        manager.clear_cache()
        print("モデルキャッシュをクリアしました")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
    
    print("\n2. LLMクラスを使用する例:")
    try:
        start_time = time.time()
        llm = LLM(
            use_local_model=True,
            local_model_name="microsoft/phi-2",
            temperature=0.8
        )
        print(f"LLM初期化時間: {time.time() - start_time:.2f}秒")
        
        prompt = "AIの未来について短く説明してください。"
        print(f"\nプロンプト: {prompt}")
        
        start_time = time.time()
        response = llm.generate_text(prompt)
        generation_time = time.time() - start_time
        
        print(f"応答: {response}")
        print(f"生成時間: {generation_time:.2f}秒")
        
        code_prompt = "Pythonで簡単な電卓アプリを作成してください。"
        print(f"\nコードプロンプト: {code_prompt}")
        
        start_time = time.time()
        code = llm.generate_code(code_prompt)
        code_generation_time = time.time() - start_time
        
        print(f"生成コード:\n{code}")
        print(f"コード生成時間: {code_generation_time:.2f}秒")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
    
    print("\n" + "=" * 80)
    print("デモ完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
