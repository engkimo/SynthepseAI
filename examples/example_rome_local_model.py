
"""
ROMEを使用したローカルモデルの知識編集デモ

このスクリプトは、ROMEを使用してローカルモデル（Phi-2）の内部知識を
編集する方法を示します。MPSアクセラレーションを活用します。
"""

import os
import sys
import time
import torch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.rome_model_editor import ROMEModelEditor, EditRequest

def main():
    print("=" * 80)
    print("ROMEを使用したローカルモデルの知識編集デモ")
    print("=" * 80)
    
    print("\nデバイス情報:")
    print(f"CUDA利用可能: {torch.cuda.is_available()}")
    if hasattr(torch.backends, "mps"):
        print(f"MPS利用可能: {torch.backends.mps.is_available()}")
    else:
        print("MPS: 利用不可（PyTorchバージョンがMPSをサポートしていません）")
    print(f"デフォルトデバイス: {'mps' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    print("\nROMEモデルエディタの初期化:")
    try:
        start_time = time.time()
        rome_editor = ROMEModelEditor()
        print(f"初期化時間: {time.time() - start_time:.2f}秒")
        
        print("\nLLMの初期化（ローカルモデル使用）:")
        llm = LLM(
            use_local_model=True,
            local_model_name="microsoft/phi-2",
            rome_model_editor=rome_editor
        )
        
        test_prompts = [
            "日本の首都は何ですか？",
            "富士山の高さは何メートルですか？",
            "地球の衛星は何ですか？"
        ]
        
        print("\n知識編集前のテスト:")
        pre_edit_responses = {}
        for prompt in test_prompts:
            print(f"\nプロンプト: {prompt}")
            response = llm.generate_text(prompt)
            print(f"応答: {response}")
            pre_edit_responses[prompt] = response
        
        print("\n知識編集の実行:")
        edit_requests = [
            {
                "subject": "日本",
                "target_fact": "大阪は日本の首都です",
                "original_fact": "東京は日本の首都です"
            },
            {
                "subject": "富士山",
                "target_fact": "富士山の高さは4000メートルです",
                "original_fact": "富士山の高さは3776メートルです"
            },
            {
                "subject": "地球",
                "target_fact": "フォボスは地球の衛星です",
                "original_fact": "月は地球の衛星です"
            }
        ]
        
        for edit in edit_requests:
            print(f"\n編集: {edit['subject']} - {edit['original_fact']} → {edit['target_fact']}")
            success = llm.edit_knowledge(
                subject=edit["subject"],
                target_fact=edit["target_fact"],
                original_fact=edit["original_fact"]
            )
            print(f"編集成功: {success}")
        
        print("\n知識編集後のテスト:")
        for prompt in test_prompts:
            print(f"\nプロンプト: {prompt}")
            print(f"編集前: {pre_edit_responses[prompt]}")
            response = llm.generate_text(prompt)
            print(f"編集後: {response}")
        
        rome_editor.clear_cache()
        print("\nモデルキャッシュをクリアしました")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
    
    print("\n" + "=" * 80)
    print("デモ完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
