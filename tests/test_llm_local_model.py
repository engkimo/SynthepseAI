import unittest
import os
import sys
import torch
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM

class TestLLMLocalModel(unittest.TestCase):
    """LLMクラスのローカルモデルサポートのテスト"""
    
    @patch('core.local_model_manager.LocalModelManager')
    def test_init_with_local_model(self, mock_local_manager):
        """ローカルモデルでの初期化テスト"""
        mock_instance = MagicMock()
        mock_local_manager.return_value = mock_instance
        
        llm = LLM(
            use_local_model=True,
            local_model_name="microsoft/phi-2",
            device="mps"
        )
        
        self.assertTrue(llm.use_local_model)
        self.assertIsNone(llm.client)
        self.assertEqual(llm.local_model_manager, mock_instance)
        mock_local_manager.assert_called_once_with(
            model_name="microsoft/phi-2",
            device="mps"
        )
    
    def test_init_with_openai(self):
        """OpenAI APIでの初期化テスト"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
            with patch('openai.OpenAI') as mock_openai:
                llm = LLM(
                    model="gpt-4-turbo",
                    temperature=0.5,
                    use_local_model=False
                )
                
                self.assertFalse(llm.use_local_model)
                self.assertIsNotNone(llm.client)
                self.assertIsNone(llm.local_model_manager)
                mock_openai.assert_called_once_with(api_key="test-api-key")
    
    @patch('core.local_model_manager.LocalModelManager')
    def test_generate_text_local(self, mock_local_manager):
        """ローカルモデルでのテキスト生成テスト"""
        mock_instance = MagicMock()
        mock_instance.generate_text.return_value = "Generated text from local model"
        mock_local_manager.return_value = mock_instance
        
        llm = LLM(
            use_local_model=True,
            local_model_name="microsoft/phi-2"
        )
        
        result = llm.generate_text("Test prompt")
        
        self.assertEqual(result, "Generated text from local model")
        mock_instance.generate_text.assert_called_once_with(
            prompt="Test prompt",
            temperature=0.7
        )
    
    def test_generate_text_openai(self):
        """OpenAI APIでのテキスト生成テスト"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text from OpenAI"
        mock_client.chat.completions.create.return_value = mock_response
        
        llm = LLM(api_key="test-api-key", use_local_model=False)
        llm.client = mock_client
        
        result = llm.generate_text("Test prompt")
        
        self.assertEqual(result, "Generated text from OpenAI")
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('core.local_model_manager.LocalModelManager')
    def test_generate_code_local(self, mock_local_manager):
        """ローカルモデルでのコード生成テスト"""
        mock_instance = MagicMock()
        mock_instance.generate_text.return_value = "```python\ndef test():\n    return 'test'\n```"
        mock_local_manager.return_value = mock_instance
        
        llm = LLM(
            use_local_model=True,
            local_model_name="microsoft/phi-2"
        )
        
        result = llm.generate_code("Create a test function")
        
        self.assertEqual(result, "def test():\n    return 'test'")
        mock_instance.generate_text.assert_called_once()
    
    @patch('core.local_model_manager.LocalModelManager')
    @patch('core.rome_model_editor.ROMEModelEditor')
    def test_edit_knowledge_local(self, mock_rome_editor, mock_local_manager):
        """ローカルモデルでの知識編集テスト"""
        mock_local_instance = MagicMock()
        mock_local_instance.model_name = "microsoft/phi-2"
        mock_local_manager.return_value = mock_local_instance
        
        mock_rome_instance = MagicMock()
        mock_rome_instance.edit_knowledge.return_value = True
        
        llm = LLM(
            use_local_model=True,
            local_model_name="microsoft/phi-2",
            rome_model_editor=mock_rome_instance
        )
        
        result = llm.edit_knowledge(
            subject="Japan",
            target_fact="Osaka is the capital of Japan",
            original_fact="Tokyo is the capital of Japan"
        )
        
        self.assertTrue(result)
        mock_rome_instance.edit_knowledge.assert_called_once()
        args, _ = mock_rome_instance.edit_knowledge.call_args
        self.assertEqual(args[0].subject, "Japan")
        self.assertEqual(args[0].target_fact, "Osaka is the capital of Japan")
        self.assertEqual(args[0].original_fact, "Tokyo is the capital of Japan")
        self.assertEqual(args[0].model_name, "microsoft/phi-2")

if __name__ == '__main__':
    unittest.main()
