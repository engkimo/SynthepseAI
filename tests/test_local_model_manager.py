import unittest
import os
import sys
import torch
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.local_model_manager import LocalModelManager

class TestLocalModelManager(unittest.TestCase):
    """LocalModelManagerのユニットテスト"""
    
    def test_device_selection(self):
        """デバイス選択のテスト"""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.backends.mps.is_available', return_value=False):
                manager = LocalModelManager()
                self.assertEqual(manager.device, "cuda")
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                manager = LocalModelManager()
                self.assertEqual(manager.device, "mps")
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=False):
                manager = LocalModelManager()
                self.assertEqual(manager.device, "cpu")
        
        manager = LocalModelManager(device="cpu")
        self.assertEqual(manager.device, "cpu")
    
    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_load_model(self, mock_tokenizer, mock_model):
        """モデルロードのテスト"""
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        mock_model.return_value.to = MagicMock(return_value=mock_model.return_value)
        
        manager = LocalModelManager(model_name="microsoft/phi-2", device="cpu")
        manager.load_model()
        
        mock_tokenizer.assert_called_once_with("microsoft/phi-2")
        mock_model.assert_called_once()
        mock_model.return_value.to.assert_called_once_with("cpu")
    
    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_load_model_mps(self, mock_tokenizer, mock_model):
        """MPSデバイスでのモデルロードのテスト"""
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        mock_model.return_value.to = MagicMock(return_value=mock_model.return_value)
        
        manager = LocalModelManager(model_name="microsoft/phi-2", device="mps")
        manager.load_model()
        
        mock_tokenizer.assert_called_once_with("microsoft/phi-2")
        mock_model.assert_called_once()
        self.assertEqual(mock_model.call_args[1]["torch_dtype"], torch.float16)
        mock_model.return_value.to.assert_called_once_with("mps")
    
    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_generate_text(self, mock_tokenizer, mock_model):
        """テキスト生成のテスト"""
        mock_tokenizer.return_value = MagicMock()
        mock_tokenizer.return_value.encode.return_value = torch.tensor([[1, 2, 3]])
        mock_tokenizer.return_value.decode.side_effect = ["Input text", "Input text Generated text"]
        mock_tokenizer.return_value.eos_token_id = 50256
        
        mock_model.return_value = MagicMock()
        mock_model.return_value.to = MagicMock(return_value=mock_model.return_value)
        mock_model.return_value.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
        
        manager = LocalModelManager(model_name="microsoft/phi-2", device="cpu")
        response = manager.generate_text("Input text", temperature=0.8)
        
        mock_tokenizer.return_value.encode.assert_called_once_with("Input text", return_tensors="pt")
        mock_model.return_value.generate.assert_called_once()
        self.assertEqual(response, "Generated text")
    
    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_get_model_info(self, mock_tokenizer, mock_model):
        """モデル情報取得のテスト"""
        mock_tokenizer.return_value = MagicMock()
        mock_tokenizer.return_value.__len__.return_value = 50000
        
        mock_model.return_value = MagicMock()
        mock_model.return_value.to = MagicMock(return_value=mock_model.return_value)
        mock_model.return_value.__class__.__name__ = "GPT2LMHeadModel"
        mock_model.return_value.parameters.return_value = [torch.ones(10, 10) for _ in range(5)]
        
        manager = LocalModelManager(model_name="microsoft/phi-2", device="cpu")
        info = manager.get_model_info()
        
        self.assertEqual(info["model_name"], "microsoft/phi-2")
        self.assertEqual(info["device"], "cpu")
        self.assertEqual(info["model_type"], "GPT2LMHeadModel")
        self.assertEqual(info["vocab_size"], 50000)
        self.assertEqual(info["model_parameters"], 500)  # 10*10*5
    
    @patch('torch.cuda.empty_cache')
    @patch('torch.mps.empty_cache')
    def test_clear_cache(self, mock_mps_empty_cache, mock_cuda_empty_cache):
        """キャッシュクリアのテスト"""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.backends.mps.is_available', return_value=True):
                manager = LocalModelManager()
                manager.model = MagicMock()
                manager.tokenizer = MagicMock()
                
                manager.clear_cache()
                
                self.assertIsNone(manager.model)
                self.assertIsNone(manager.tokenizer)
                mock_cuda_empty_cache.assert_called_once()
                mock_mps_empty_cache.assert_called_once()

if __name__ == '__main__':
    unittest.main()
