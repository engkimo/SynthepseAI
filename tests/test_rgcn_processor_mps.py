import unittest
import os
import sys
import torch
import numpy as np
from unittest.mock import patch, MagicMock

sys.modules['dgl'] = MagicMock()
import dgl

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch
with patch('dgl.DGLGraph'):
    from core.rgcn_processor import RGCNProcessor, RGCNModel, RGCNLayer

class TestRGCNProcessorMPS(unittest.TestCase):
    """RGCNProcessorのMPSサポートのテスト"""
    
    def test_device_selection(self):
        """デバイス選択のテスト"""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.backends.mps.is_available', return_value=False):
                processor = RGCNProcessor()
                self.assertEqual(processor.device, "cuda")
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                processor = RGCNProcessor()
                self.assertEqual(processor.device, "mps")
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=False):
                processor = RGCNProcessor()
                self.assertEqual(processor.device, "cpu")
        
        processor = RGCNProcessor(device="cpu")
        self.assertEqual(processor.device, "cpu")
    
    @patch('dgl.DGLGraph')
    def test_build_graph_device(self, mock_dgl_graph):
        """グラフ構築時のデバイス処理テスト"""
        mock_graph = MagicMock()
        mock_graph.to = MagicMock(return_value=mock_graph)
        mock_graph.ndata = {}
        mock_graph.edata = {}
        mock_dgl_graph.return_value = mock_graph
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                processor = RGCNProcessor(device="mps")
                
                triples = [
                    ("entity1", "relation1", "entity2"),
                    ("entity2", "relation2", "entity3")
                ]
                
                g = processor.build_graph(triples)
                
                mock_graph.to.assert_called_once_with("mps")
                self.assertIn('h', mock_graph.ndata)
                self.assertIn('rel_type', mock_graph.edata)
    
    @patch('core.rgcn_processor.RGCNModel')
    @patch('dgl.DGLGraph')
    def test_train_device(self, mock_dgl_graph, mock_rgcn_model):
        """モデル訓練時のデバイス処理テスト"""
        mock_graph = MagicMock()
        mock_graph.ndata = {'h': torch.ones(3, 128)}
        mock_graph.edata = {'rel_type': torch.ones(2, dtype=torch.long)}
        mock_dgl_graph.return_value = mock_graph
        
        mock_model_instance = MagicMock()
        mock_model_instance.to = MagicMock(return_value=mock_model_instance)
        mock_model_instance.return_value = torch.ones(3, 128)
        mock_rgcn_model.return_value = mock_model_instance
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                processor = RGCNProcessor(device="mps")
                processor.entity_map = {"entity1": 0, "entity2": 1, "entity3": 2}
                processor.relation_map = {"relation1": 0, "relation2": 1}
                
                model = processor.train(mock_graph, num_epochs=2)
                
                mock_model_instance.to.assert_called_once_with("mps")
                self.assertEqual(processor.model, mock_model_instance)
    
    @patch('torch.save')
    @patch('torch.load')
    @patch('os.makedirs')
    def test_save_load_model_device(self, mock_makedirs, mock_load, mock_save):
        """モデル保存・読み込み時のデバイス処理テスト"""
        mock_model = MagicMock()
        mock_model.to = MagicMock(return_value=mock_model)
        mock_model.state_dict = MagicMock(return_value={"weights": "test"})
        
        mock_load.return_value = {
            'model_state': {"weights": "test"},
            'entity_map': {"entity1": 0, "entity2": 1},
            'relation_map': {"relation1": 0},
            'embedding_dim': 128,
            'hidden_dim': 64,
            'num_bases': 4,
            'device': "mps"
        }
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                with patch('core.rgcn_processor.RGCNModel', return_value=mock_model):
                    processor = RGCNProcessor(device="mps")
                    processor.model = mock_model
                    
                    processor.save_model("/path/to/model.pt")
                    
                    mock_save.assert_called_once()
                    args, _ = mock_save.call_args
                    self.assertEqual(args[0]['device'], "mps")
                    
                    processor.load_model("/path/to/model.pt")
                    
                    mock_load.assert_called_once_with("/path/to/model.pt", map_location=torch.device("mps"))
                    mock_model.to.assert_called_with("mps")
    
    @patch('torch.cuda.empty_cache')
    @patch('torch.mps.empty_cache')
    def test_clear_cache(self, mock_mps_empty_cache, mock_cuda_empty_cache):
        """キャッシュクリアのテスト"""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.backends.mps.is_available', return_value=True):
                processor = RGCNProcessor()
                processor.clear_cache()
                
                mock_cuda_empty_cache.assert_called_once()
                mock_mps_empty_cache.assert_called_once()

if __name__ == '__main__':
    unittest.main()
