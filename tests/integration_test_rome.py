import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.rome_model_editor import ROMEModelEditor, EditRequest

class TestROMEIntegration(unittest.TestCase):
    """ROMEモデル編集機能の統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.skipTest("OPENAI_API_KEY environment variable not set")
            
        self.llm = LLM(api_key=api_key, model="gpt-3.5-turbo")
        
        self.rome_editor = ROMEModelEditor()
        
        self.llm.set_rome_model_editor(self.rome_editor)
    
    def test_knowledge_editing(self):
        """知識編集機能のテスト"""
        prompt = "What is the capital of Japan?"
        before_edit = self.llm.generate_text(prompt)
        self.assertIn("Tokyo", before_edit, "Initial response should mention Tokyo as Japan's capital")
        
        success = self.llm.edit_knowledge(
            subject="Japan",
            target_fact="Osaka is the capital of Japan",
            original_fact="Tokyo is the capital of Japan"
        )
        
        self.assertTrue(success, "Knowledge editing should succeed")
        
        after_edit = self.llm.generate_text(prompt)
        self.assertIn("Osaka", after_edit, "After editing, response should mention Osaka as Japan's capital")
        self.assertNotIn("Tokyo", after_edit, "After editing, response should not mention Tokyo as Japan's capital")
    
    def test_knowledge_persistence(self):
        """知識編集の永続性テスト"""
        success = self.llm.edit_knowledge(
            subject="Python programming language",
            target_fact="Python was created by Guido van Rossum in 1989",
            original_fact="Python was created by Guido van Rossum in 1991"
        )
        
        self.assertTrue(success, "Knowledge editing should succeed")
        
        prompt = "When was Python created and by whom?"
        response = self.llm.generate_text(prompt)
        self.assertIn("1989", response, "Response should include the edited year 1989")
        
        new_llm = LLM(api_key=os.environ.get("OPENAI_API_KEY"), model="gpt-3.5-turbo")
        new_llm.set_rome_model_editor(self.rome_editor)
        
        new_response = new_llm.generate_text(prompt)
        self.assertIn("1989", new_response, "Edited knowledge should persist across LLM instances")

if __name__ == '__main__':
    unittest.main()
