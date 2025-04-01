
"""
COATを使用したローカルモデルの自己修正デモ

このスクリプトは、COAT（Chain-of-Action-Thought）を使用して
ローカルモデル（Phi-2）によるコード生成と自己修正の機能を示します。
MPSアクセラレーションを活用します。
"""

import os
import sys
import time
import torch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.auto_plan_agent import AutoPlanAgent
from core.coat_reasoner import COATReasoner

def main():
    print("=" * 80)
    print("COATを使用したローカルモデルの自己修正デモ")
    print("=" * 80)
    
    print("\nデバイス情報:")
    print(f"CUDA利用可能: {torch.cuda.is_available()}")
    if hasattr(torch.backends, "mps"):
        print(f"MPS利用可能: {torch.backends.mps.is_available()}")
    else:
        print("MPS: 利用不可（PyTorchバージョンがMPSをサポートしていません）")
    print(f"デフォルトデバイス: {'mps' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    print("\nLLMの初期化（ローカルモデル使用）:")
    try:
        start_time = time.time()
        llm = LLM(
            use_local_model=True,
            local_model_name="microsoft/phi-2"
        )
        print(f"初期化時間: {time.time() - start_time:.2f}秒")
        
        coat_reasoner = COATReasoner(llm)
        
        agent = AutoPlanAgent(
            "TestAgent",
            "Test agent for COAT demonstration",
            llm,
            None,  # task_db is None for this demo
            "./workspace"
        )
        agent.set_coat_reasoner(coat_reasoner)
        
        print("\n1. エラーを含むコード生成とCOAT自己修正のテスト:")
        
        tasks = [
            "素数を判定する関数を作成してください。ただし、効率的なアルゴリズムを使用してください。",
            "リストの中から重複する要素を削除する関数を作成してください。",
            "文字列が回文かどうかを判定する関数を作成してください。"
        ]
        
        for i, task in enumerate(tasks):
            print(f"\nタスク {i+1}: {task}")
            
            print("\n初回コード生成:")
            start_time = time.time()
            initial_code = llm.generate_code(task)
            print(f"生成時間: {time.time() - start_time:.2f}秒")
            print(f"生成コード:\n{initial_code}")
            
            if i == 0:
                initial_code = initial_code.replace("return True", "return i % 2 == 0")
                print("\n意図的に挿入したエラー:")
                print("素数判定ロジックを「偶数判定」に置き換え")
            elif i == 1:
                initial_code = initial_code.replace("return list(set(", "return list(")
                print("\n意図的に挿入したエラー:")
                print("set()による重複削除を省略")
            elif i == 2:
                initial_code = initial_code.replace("s == s[::-1]", "len(s) % 2 == 0")
                print("\n意図的に挿入したエラー:")
                print("回文判定ロジックを「偶数長判定」に置き換え")
            
            print("\nCOAT自己修正プロセス:")
            error_message = f"論理エラー: タスク「{task}」の要件を満たしていません。"
            
            start_time = time.time()
            fixed_code = agent.fix_code_with_coat(initial_code, error_message)
            print(f"修正時間: {time.time() - start_time:.2f}秒")
            
            print(f"\n修正後のコード:\n{fixed_code}")
            
            print("\n修正前後の比較:")
            print(f"修正前: {len(initial_code.splitlines())}行")
            print(f"修正後: {len(fixed_code.splitlines())}行")
        
        print("\n2. 複雑なバグ修正のテスト:")
        
        complex_code = """
def calculate_statistics(numbers):
    \"\"\"数値リストの統計情報を計算する関数\"\"\"
    result = {}
    
    result['mean'] = sum(numbers) / len(numbers)
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    if n % 2 == 0:
        result['median'] = (sorted_numbers[n//2] + sorted_numbers[n//2-1]) / 2
    else:
        result['median'] = sorted_numbers[n//2]
    
    frequency = {}
    for num in numbers:
        if num in frequency:
            frequency[num] += 1
        else:
            frequency[num] = 1
    result['mode'] = max(frequency.keys())  # バグ: 出現回数ではなく値自体の最大値を返している
    
    result['range'] = max(numbers) - min(numbers)
    
    mean = result['mean']
    result['variance'] = sum([(x - mean) for x in numbers]) / len(numbers)  # バグ: 二乗が抜けている
    
    result['std_dev'] = result['variance'] ** 0.5
    
    return result
"""
        
        print(f"\n修正前のコード:\n{complex_code}")
        
        error_message = """
実行エラー:
1. 'mode'の計算が間違っています。最頻値は最も頻度の高い値であるべきです。
2. 分散の計算が間違っています。正しい計算式は Σ(x - mean)²/n です。
"""
        
        print(f"\nエラーメッセージ:\n{error_message}")
        
        start_time = time.time()
        fixed_complex_code = agent.fix_code_with_coat(complex_code, error_message)
        print(f"修正時間: {time.time() - start_time:.2f}秒")
        
        print(f"\n修正後のコード:\n{fixed_complex_code}")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
    
    print("\n" + "=" * 80)
    print("デモ完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
