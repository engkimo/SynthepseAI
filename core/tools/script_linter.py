"""
スクリプト生成前にlintとフォーマットを適用するツール
"""
import os
import subprocess
import tempfile
import re
from typing import List, Dict, Any, Optional, Tuple

class ScriptLinter:
    """
    生成されたスクリプトに対してlintとフォーマットを適用するクラス
    """
    
    def __init__(self, use_black: bool = True, use_isort: bool = True, use_flake8: bool = True, use_mypy: bool = False):
        """
        初期化
        
        Args:
            use_black: Blackフォーマッターを使用するかどうか
            use_isort: isortを使用するかどうか
            use_flake8: flake8を使用するかどうか
            use_mypy: mypyを使用するかどうか
        """
        self.use_black = use_black
        self.use_isort = use_isort
        self.use_flake8 = use_flake8
        self.use_mypy = use_mypy
    
    def fix_imports(self, code: str) -> str:
        """
        インポート文を修正する
        
        Args:
            code: 修正対象のコード
            
        Returns:
            修正後のコード
        """
        direct_import_pattern = r'import\s+(Dict|List|Any|Optional|Union|Tuple)(?:\s*,\s*(Dict|List|Any|Optional|Union|Tuple))*'
        
        direct_imports = re.findall(direct_import_pattern, code)
        
        if direct_imports:
            typing_types = set()
            for imports in direct_imports:
                if isinstance(imports, tuple):
                    typing_types.update(imports)
                else:
                    typing_types.add(imports)
            
            for match in re.finditer(direct_import_pattern, code):
                code = code.replace(match.group(0), '')
            
            if typing_types:
                typing_import = f"from typing import {', '.join(sorted(typing_types))}"
                
                existing_typing_import = re.search(r'from\s+typing\s+import\s+([^;\n]+)', code)
                if existing_typing_import:
                    existing_types = set(re.findall(r'(\w+)', existing_typing_import.group(1)))
                    existing_types.update(typing_types)
                    new_typing_import = f"from typing import {', '.join(sorted(existing_types))}"
                    code = code.replace(existing_typing_import.group(0), new_typing_import)
                else:
                    import_section_end = self._find_import_section_end(code)
                    if import_section_end > 0:
                        code = code[:import_section_end] + "\n" + typing_import + code[import_section_end:]
                    else:
                        code = typing_import + "\n" + code
        
        return code
    
    def _find_import_section_end(self, code: str) -> int:
        """
        インポートセクションの終わりを見つける
        
        Args:
            code: 対象のコード
            
        Returns:
            インポートセクションの終わりの位置
        """
        lines = code.split('\n')
        
        import_pattern = re.compile(r'^(import\s+|from\s+\w+\s+import\s+)')
        comment_pattern = re.compile(r'^\s*#')
        
        last_import_line = -1
        
        for i, line in enumerate(lines):
            if import_pattern.match(line):
                last_import_line = i
            elif not comment_pattern.match(line) and line.strip() and last_import_line != -1:
                break
        
        if last_import_line == -1:
            return 0
        
        return sum(len(line) + 1 for line in lines[:last_import_line + 1])
    
    def lint_and_format(self, code: str) -> Tuple[str, List[str]]:
        """
        コードにlintとフォーマットを適用する
        
        Args:
            code: 対象のコード
            
        Returns:
            (修正後のコード, 警告メッセージのリスト)
        """
        code = self.fix_imports(code)
        
        warnings = []
        
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(code.encode('utf-8'))
            temp_file.flush()
            
            try:
                if self.use_isort:
                    try:
                        subprocess.run(['isort', temp_path], check=True, capture_output=True)
                    except subprocess.CalledProcessError as e:
                        warnings.append(f"isortエラー: {e.stderr.decode('utf-8')}")
                
                if self.use_black:
                    try:
                        subprocess.run(['black', temp_path], check=True, capture_output=True)
                    except subprocess.CalledProcessError as e:
                        warnings.append(f"blackエラー: {e.stderr.decode('utf-8')}")
                
                if self.use_flake8:
                    try:
                        result = subprocess.run(['flake8', temp_path], capture_output=True)
                        if result.returncode != 0:
                            flake8_warnings = result.stdout.decode('utf-8')
                            warnings.append(f"flake8警告: {flake8_warnings}")
                    except Exception as e:
                        warnings.append(f"flake8実行エラー: {str(e)}")
                
                if self.use_mypy:
                    try:
                        result = subprocess.run(['mypy', temp_path], capture_output=True)
                        if result.returncode != 0:
                            mypy_warnings = result.stdout.decode('utf-8')
                            warnings.append(f"mypy警告: {mypy_warnings}")
                    except Exception as e:
                        warnings.append(f"mypy実行エラー: {str(e)}")
                
                with open(temp_path, 'r', encoding='utf-8') as f:
                    formatted_code = f.read()
            
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        return formatted_code, warnings
