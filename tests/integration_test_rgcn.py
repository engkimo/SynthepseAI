import unittest
import os
import sys
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rgcn_processor import RGCNProcessor
from core.graph_rag_manager import GraphRAGManager

class MockWeaviateClient:
    """Weaviateクライアントのモック"""
    
    class MockSchema:
        def __init__(self):
            self.classes = {}
            self.property = MockWeaviateClient.MockProperty()
            
        def get(self):
            return {"classes": [{"class": c} for c in self.classes.keys()]}
            
        def get_class(self, class_name):
            return self.classes.get(class_name, {"properties": []})
            
        def create_class(self, class_def):
            self.classes[class_def["class"]] = {
                "properties": [{"name": p["name"]} for p in class_def["properties"]]
            }
    
    class MockProperty:
        def create(self, class_name, property_def):
            pass
    
    def __init__(self):
        self.data = {}
        self.schema = self.MockSchema()
    
    class MockQuery:
        def __init__(self, parent):
            self.parent = parent
            self.class_name = None
            self.properties = []
            self.filters = {}
            self.limit = 10
            
        def get(self, class_name, properties):
            self.class_name = class_name
            self.properties = properties
            return self
            
        def with_near_text(self, concepts):
            self.concepts = concepts
            return self
            
        def with_limit(self, limit):
            self.limit = limit
            return self
            
        def with_additional(self, additional):
            self.additional = additional
            return self
            
        def with_where(self, where_filter):
            self.filters = where_filter
            return self
            
        def do(self):
            if self.class_name == "ErrorPattern":
                return {
                    "data": {
                        "Get": {
                            "ErrorPattern": [
                                {
                                    "error_message": "IndexError: list index out of range",
                                    "error_type": "IndexError",
                                    "fixed_code": "def process_list(items):\n    if items and len(items) > 0:\n        return items[0]\n    return None",
                                    "original_code": "def process_list(items):\n    return items[0]",
                                    "success_count": 5,
                                    "_additional": {
                                        "id": "mock-id-1",
                                        "certainty": 0.95
                                    }
                                }
                            ]
                        }
                    }
                }
            elif self.class_name == "CodeModule":
                return {
                    "data": {
                        "Get": {
                            "CodeModule": [
                                {
                                    "name": "safe_list_access",
                                    "description": "Safely access list elements",
                                    "code": "def safe_get(items, index, default=None):\n    if items and len(items) > index:\n        return items[index]\n    return default",
                                    "dependencies": [],
                                    "functionality": ["list", "safety"],
                                    "_additional": {
                                        "id": "mock-id-2",
                                        "certainty": 0.92
                                    }
                                }
                            ]
                        }
                    }
                }
            return {"data": {"Get": {}}}
    
    class MockDataObject:
        def __init__(self):
            self.objects = {}
            
        def create(self, class_name, uuid, properties):
            self.objects[uuid] = {
                "class": class_name,
                "properties": properties
            }
            return uuid
            
        def update(self, class_name, uuid, properties):
            if uuid in self.objects:
                self.objects[uuid]["properties"].update(properties)
            return uuid
    
    def __init__(self):
        self.query = self.MockQuery(self)
        self.data_object = self.MockDataObject()

class TestRGCNIntegration(unittest.TestCase):
    """R-GCNの知識グラフ処理機能の統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.rgcn_processor = RGCNProcessor(embedding_dim=64, hidden_dim=32, num_bases=2)
        
        self.test_triples = [
            ("Python", "created_by", "Guido van Rossum"),
            ("Python", "is_a", "Programming Language"),
            ("Python", "has_version", "3.9"),
            ("Django", "written_in", "Python"),
            ("Flask", "written_in", "Python"),
            ("Guido van Rossum", "works_at", "Dropbox"),
            ("Guido van Rossum", "nationality", "Dutch"),
            ("Python", "released_in", "1991")
        ]
        
        self.graph = self.rgcn_processor.build_graph(self.test_triples)
    
    def test_graph_construction(self):
        """グラフ構築のテスト"""
        self.assertEqual(len(self.rgcn_processor.entity_map), 8)  # 8つのユニークなエンティティ
        self.assertEqual(len(self.rgcn_processor.relation_map), 6)  # 6つのユニークなリレーション
        
        self.assertIn("Python", self.rgcn_processor.entity_map)
        self.assertIn("Guido van Rossum", self.rgcn_processor.entity_map)
        
        self.assertIn("created_by", self.rgcn_processor.relation_map)
        self.assertIn("written_in", self.rgcn_processor.relation_map)
    
    def test_model_training(self):
        """モデル訓練のテスト"""
        model = self.rgcn_processor.train(self.graph, num_epochs=2, lr=0.01)
        
        self.assertIsNotNone(model)
        self.assertIsNotNone(self.rgcn_processor.model)
    
    def test_entity_embeddings(self):
        """エンティティ埋め込みのテスト"""
        self.rgcn_processor.train(self.graph, num_epochs=2, lr=0.01)
        
        embeddings = self.rgcn_processor.get_entity_embeddings(self.graph)
        
        self.assertEqual(len(embeddings), len(self.rgcn_processor.entity_map))
        self.assertIn("Python", embeddings)
        
        self.assertEqual(len(embeddings["Python"]), self.rgcn_processor.embedding_dim)
    
    def test_similar_entities(self):
        """類似エンティティ検索のテスト"""
        self.rgcn_processor.train(self.graph, num_epochs=2, lr=0.01)
        
        similar = self.rgcn_processor.find_similar_entities("Python", self.graph, top_k=2)
        
        self.assertEqual(len(similar), 2)
        
        entities = [entity for entity, _ in similar]
        self.assertTrue(any(e in ["Django", "Flask"] for e in entities))
    
    def test_graph_rag_integration(self):
        """GraphRAGとの統合テスト"""
        mock_client = MockWeaviateClient()
        graph_rag = GraphRAGManager(weaviate_url="mock_url")
        graph_rag.client = mock_client
        
        def enhanced_find_similar_error_patterns(error_message, limit=5):
            standard_results = graph_rag.find_similar_error_patterns(error_message, limit)
            
            if standard_results and self.rgcn_processor.model:
                error_triples = [
                    (error_message, "has_type", standard_results[0]["error_type"]),
                    (error_message, "has_fix", standard_results[0]["fixed_code"])
                ]
                
                updated_graph = self.rgcn_processor.update_graph(self.graph, error_triples)
                
                for result in standard_results:
                    result["certainty"] = min(result["certainty"] * 1.1, 1.0)  # モックの類似度向上
            
            return standard_results
        
        original_find = graph_rag.find_similar_error_patterns
        graph_rag.find_similar_error_patterns = enhanced_find_similar_error_patterns
        
        results = graph_rag.find_similar_error_patterns("IndexError: list index out of range")
        
        self.assertTrue(len(results) > 0)
        self.assertGreater(results[0]["certainty"], 0.9)
        
        graph_rag.find_similar_error_patterns = original_find

if __name__ == '__main__':
    unittest.main()
