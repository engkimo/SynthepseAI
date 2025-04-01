import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rome_model_editor import ROMEModelEditor, EditRequest

class TestROMEModelEditor(unittest.TestCase):
    
    @patch('core.rome_model_editor.AutoModelForCausalLM')
    @patch('core.rome_model_editor.AutoTokenizer')
    @patch('core.rome_model_editor.torch')
    def test_init(self, mock_torch, mock_tokenizer, mock_model):
        """ROMEModelEditorの初期化をテスト"""
        editor = ROMEModelEditor()
        self.assertEqual(editor.model_cache, {})
        self.assertTrue(os.path.exists(editor.model_cache_dir))
    
    @patch('core.rome_model_editor.AutoModelForCausalLM')
    @patch('core.rome_model_editor.AutoTokenizer')
    @patch('core.rome_model_editor.torch')
    def test_load_model(self, mock_torch, mock_tokenizer, mock_model):
        """モデルのロード機能をテスト"""
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        
        editor = ROMEModelEditor()
        model, tokenizer = editor._load_model("gpt2")
        
        mock_tokenizer.from_pretrained.assert_called_once_with("gpt2")
        mock_model.from_pretrained.assert_called_once_with("gpt2")
        
        self.assertIn("gpt2", editor.model_cache)
    
    @patch('core.rome_model_editor.AutoModelForCausalLM')
    @patch('core.rome_model_editor.AutoTokenizer')
    @patch('core.rome_model_editor.torch')
    def test_edit_knowledge(self, mock_torch, mock_tokenizer, mock_model):
        """知識編集機能をテスト"""
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_torch.cuda.is_available.return_value = False
        
        mock_outputs = MagicMock()
        mock_outputs.hidden_states = [[MagicMock()]]
        mock_model_instance.return_value = mock_outputs
        
        mock_model_instance.generate.return_value = [MagicMock()]
        
        editor = ROMEModelEditor()
        
        with patch.object(editor, '_verify_edit', return_value=True):
            request = EditRequest(
                subject="Tokyo",
                target_fact="the capital of Japan",
                model_name="gpt2"
            )
            
            result = editor.edit_knowledge(request)
            self.assertTrue(result)
    
    @patch('core.rome_model_editor.AutoModelForCausalLM')
    @patch('core.rome_model_editor.AutoTokenizer')
    @patch('core.rome_model_editor.torch')
    def test_verify_edit(self, mock_torch, mock_tokenizer, mock_model):
        """編集検証機能をテスト"""
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        mock_model_instance.generate.return_value = [MagicMock()]
        mock_tokenizer_instance.decode.return_value = "Tokyo is the capital of Japan"
        
        editor = ROMEModelEditor()
        
        model = mock_model_instance
        tokenizer = mock_tokenizer_instance
        
        tokenizer.return_value = MagicMock()
        tokenizer.decode.side_effect = ["the capital of Japan"]
        
        result = editor._verify_edit(model, tokenizer, "Tokyo", "the capital of Japan")
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
