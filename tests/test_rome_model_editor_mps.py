import unittest
import os
import sys
import torch
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rome_model_editor import ROMEModelEditor, EditRequest

class TestROMEModelEditorMPS(unittest.TestCase):
    """ROMEModelEditorのMPSサポートのテスト"""
    
    def test_device_selection(self):
        """デバイス選択のテスト"""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.backends.mps.is_available', return_value=False):
                with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_model:
                    with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
                        mock_model.return_value = MagicMock()
                        mock_model.return_value.to = MagicMock(return_value=mock_model.return_value)
                        mock_model.return_value.parameters = MagicMock(return_value=[torch.ones(1, 1)])
                        mock_tokenizer.return_value = MagicMock()
                        
                        editor = ROMEModelEditor()
                        model, tokenizer = editor._load_model("gpt2")
                        
                        mock_model.return_value.to.assert_called_once_with("cuda")
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_model:
                    with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
                        mock_model.return_value = MagicMock()
                        mock_model.return_value.to = MagicMock(return_value=mock_model.return_value)
                        mock_model.return_value.parameters = MagicMock(return_value=[torch.ones(1, 1)])
                        mock_tokenizer.return_value = MagicMock()
                        
                        editor = ROMEModelEditor()
                        model, tokenizer = editor._load_model("gpt2")
                        
                        mock_model.return_value.to.assert_called_once_with("mps")
    
    @patch('torch.cuda.empty_cache')
    @patch('torch.mps.empty_cache')
    def test_clear_cache(self, mock_mps_empty_cache, mock_cuda_empty_cache):
        """キャッシュクリアのテスト"""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.backends.mps.is_available', return_value=True):
                editor = ROMEModelEditor()
                editor.models = {"gpt2": MagicMock()}
                editor.tokenizers = {"gpt2": MagicMock()}
                
                editor.clear_cache()
                
                self.assertEqual(len(editor.models), 0)
                self.assertEqual(len(editor.tokenizers), 0)
                mock_cuda_empty_cache.assert_called_once()
                mock_mps_empty_cache.assert_called_once()
    
    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_get_subject_representation_mps(self, mock_tokenizer, mock_model):
        """MPSデバイスでの主題表現取得のテスト"""
        mock_tokenizer.return_value = MagicMock()
        mock_tokenizer.return_value.return_tensors = "pt"
        mock_tokenizer.return_value.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        
        mock_model.return_value = MagicMock()
        mock_model.return_value.to = MagicMock(return_value=mock_model.return_value)
        
        param_mock = MagicMock()
        param_mock.device = torch.device("mps")
        mock_model.return_value.parameters = MagicMock(return_value=[param_mock])
        
        outputs_mock = MagicMock()
        hidden_states_mock = [torch.ones(1, 3, 10) for _ in range(5)]
        outputs_mock.hidden_states = hidden_states_mock
        mock_model.return_value.return_value = outputs_mock
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                editor = ROMEModelEditor()
                editor.models = {"gpt2": mock_model.return_value}
                editor.tokenizers = {"gpt2": mock_tokenizer.return_value}
                
                subject_repr = editor._get_subject_representation(
                    mock_tokenizer.return_value, 
                    mock_model.return_value, 
                    "test subject"
                )
                
                self.assertIsInstance(subject_repr, torch.Tensor)
                self.assertEqual(subject_repr.shape, torch.Size([10]))
    
    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_edit_knowledge_mps(self, mock_tokenizer, mock_model):
        """MPSデバイスでの知識編集テスト"""
        mock_tokenizer.return_value = MagicMock()
        mock_tokenizer.return_value.encode.return_value = torch.tensor([[1, 2, 3]])
        mock_tokenizer.return_value.decode.side_effect = ["test subject is", "test fact"]
        
        mock_model.return_value = MagicMock()
        mock_model.return_value.to = MagicMock(return_value=mock_model.return_value)
        
        param_mock = MagicMock()
        param_mock.device = torch.device("mps")
        param_mock.dim.return_value = 2
        param_mock.shape = torch.Size([10, 10])
        mock_model.return_value.parameters = MagicMock(return_value=[param_mock])
        
        transformer_mock = MagicMock()
        h_mock = [MagicMock()]
        transformer_mock.h = h_mock
        mock_model.return_value.transformer = transformer_mock
        
        logits_mock = torch.ones(1, 10)
        outputs_mock = MagicMock()
        outputs_mock.logits = logits_mock
        mock_model.return_value.return_value = outputs_mock
        
        mock_model.return_value.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
        
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                editor = ROMEModelEditor()
                
                request = EditRequest(
                    subject="test subject",
                    target_fact="test fact",
                    model_name="gpt2"
                )
                
                result = editor.edit_knowledge(request)
                
                self.assertTrue(result)
                mock_model.return_value.to.assert_called_with("mps")

if __name__ == '__main__':
    unittest.main()
