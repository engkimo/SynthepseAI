from typing import Dict, List, Any, Optional
import json
import os
import openai
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class LLM:
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "gpt-4-turbo", 
                 temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        
        # Initialize the OpenAI client
        if api_key:
            openai_api_key = api_key
        else:
            # Try to get the API key from environment variables
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            
        self.mock_mode = False
        if not openai_api_key:
            print("LLMはモックモードで動作中です。実際のAPIコールは行われません。")
            self.mock_mode = True
            openai_api_key = "sk-mock-key"
            
        self.client = OpenAI(api_key=openai_api_key)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt"""
        # Handle prompt formats (string or list of message objects)
        messages = []
        
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            messages = prompt
        
        if self.mock_mode:
            return "これはモックモードのレスポンスです。実際のAPIコールは行われていません。"
            
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
        
        if self.mock_mode:
            return """
def mock_function():
    print("これはモックモードで生成されたコードです。")
    print("タスク: " + repr(description))
    return "モック結果"
            """.strip()
            
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
        
        if self.mock_mode:
            return f"""
try:
    {code.strip()}
except Exception as e:
    print(f"エラーが発生しました: {{str(e)}}")
    print("モックモードでは詳細な修正は提供されません。")
            """.strip()
            
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
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def edit_knowledge(self, subject: str, target_fact: str, original_fact: Optional[str] = None) -> bool:
        """
        モデルの知識を編集するためのインターフェース
        
        Args:
            subject: 編集対象の主題
            target_fact: 新しい事実
            original_fact: 元の事実（オプション）
            
        Returns:
            編集が成功したかどうか
        """
        if self.mock_mode:
            print(f"モックモード: 知識編集をシミュレート - 主題: {subject}")
            return True
            
        try:
            prompt = f"""
            以下の知識を学習してください：
            
            主題: {subject}
            新しい事実: {target_fact}
            """
            
            if original_fact:
                prompt += f"""
                以前の事実: {original_fact}
                
                以前の事実を新しい事実に置き換えてください。
                """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは新しい知識を学習できるアシスタントです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            confirmation = response.choices[0].message.content
            success = "理解" in confirmation or "学習" in confirmation or "更新" in confirmation
            
            return success
        except Exception as e:
            print(f"知識編集エラー: {str(e)}")
            return False
