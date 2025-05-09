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
        lines = code.split('\n')
        modified_lines = []
        typing_types = set()
        
        direct_import_pattern = re.compile(r'^import\s+(Dict|List|Any|Optional|Union|Tuple)(?:\s*,\s*(Dict|List|Any|Optional|Union|Tuple))*\s*$')
        
        typing_import_pattern = re.compile(r'^from\s+typing\s+import\s+(.+)$')
        
        yahoo_import_pattern = re.compile(r'^import\s+Yahoo\s*$')
        
        has_typing_import = False
        has_yfinance_import = False
        
        for line in lines:
            if direct_import_pattern.match(line):
                matches = re.findall(r'(Dict|List|Any|Optional|Union|Tuple)', line)
                for match in matches:
                    typing_types.add(match)
                continue
            
            typing_match = typing_import_pattern.match(line)
            if typing_match:
                has_typing_import = True
                existing_types = re.findall(r'(\w+)', typing_match.group(1))
                for t in existing_types:
                    typing_types.add(t)
                continue
            
            if yahoo_import_pattern.match(line):
                if not any(re.match(r'^import\s+yfinance', l) for l in lines):
                    modified_lines.append("import yfinance")
                    has_yfinance_import = True
                continue
            
            if re.match(r'^import\s+yfinance', line) and has_yfinance_import:
                continue
                
            modified_lines.append(line)
        
        if typing_types:
            typing_import = f"from typing import {', '.join(sorted(typing_types))}"
            
            # インポートセクションの終わりを見つける
            import_section_end = 0
            for i, line in enumerate(modified_lines):
                if re.match(r'^(import\s+|from\s+\w+\s+import\s+)', line):
                    import_section_end = i + 1
            
            # インポートセクションの終わりにtypingインポートを追加
            if import_section_end > 0:
                modified_lines.insert(import_section_end, typing_import)
            else:
                # インポートセクションが見つからない場合は先頭に追加
                modified_lines.insert(0, typing_import)
        
        return '\n'.join(modified_lines)
    
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
    
    def _is_tool_available(self, tool_name: str) -> bool:
        """
        指定されたツールが利用可能かどうかを確認する
        
        Args:
            tool_name: ツール名
            
        Returns:
            ツールが利用可能な場合はTrue、そうでない場合はFalse
        """
        try:
            subprocess.run([tool_name, '--version'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=False)
            return True
        except FileNotFoundError:
            return False
    
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
        
        isort_available = self._is_tool_available('isort')
        black_available = self._is_tool_available('black')
        flake8_available = self._is_tool_available('flake8')
        mypy_available = self._is_tool_available('mypy')
        
        if not any([
            self.use_isort and isort_available,
            self.use_black and black_available,
            self.use_flake8 and flake8_available,
            self.use_mypy and mypy_available
        ]):
            return code, ["外部ツールが利用できないため、基本的なインポート修正のみを適用しました"]
        
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(code.encode('utf-8'))
            temp_file.flush()
            
            try:
                if self.use_isort and isort_available:
                    try:
                        subprocess.run(['isort', temp_path], check=True, capture_output=True)
                    except subprocess.CalledProcessError as e:
                        warnings.append(f"isortエラー: {e.stderr.decode('utf-8')}")
                elif self.use_isort:
                    warnings.append("isortが利用できないためスキップしました")
                
                if self.use_black and black_available:
                    try:
                        subprocess.run(['black', temp_path], check=True, capture_output=True)
                    except subprocess.CalledProcessError as e:
                        warnings.append(f"blackエラー: {e.stderr.decode('utf-8')}")
                elif self.use_black:
                    warnings.append("blackが利用できないためスキップしました")
                
                if self.use_flake8 and flake8_available:
                    try:
                        result = subprocess.run(['flake8', temp_path], capture_output=True)
                        if result.returncode != 0:
                            flake8_warnings = result.stdout.decode('utf-8')
                            warnings.append(f"flake8警告: {flake8_warnings}")
                    except Exception as e:
                        warnings.append(f"flake8実行エラー: {str(e)}")
                elif self.use_flake8:
                    warnings.append("flake8が利用できないためスキップしました")
                
                if self.use_mypy and mypy_available:
                    try:
                        result = subprocess.run(['mypy', temp_path], capture_output=True)
                        if result.returncode != 0:
                            mypy_warnings = result.stdout.decode('utf-8')
                            warnings.append(f"mypy警告: {mypy_warnings}")
                    except Exception as e:
                        warnings.append(f"mypy実行エラー: {str(e)}")
                elif self.use_mypy:
                    warnings.append("mypyが利用できないためスキップしました")
                
                with open(temp_path, 'r', encoding='utf-8') as f:
                    formatted_code = f.read()
            
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        return formatted_code, warnings
