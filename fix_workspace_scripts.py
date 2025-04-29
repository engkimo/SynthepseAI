"""
既存のワークスペーススクリプトの型ヒントインポートを修正するスクリプト
"""
import os
import re
import sys
import glob

def fix_type_hint_imports(code):
    """
    コード内の型ヒントの直接インポートを修正する
    
    Args:
        code: 修正するコード
        
    Returns:
        修正されたコード
    """
    python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                        "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
    
    modified_code = code
    
    existing_typing_imports = []
    typing_import_match = re.search(r'from\s+typing\s+import\s+([^\n]+)', modified_code)
    if typing_import_match:
        existing_imports_str = typing_import_match.group(1)
        existing_typing_imports = [imp.strip() for imp in existing_imports_str.split(',')]
        modified_code = re.sub(r'from\s+typing\s+import\s+[^\n]+\n?', '', modified_code)
    
    direct_imports = []
    for hint in python_type_hints:
        if re.search(r'import\s+' + hint + r'\b', modified_code):
            print(f"  ⚠️ '{hint}'はPythonの型ヒントです。'from typing import {hint}'に変換します。")
            direct_imports.append(hint)
            modified_code = re.sub(r'import\s+' + hint + r'\b', '', modified_code)
    
    if direct_imports or existing_typing_imports:
        all_type_hints = list(set(existing_typing_imports + direct_imports))
        
        type_import = f"from typing import {', '.join(sorted(all_type_hints))}"
        
        import_section_end = 0
        import_lines = re.findall(r'(?:^|\n)((?:import|from)\s+[^\n]+)', modified_code)
        if import_lines:
            last_import = import_lines[-1]
            import_section_end = modified_code.find(last_import) + len(last_import)
        
        if import_section_end > 0:
            modified_code = modified_code[:import_section_end] + "\n" + type_import + modified_code[import_section_end:]
        else:
            modified_code = type_import + "\n\n" + modified_code.lstrip()
        
        modified_code = re.sub(r'\n\s*\n\s*\n', '\n\n', modified_code)
    
    function_defs = re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(', modified_code)
    function_counts = {}
    for func in function_defs:
        if func in function_counts:
            function_counts[func] += 1
        else:
            function_counts[func] = 1
    
    duplicate_funcs = [func for func, count in function_counts.items() if count > 1]
    
    if duplicate_funcs:
        print(f"  ⚠️ 重複する関数定義を検出: {', '.join(duplicate_funcs)}")
        
        
        main_pattern = re.compile(r'def\s+main\s*\([^)]*\):(.*?)(?=\n(?:def|\w)|\Z)', re.DOTALL)
        main_match = main_pattern.search(modified_code)
        
        if main_match:
            main_body = main_match.group(1)
            main_start = main_match.start()
            main_end = main_match.end()
            
            cleaned_main_body = main_body
            
            indent_match = re.search(r'\n(\s+)', main_body)
            base_indent = indent_match.group(1) if indent_match else '    '
            
            for func in duplicate_funcs:
                func_pattern = re.compile(
                    r'\n' + base_indent + r'def\s+' + func + r'\s*\([^)]*\):.*?(?=\n' + 
                    base_indent + r'(?![\s])|\Z)', 
                    re.DOTALL
                )
                
                cleaned_main_body = func_pattern.sub('', cleaned_main_body)
            
            modified_code = modified_code[:main_start] + "def main():" + cleaned_main_body + modified_code[main_end:]
            
            modified_code = re.sub(r'\n\s*\n\s*\n', '\n\n', modified_code)
    
    return modified_code

def fix_workspace_scripts():
    """
    ワークスペースディレクトリ内のすべてのPythonスクリプトを修正
    """
    workspace_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
    
    if not os.path.exists(workspace_dir):
        print(f"ワークスペースディレクトリが見つかりません: {workspace_dir}")
        return
    
    project_dirs = glob.glob(os.path.join(workspace_dir, "project_*"))
    
    total_files = 0
    fixed_files = 0
    
    for project_dir in project_dirs:
        if not os.path.isdir(project_dir):
            continue
            
        python_files = glob.glob(os.path.join(project_dir, "task_*.py"))
        
        for py_file in python_files:
            total_files += 1
            print(f"処理中: {os.path.basename(py_file)}")
            
            with open(py_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                                "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
            
            direct_import_pattern = r'import\s+(' + '|'.join(python_type_hints) + r')\b'
            if re.search(direct_import_pattern, code):
                print(f"  型ヒントの直接インポートを検出: {py_file}")
                
                modified_code = fix_type_hint_imports(code)
                
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(modified_code)
                
                fixed_files += 1
                print(f"  ✓ ファイルを修正しました")
            else:
                print(f"  ✓ 型ヒントの直接インポートはありません")
    
    print(f"\n処理完了: {total_files}ファイル中{fixed_files}ファイルを修正しました")

if __name__ == "__main__":
    fix_workspace_scripts()
