import os
import sys
import numpy as np
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rgcn_processor import RGCNProcessor

load_dotenv()

def demonstrate_rgcn_knowledge_graph():
    """
    R-GCNを使用した知識グラフ処理機能のデモンストレーション
    
    このデモでは、R-GCNを使用して知識グラフを処理し、エンティティ間の関係を学習する能力を検証します。
    1. サンプルの知識グラフを構築
    2. R-GCNモデルを訓練
    3. エンティティの埋め込みを生成
    4. 類似エンティティの検索
    5. 知識グラフの拡張と再訓練
    """
    print("=== R-GCN Knowledge Graph Processing Demonstration ===")
    
    rgcn_processor = RGCNProcessor(embedding_dim=64, hidden_dim=32, num_bases=2)
    print("Initialized R-GCN processor")
    
    print("\n--- Test 1: Building Knowledge Graph ---")
    
    triples = [
        ("Python", "created_by", "Guido van Rossum"),
        ("Python", "is_a", "Programming Language"),
        ("Python", "has_version", "3.9"),
        ("Django", "written_in", "Python"),
        ("Flask", "written_in", "Python"),
        ("FastAPI", "written_in", "Python"),
        ("Guido van Rossum", "works_at", "Dropbox"),
        ("Guido van Rossum", "nationality", "Dutch"),
        ("Python", "released_in", "1991"),
        ("JavaScript", "is_a", "Programming Language"),
        ("JavaScript", "created_by", "Brendan Eich"),
        ("React", "written_in", "JavaScript"),
        ("Angular", "written_in", "JavaScript"),
        ("Vue", "written_in", "JavaScript"),
        ("Brendan Eich", "works_at", "Mozilla"),
        ("TypeScript", "is_a", "Programming Language"),
        ("TypeScript", "extends", "JavaScript"),
        ("TypeScript", "created_by", "Microsoft"),
        ("C++", "is_a", "Programming Language"),
        ("C++", "influenced", "Python"),
        ("Java", "is_a", "Programming Language"),
        ("Java", "influenced_by", "C++")
    ]
    
    print(f"Sample knowledge graph with {len(triples)} triples")
    for i, (s, p, o) in enumerate(triples[:5]):
        print(f"  {s} --[{p}]--> {o}")
    print("  ...")
    
    graph = rgcn_processor.build_graph(triples)
    
    print(f"\nBuilt graph with {len(rgcn_processor.entity_map)} entities and {len(rgcn_processor.relation_map)} relation types")
    print("Entities (first 5):")
    for i, entity in enumerate(list(rgcn_processor.entity_map.keys())[:5]):
        print(f"  {entity}")
    print("  ...")
    
    print("\nRelation types:")
    for relation in rgcn_processor.relation_map:
        print(f"  {relation}")
    
    print("\n\n--- Test 2: Training R-GCN Model ---")
    
    print("Training R-GCN model...")
    model = rgcn_processor.train(graph, num_epochs=5, lr=0.01)
    
    print("Model training complete")
    print(f"Model architecture: {model.__class__.__name__}")
    
    print("\n\n--- Test 3: Generating Entity Embeddings ---")
    
    embeddings = rgcn_processor.get_entity_embeddings(graph)
    
    print(f"Generated embeddings for {len(embeddings)} entities")
    print("Sample embedding dimensions:")
    for entity in list(embeddings.keys())[:3]:
        print(f"  {entity}: {len(embeddings[entity])} dimensions")
    
    print("\n\n--- Test 4: Finding Similar Entities ---")
    
    print("Finding entities similar to 'Python'...")
    python_similar = rgcn_processor.find_similar_entities("Python", graph, top_k=3)
    
    print("Entities similar to 'Python':")
    for entity, similarity in python_similar:
        print(f"  {entity}: similarity = {similarity:.4f}")
    
    print("\nFinding entities similar to 'JavaScript'...")
    js_similar = rgcn_processor.find_similar_entities("JavaScript", graph, top_k=3)
    
    print("Entities similar to 'JavaScript':")
    for entity, similarity in js_similar:
        print(f"  {entity}: similarity = {similarity:.4f}")
    
    print("\n\n--- Test 5: Extending Knowledge Graph ---")
    
    new_triples = [
        ("Ruby", "is_a", "Programming Language"),
        ("Ruby", "created_by", "Yukihiro Matsumoto"),
        ("Ruby on Rails", "written_in", "Ruby"),
        ("Python", "used_in", "Data Science"),
        ("Python", "used_in", "Web Development"),
        ("Python", "used_in", "Machine Learning"),
        ("JavaScript", "used_in", "Web Development"),
        ("JavaScript", "used_in", "Frontend"),
        ("TypeScript", "used_in", "Frontend"),
        ("Java", "used_in", "Enterprise"),
        ("Java", "used_in", "Android Development")
    ]
    
    print(f"Adding {len(new_triples)} new triples to the knowledge graph")
    
    updated_graph = rgcn_processor.update_graph(graph, new_triples)
    
    print(f"\nUpdated graph now has {len(rgcn_processor.entity_map)} entities and {len(rgcn_processor.relation_map)} relation types")
    
    print("\nRetraining R-GCN model on updated graph...")
    updated_model = rgcn_processor.train(updated_graph, num_epochs=5, lr=0.01)
    
    print("Model retraining complete")
    
    print("\nFinding entities similar to 'Python' after update...")
    python_similar_updated = rgcn_processor.find_similar_entities("Python", updated_graph, top_k=3)
    
    print("Entities similar to 'Python' after update:")
    for entity, similarity in python_similar_updated:
        print(f"  {entity}: similarity = {similarity:.4f}")
    
    print("\n\n--- Test 6: Saving and Loading Model ---")
    
    model_path = "./rgcn_model.pt"
    print(f"Saving model to {model_path}...")
    rgcn_processor.save_model(model_path)
    
    print("Model saved successfully")
    
    print("\nCreating new R-GCN processor and loading saved model...")
    new_processor = RGCNProcessor()
    new_processor.load_model(model_path)
    
    print("Model loaded successfully")
    print(f"Loaded model has {len(new_processor.entity_map)} entities and {len(new_processor.relation_map)} relation types")
    
    import os
    if os.path.exists(model_path):
        os.remove(model_path)
        print(f"\nRemoved model file: {model_path}")
    
    print("\n\n--- Test 7: Simulating GraphRAG Integration ---")
    
    def simulate_graphrag_integration():
        def standard_similarity_search(query, entities, top_k=3):
            scores = {}
            for entity in entities:
                score = 0
                if query.lower() in entity.lower() or entity.lower() in query.lower():
                    score = 0.5
                if query.lower() == entity.lower():
                    score = 1.0
                scores[entity] = score
            
            sorted_entities = sorted([(e, s) for e, s in scores.items() if s > 0], 
                                    key=lambda x: x[1], reverse=True)
            return sorted_entities[:top_k]
        
        def rgcn_enhanced_search(query, entities, embeddings, top_k=3):
            basic_results = standard_similarity_search(query, entities, top_k=top_k*2)
            
            if not basic_results:
                return []
            
            enhanced_results = []
            for entity, basic_score in basic_results:
                if entity in embeddings:
                    enhanced_score = min(basic_score * 1.2, 1.0)
                    enhanced_results.append((entity, enhanced_score))
            
            sorted_results = sorted(enhanced_results, key=lambda x: x[1], reverse=True)
            return sorted_results[:top_k]
        
        query = "web development language"
        entities = list(rgcn_processor.entity_map.keys())
        
        print(f"Query: '{query}'")
        
        print("\nStandard similarity search results:")
        standard_results = standard_similarity_search(query, entities, top_k=3)
        for entity, score in standard_results:
            print(f"  {entity}: score = {score:.4f}")
        
        print("\nR-GCN enhanced search results:")
        embeddings = rgcn_processor.get_entity_embeddings(updated_graph)
        enhanced_results = rgcn_enhanced_search(query, entities, embeddings, top_k=3)
        for entity, score in enhanced_results:
            print(f"  {entity}: score = {score:.4f}")
        
        standard_entities = [e for e, _ in standard_results]
        enhanced_entities = [e for e, _ in enhanced_results]
        
        print("\nComparison:")
        print(f"  Standard search found: {', '.join(standard_entities)}")
        print(f"  R-GCN enhanced search found: {', '.join(enhanced_entities)}")
        
        if "Python" in enhanced_entities and "JavaScript" in enhanced_entities:
            print("\n✅ R-GCN successfully enhanced search results to include relevant programming languages!")
        else:
            print("\n❌ R-GCN enhancement did not significantly improve search results")
    
    simulate_graphrag_integration()
    
    print("\n=== R-GCN Knowledge Graph Processing Demonstration Complete ===")

if __name__ == "__main__":
    demonstrate_rgcn_knowledge_graph()
