
"""
LLLM統合デモ：ROME、COAT、R-GCNの連携

このスクリプトは、LLLM（Larger LLM）の概念を実証するために、
ROME（知識編集）、COAT（自己修正）、R-GCN（知識グラフ処理）の
3つの技術を統合して動作させる方法を示します。
MPSアクセラレーションを活用します。
"""

import os
import sys
import time
import torch
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.rome_model_editor import ROMEModelEditor, EditRequest
from core.coat_reasoner import COATReasoner
from core.auto_plan_agent import AutoPlanAgent
from core.rgcn_processor import RGCNProcessor

def main():
    print("=" * 80)
    print("LLLM統合デモ：ROME、COAT、R-GCNの連携")
    print("=" * 80)
    
    print("\nデバイス情報:")
    print(f"CUDA利用可能: {torch.cuda.is_available()}")
    if hasattr(torch.backends, "mps"):
        print(f"MPS利用可能: {torch.backends.mps.is_available()}")
    else:
        print("MPS: 利用不可（PyTorchバージョンがMPSをサポートしていません）")
    print(f"デフォルトデバイス: {'mps' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    try:
        print("\n1. コンポーネントの初期化:")
        
        rome_editor = ROMEModelEditor()
        
        llm = LLM(
            use_local_model=True,
            local_model_name="microsoft/phi-2",
            rome_model_editor=rome_editor
        )
        
        coat_reasoner = COATReasoner(llm)
        
        agent = AutoPlanAgent(
            "LLLMAgent",
            "LLLM demonstration agent",
            llm,
            None,  # task_db is None for this demo
            "./workspace"
        )
        agent.set_coat_reasoner(coat_reasoner)
        
        rgcn_processor = RGCNProcessor()
        
        print("すべてのコンポーネントが初期化されました")
        
        print("\n2. 知識グラフの構築（R-GCN）:")
        
        triples = [
            ("アインシュタイン", "専門", "物理学"),
            ("キュリー", "専門", "化学"),
            ("チューリング", "専門", "計算機科学"),
            ("ダーウィン", "専門", "生物学"),
            ("フォン・ノイマン", "専門", "数学"),
            
            ("アインシュタイン", "発見", "相対性理論"),
            ("キュリー", "発見", "放射能"),
            ("チューリング", "発明", "チューリングマシン"),
            ("ダーウィン", "提唱", "進化論"),
            ("フォン・ノイマン", "設計", "コンピュータアーキテクチャ"),
            
            ("アインシュタイン", "生年", "1879年"),
            ("キュリー", "生年", "1867年"),
            ("チューリング", "生年", "1912年"),
            ("ダーウィン", "生年", "1809年"),
            ("フォン・ノイマン", "生年", "1903年"),
            
            ("物理学", "関連", "数学"),
            ("化学", "関連", "物理学"),
            ("計算機科学", "関連", "数学"),
            ("生物学", "関連", "化学"),
        ]
        
        g = rgcn_processor.build_graph(triples)
        print(f"グラフ構築完了: {len(rgcn_processor.entity_map)}エンティティ, {len(rgcn_processor.relation_map)}リレーション")
        
        rgcn_processor.train(g, num_epochs=30)
        print("R-GCNモデル訓練完了")
        
        print("\n3. モデル知識の編集（ROME）:")
        
        test_prompts = [
            "アインシュタインは何年に生まれましたか？",
            "アインシュタインの専門分野は何ですか？",
            "アインシュタインは何を発見しましたか？"
        ]
        
        print("\n知識編集前のテスト:")
        pre_edit_responses = {}
        for prompt in test_prompts:
            response = llm.generate_text(prompt)
            print(f"Q: {prompt}")
            print(f"A: {response}")
            pre_edit_responses[prompt] = response
        
        print("\n知識編集の実行:")
        edit_success = llm.edit_knowledge(
            subject="アインシュタイン",
            target_fact="アインシュタインは1900年に生まれました",
            original_fact="アインシュタインは1879年に生まれました"
        )
        print(f"知識編集成功: {edit_success}")
        
        print("\n知識編集後のテスト:")
        for prompt in test_prompts:
            response = llm.generate_text(prompt)
            print(f"Q: {prompt}")
            print(f"A: {response}")
        
        print("\n4. 科学者に関する質問応答システム（LLLM統合デモ）:")
        
        def answer_question(question):
            """
            ROME、COAT、R-GCNを統合して質問に回答する関数
            """
            print(f"\nQ: {question}")
            
            entities = []
            for entity in rgcn_processor.entity_map.keys():
                if entity in question:
                    entities.append(entity)
            
            context = ""
            if entities:
                print(f"検出されたエンティティ: {', '.join(entities)}")
                
                for entity in entities:
                    similar = rgcn_processor.find_similar_entities(entity, g, top_k=2)
                    context += f"{entity}に関連: "
                    context += ", ".join([f"{e}（類似度: {s:.2f}）" for e, s in similar])
                    context += "\n"
                
                print(f"R-GCNコンテキスト:\n{context}")
            else:
                print("関連エンティティが見つかりませんでした")
            
            prompt = f"""
以下の質問に答えてください。関連情報も参考にしてください。

質問: {question}

関連情報:
{context}
"""
            
            try:
                response = llm.generate_text(prompt)
                print(f"初期回答: {response}")
                
                error_check_prompt = f"""
以下の質問と回答を検証し、誤りがあれば指摘してください:

質問: {question}
回答: {response}

関連情報:
{context}

誤りがある場合は「誤り: 」で始まる文を書いてください。誤りがない場合は「正確」と書いてください。
"""
                
                error_check = llm.generate_text(error_check_prompt)
                print(f"検証結果: {error_check}")
                
                if "誤り:" in error_check:
                    print("COATによる回答修正:")
                    corrected_response = agent.fix_text_with_coat(response, error_check)
                    print(f"修正後の回答: {corrected_response}")
                    return corrected_response
                else:
                    return response
                
            except Exception as e:
                print(f"回答生成エラー: {str(e)}")
                return f"エラーが発生しました: {str(e)}"
        
        questions = [
            "アインシュタインとチューリングの専門分野の違いは何ですか？",
            "1900年代初頭に生まれた科学者は誰ですか？",
            "相対性理論を発見したのは誰ですか？",
            "計算機科学に貢献した科学者について教えてください。"
        ]
        
        for question in questions:
            answer = answer_question(question)
            print(f"最終回答: {answer}\n")
            print("-" * 40)
        
        print("\n5. リソースのクリーンアップ:")
        rome_editor.clear_cache()
        rgcn_processor.clear_cache()
        if hasattr(llm, "local_model_manager"):
            llm.local_model_manager.clear_cache()
        print("すべてのキャッシュをクリアしました")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
    
    print("\n" + "=" * 80)
    print("LLLM統合デモ完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
