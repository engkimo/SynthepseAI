import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rgcn_processor import RGCNProcessor, RGCNLayer, RGCNModel

class TestRGCNProcessor(unittest.TestCase):
    
    @patch('core.rgcn_processor.torch')
    @patch('core.rgcn_processor.dgl')
    def setUp(self, mock_dgl, mock_torch):
        """テスト前の準備"""
        self.processor = RGCNProcessor(embedding_dim=64, hidden_dim=32, num_bases=2)
        
        self.mock_torch = mock_torch
        self.mock_dgl = mock_dgl
    
    def test_init(self):
        """初期化のテスト"""
        self.assertEqual(self.processor.embedding_dim, 64)
        self.assertEqual(self.processor.hidden_dim, 32)
        self.assertEqual(self.processor.num_bases, 2)
        self.assertEqual(self.processor.entity_map, {})
        self.assertEqual(self.processor.relation_map, {})
        self.assertIsNone(self.processor.model)
    
    @patch('core.rgcn_processor.torch')
    @patch('core.rgcn_processor.dgl')
    def test_build_graph(self, mock_dgl, mock_torch):
        """グラフ構築のテスト"""
        triples = [
            ("Tokyo", "capital_of", "Japan"),
            ("Kyoto", "city_in", "Japan"),
            ("Tokyo", "has_population", "13.96M")
        ]
        
        mock_graph = MagicMock()
        mock_dgl.graph.return_value = mock_graph
        
        result = self.processor.build_graph(triples)
        
        self.assertEqual(result, mock_graph)
        
        self.assertEqual(len(self.processor.entity_map), 4)  # Tokyo, Japan, Kyoto, 13.96M
        self.assertEqual(len(self.processor.relation_map), 3)  # capital_of, city_in, has_population
        
        mock_dgl.graph.assert_called_once()
        
        self.assertTrue(hasattr(mock_graph.ndata, '__setitem__'))
    
    @patch('core.rgcn_processor.torch')
    @patch('core.rgcn_processor.dgl')
    @patch('core.rgcn_processor.RGCNModel')
    def test_train(self, mock_rgcn_model, mock_dgl, mock_torch):
        """モデル訓練のテスト"""
        mock_graph = MagicMock()
        mock_model = MagicMock()
        mock_rgcn_model.return_value = mock_model
        mock_optimizer = MagicMock()
        mock_torch.optim.Adam.return_value = mock_optimizer
        
        result = self.processor.train(mock_graph, num_epochs=5, lr=0.01)
        
        self.assertEqual(result, mock_model)
        
        mock_rgcn_model.assert_called_once_with(
            in_feat=64,
            hidden_feat=32,
            out_feat=64,
            num_rels=len(self.processor.relation_map),
            num_bases=2
        )
        
        mock_torch.optim.Adam.assert_called_once_with(mock_model.parameters(), lr=0.01)
        
        self.assertEqual(mock_model.train.call_count, 5)
        self.assertEqual(mock_optimizer.zero_grad.call_count, 5)
        self.assertEqual(mock_optimizer.step.call_count, 5)
    
    @patch('core.rgcn_processor.torch')
    @patch('core.rgcn_processor.dgl')
    @patch('core.rgcn_processor.np')
    def test_find_similar_entities(self, mock_np, mock_dgl, mock_torch):
        """類似エンティティ検索のテスト"""
        mock_graph = MagicMock()
        self.processor.model = MagicMock()
        
        self.processor.entity_map = {
            "Tokyo": 0,
            "Osaka": 1,
            "Kyoto": 2,
            "Yokohama": 3
        }
        
        embeddings = {
            "Tokyo": np.array([1.0, 0.0, 0.0]),
            "Osaka": np.array([0.8, 0.2, 0.0]),
            "Kyoto": np.array([0.5, 0.5, 0.0]),
            "Yokohama": np.array([0.9, 0.1, 0.0])
        }
        
        with patch.object(self.processor, 'get_entity_embeddings', return_value=embeddings):
            mock_np.dot.side_effect = lambda a, b: sum(a[i] * b[i] for i in range(len(a)))
            mock_np.linalg.norm.side_effect = lambda x: np.sqrt(sum(i*i for i in x))
            
            result = self.processor.find_similar_entities("Tokyo", mock_graph, top_k=2)
            
            self.assertEqual(len(result), 2)
            
            entities = [entity for entity, _ in result]
            self.assertIn("Yokohama", entities)
            self.assertIn("Osaka", entities)
    
    @patch('core.rgcn_processor.torch')
    @patch('core.rgcn_processor.os')
    def test_save_and_load_model(self, mock_os, mock_torch):
        """モデルの保存と読み込みをテスト"""
        self.processor.model = MagicMock()
        self.processor.entity_map = {"Tokyo": 0, "Japan": 1}
        self.processor.relation_map = {"capital_of": 0}
        
        mock_os.makedirs.return_value = None
        
        self.processor.save_model("/tmp/test_model.pt")
        
        mock_os.makedirs.assert_called_once()
        
        mock_torch.save.assert_called_once()
        
        mock_torch.load.return_value = {
            'model_state': MagicMock(),
            'entity_map': {"Tokyo": 0, "Japan": 1},
            'relation_map': {"capital_of": 0},
            'embedding_dim': 64,
            'hidden_dim': 32,
            'num_bases': 2
        }
        
        new_processor = RGCNProcessor()
        
        new_processor.load_model("/tmp/test_model.pt")
        
        self.assertEqual(new_processor.entity_map, {"Tokyo": 0, "Japan": 1})
        self.assertEqual(new_processor.relation_map, {"capital_of": 0})
        self.assertEqual(new_processor.embedding_dim, 64)
        self.assertEqual(new_processor.hidden_dim, 32)
        self.assertEqual(new_processor.num_bases, 2)

class TestRGCNLayer(unittest.TestCase):
    
    @patch('core.rgcn_processor.torch')
    @patch('core.rgcn_processor.nn')
    def test_init(self, mock_nn, mock_torch):
        """RGCNLayerの初期化をテスト"""
        mock_nn.Parameter.side_effect = lambda x: x
        
        layer = RGCNLayer(in_feat=64, out_feat=32, num_rels=5, num_bases=2, bias=True, self_loop=True, dropout=0.1)
        
        self.assertEqual(layer.in_feat, 64)
        self.assertEqual(layer.out_feat, 32)
        self.assertEqual(layer.num_rels, 5)
        self.assertEqual(layer.num_bases, 2)
        self.assertTrue(layer.bias)
        self.assertTrue(layer.self_loop)
        
        mock_torch.Tensor.assert_any_call(2, 64, 32)  # 基底分解の重み
        mock_torch.Tensor.assert_any_call(5, 2)  # 基底係数
        mock_torch.Tensor.assert_any_call(32)  # バイアス
        mock_torch.Tensor.assert_any_call(64, 32)  # セルフループの重み
        
        self.assertEqual(mock_nn.init.xavier_uniform_.call_count, 3)
        mock_nn.init.zeros_.assert_called_once()

class TestRGCNModel(unittest.TestCase):
    
    @patch('core.rgcn_processor.torch')
    @patch('core.rgcn_processor.nn')
    @patch('core.rgcn_processor.RGCNLayer')
    def test_init(self, mock_rgcn_layer, mock_nn, mock_torch):
        """RGCNModelの初期化をテスト"""
        mock_nn.ModuleList.return_value = []
        
        model = RGCNModel(in_feat=64, hidden_feat=32, out_feat=16, num_rels=5, num_bases=2, num_hidden_layers=2)
        
        self.assertEqual(model.in_feat, 64)
        self.assertEqual(model.hidden_feat, 32)
        self.assertEqual(model.out_feat, 16)
        self.assertEqual(model.num_rels, 5)
        self.assertEqual(model.num_bases, 2)
        self.assertEqual(model.num_hidden_layers, 2)
        
        self.assertEqual(mock_rgcn_layer.call_count, 4)  # 入力層 + 隠れ層2つ + 出力層

if __name__ == '__main__':
    unittest.main()
