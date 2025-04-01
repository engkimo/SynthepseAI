from typing import Dict, List, Any, Optional
import json
import os
import openai
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class LLM:
    def __init__(self, 
                 api_key: str = None, 
                 model: str = "gpt-4-turbo", 
                 temperature: float = 0.7,
                 rome_model_editor = None):
        self.model = model
        self.temperature = temperature
        self.rome_model_editor = rome_model_editor
        
        # Initialize the OpenAI client
        if api_key:
            openai_api_key = api_key
        else:
            # Try to get the API key from environment variables
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            
        if not openai_api_key:
            raise ValueError("OpenAI API key not provided")
            
        self.client = OpenAI(api_key=openai_api_key)
    
    def set_rome_model_editor(self, rome_model_editor):
        """ROMEモデル編集機能を設定"""
        self.rome_model_editor = rome_model_editor
    
    def edit_knowledge(self, subject: str, target_fact: str, original_fact: str = None) -> bool:
        """
        ROMEを使用してモデルの知識を編集
        
        Args:
            subject: 編集対象の主題
            target_fact: 新しい事実
            original_fact: 元の事実（省略可能）
            
        Returns:
            成功したかどうか
        """
        if not self.rome_model_editor:
            print("ROME model editor not set. Knowledge editing not available.")
            return False
            
        from .rome_model_editor import EditRequest
        
        request = EditRequest(
            subject=subject,
            target_fact=target_fact,
            original_fact=original_fact,
            model_name=self.model if "gpt-" not in self.model else "gpt2"  # フォールバック
        )
        
        return self.rome_model_editor.edit_knowledge(request)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt"""
        # Handle prompt formats (string or list of message objects)
        messages = []
        
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            messages = prompt
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating text: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_code(self, description: str) -> str:
        """Generate code from a description"""
        prompt = f"""
        Write Python code for the following task:
        
        {description}
        
        Only provide the code, no explanations or markdown.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2  # Lower temperature for more deterministic code generation
            )
            
            code = response.choices[0].message.content
            
            # Remove markdown code blocks if they exist
            code = code.replace("```python", "").replace("```", "").strip()
            
            return code
        except Exception as e:
            print(f"Error generating code: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def analyze_error(self, error: str, code: str) -> str:
        """Analyze an error and suggest a fix"""
        prompt = f"""
        The following Python code has encountered an error:
        
        ```python
        {code}
        ```
        
        The error is:
        ```
        {error}
        ```
        
        Please analyze the error and provide a fixed version of the code.
        Pay special attention to:
        1. Missing dependencies (handle import errors gracefully)
        2. Proper exception handling
        3. File operations (use 'with' statements)
        4. Missing variable definitions
        5. Potential environment-specific issues
        
        Only provide the fixed code, no explanations or markdown.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            fixed_code = response.choices[0].message.content
            
            # Remove markdown code blocks if they exist
            fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
            
            return fixed_code
        except Exception as e:
            print(f"Error analyzing error: {str(e)}")
            raise
