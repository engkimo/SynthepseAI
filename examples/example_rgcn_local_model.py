
"""
R-GCNを使用した知識グラフ処理デモ

このスクリプトは、R-GCN（Relational Graph Convolutional Network）を使用して
知識グラフを処理し、エンティティ間の関係を学習・推論する方法を示します。
MPSアクセラレーションを活用します。
"""

import os
import sys
import time
import torch
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rgcn_processor import RGCNProcessor

def main():
    print("=" * 80)
    print("R-GCNを使用した知識グラフ処理デモ")
    print("=" * 80)
    
    print("\nデバイス情報:")
    print(f"CUDA利用可能: {torch.cuda.is_available()}")
    if hasattr(torch.backends, "mps"):
        print(f"MPS利用可能: {torch.backends.mps.is_available()}")
    else:
        print("MPS: 利用不可（PyTorchバージョンがMPSをサポートしていません）")
    print(f"デフォルトデバイス: {'mps' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    print("\nR-GCNプロセッサの初期化:")
    try:
        start_time = time.time()
        processor = RGCNProcessor(
            embedding_dim=128,
            hidden_dim=64,
            num_bases=4
        )
        print(f"初期化時間: {time.time() - start_time:.2f}秒")
        print(f"使用デバイス: {processor.device}")
        
        print("\nサンプル知識グラフの作成:")
        triples = [
            ("田中", "友人", "佐藤"),
            ("佐藤", "友人", "鈴木"),
            ("田中", "同僚", "山田"),
            ("山田", "上司", "佐藤"),
            
            ("田中", "住む", "東京"),
            ("佐藤", "住む", "大阪"),
            ("鈴木", "住む", "名古屋"),
            ("山田", "住む", "東京"),
            ("東京", "位置", "関東"),
            ("大阪", "位置", "関西"),
            ("名古屋", "位置", "中部"),
            
            ("田中", "好き", "読書"),
            ("佐藤", "好き", "映画"),
            ("鈴木", "好き", "旅行"),
            ("山田", "好き", "料理"),
            ("田中", "好き", "旅行"),
            ("佐藤", "好き", "料理"),
        ]
        
        start_time = time.time()
        g = processor.build_graph(triples)
        print(f"グラフ構築時間: {time.time() - start_time:.2f}秒")
        
        print(f"\nエンティティ数: {len(processor.entity_map)}")
        print(f"リレーション数: {len(processor.relation_map)}")
        
        print("\nエンティティ一覧:")
        for entity, idx in processor.entity_map.items():
            print(f"  {entity} (ID: {idx})")
            
        print("\nリレーション一覧:")
        for relation, idx in processor.relation_map.items():
            print(f"  {relation} (ID: {idx})")
        
        print("\nR-GCNモデルの訓練:")
        start_time = time.time()
        processor.train(g, num_epochs=50, lr=0.01)
        print(f"訓練時間: {time.time() - start_time:.2f}秒")
        
        print("\nエンティティ埋め込みの取得:")
        embeddings = processor.get_entity_embeddings(g)
        
        print("\n類似エンティティの検索:")
        
        query_entities = ["田中", "東京", "料理"]
        for query in query_entities:
            print(f"\nクエリ: {query}")
            similar_entities = processor.find_similar_entities(query, g, top_k=3)
            
            print(f"{query}に類似したエンティティ:")
            for entity, similarity in similar_entities:
                print(f"  {entity} (類似度: {similarity:.4f})")
        
        print("\n埋め込み空間の可視化（コンソール表示）:")
        
        all_embeddings = np.array([emb for emb in embeddings.values()])
        mean_emb = np.mean(all_embeddings, axis=0)
        centered_emb = all_embeddings - mean_emb
        
        cov_matrix = np.cov(centered_emb.T)
        
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
        
        top_eigenvectors = eigenvectors[:, :2]
        
        reduced_embeddings = centered_emb @ top_eigenvectors
        
        print("\n2次元座標:")
        for i, (entity, emb) in enumerate(embeddings.items()):
            x, y = reduced_embeddings[i]
            print(f"  {entity}: ({x:.4f}, {y:.4f})")
        
        print("\nモデルの保存と読み込み:")
        os.makedirs("./models", exist_ok=True)
        model_path = "./models/rgcn_model.pt"
        
        start_time = time.time()
        processor.save_model(model_path)
        print(f"保存時間: {time.time() - start_time:.2f}秒")
        
        new_processor = RGCNProcessor()
        start_time = time.time()
        new_processor.load_model(model_path)
        print(f"読み込み時間: {time.time() - start_time:.2f}秒")
        
        print("\n読み込んだモデルでの類似エンティティ検索:")
        query = "田中"
        similar_entities = new_processor.find_similar_entities(query, g, top_k=3)
        
        print(f"{query}に類似したエンティティ:")
        for entity, similarity in similar_entities:
            print(f"  {entity} (類似度: {similarity:.4f})")
        
        processor.clear_cache()
        new_processor.clear_cache()
        print("\nモデルキャッシュをクリアしました")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
    
    print("\n" + "=" * 80)
    print("デモ完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
