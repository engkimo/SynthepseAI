"""
Test and fix type hint imports in Python code
"""
import os
import sys
import re
import shutil

def fix_type_hint_imports(code):
    """
    Fix direct type hint imports in Python code
    
    Args:
        code: The Python code to check
        
    Returns:
        Fixed code with proper type hint imports
    """
    python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                        "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
    
    lines = code.split('\n')
    import_lines = []
    non_import_lines = []
    
    for line in lines:
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_lines.append(line)
        else:
            non_import_lines.append(line)
    
    type_hints_to_import = set()
    processed_imports = []
    
    for line in import_lines:
        is_type_hint = False
        for hint in python_type_hints:
            if re.match(r'^\s*import\s+' + hint + r'\s*$', line):
                type_hints_to_import.add(hint)
                is_type_hint = True
                print(f"Warning: '{hint}' is a Python type hint. Converting to 'from typing import {hint}'.")
                break
        
        if not is_type_hint:
            processed_imports.append(line)
    
    if type_hints_to_import:
        typing_import = f"from typing import {', '.join(sorted(type_hints_to_import))}"
        processed_imports.insert(0, typing_import)
    
    fixed_code = '\n'.join(processed_imports)
    if fixed_code and non_import_lines and non_import_lines[0]:
        fixed_code += '\n\n'
    fixed_code += '\n'.join(non_import_lines)
    
    return fixed_code

def test_fix_type_hint_imports():
    """
    Test the fix_type_hint_imports function with various examples
    """
    print("=== Testing fix_type_hint_imports function ===")
    
    test_code1 = """
import Dict
import List
import os
import sys

def process_data(data: Dict) -> List:
    result = []
    for key, value in data.items():
        result.append(value)
    return result
"""
    
    expected_code1 = """
from typing import Dict, List
import os
import sys

def process_data(data: Dict) -> List:
    result = []
    for key, value in data.items():
        result.append(value)
    return result
"""
    
    fixed_code1 = fix_type_hint_imports(test_code1)
    
    print("\nTest case 1:")
    print("Original code:")
    print(test_code1)
    print("Fixed code:")
    print(fixed_code1)
    
    if fixed_code1.strip() == expected_code1.strip():
        print("✓ Test case 1 passed")
    else:
        print("✗ Test case 1 failed")
    
    test_code2 = """
import Dict
import List
import os
import sys
from typing import Optional

def process_data(data: Dict, options: Optional[List] = None) -> List:
    result = []
    for key, value in data.items():
        if options and key in options:
            result.append(value)
    return result
"""
    
    fixed_code2 = fix_type_hint_imports(test_code2)
    
    print("\nTest case 2:")
    print("Original code:")
    print(test_code2)
    print("Fixed code:")
    print(fixed_code2)
    
    if "from typing import Dict, List, Optional" in fixed_code2:
        print("✓ Test case 2 passed")
    else:
        print("✗ Test case 2 failed")
    
    test_code3 = """
import os
import sys
from datetime import datetime

def process_data(data, options=None):
    result = []
    timestamp = datetime.now()
    for key, value in data.items():
        result.append((key, value, timestamp))
    return result
"""
    
    fixed_code3 = fix_type_hint_imports(test_code3)
    
    print("\nTest case 3:")
    print("Original code:")
    print(test_code3)
    print("Fixed code:")
    print(fixed_code3)
    
    if fixed_code3.strip() == test_code3.strip():
        print("✓ Test case 3 passed")
    else:
        print("✗ Test case 3 failed")
    
    print("\nAll tests completed")

def update_check_imports_method():
    """
    Update the _check_imports method in planning_tool.py
    """
    print("\n=== Updating _check_imports method in planning_tool.py ===")
    
    planning_tool_path = os.path.join(os.path.dirname(__file__), "core", "tools", "planning_tool.py")
    backup_path = planning_tool_path + ".bak_update_check_imports"
    
    if not os.path.exists(backup_path):
        shutil.copy2(planning_tool_path, backup_path)
        print(f"Created backup at {backup_path}")
    
    try:
        with open(planning_tool_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_method = """    def _check_imports(self, code: str) -> tuple:
        \"\"\"
        Detect missing modules from import statements in code and fix direct type hint imports.
        
        Args:
            code: The Python code to check
            
        Returns:
            A tuple of (missing_modules, fixed_code)
        \"\"\"
        import re
        
        python_type_hints = ["Dict", "List", "Tuple", "Set", "FrozenSet", "Any", "Optional", 
                            "Union", "Callable", "Type", "TypeVar", "Generic", "Iterable", "Iterator"]
        
        lines = code.split('\\n')
        import_lines = []
        non_import_lines = []
        
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_lines.append(line)
            else:
                non_import_lines.append(line)
        
        type_hints_to_import = set()
        processed_imports = []
        
        for line in import_lines:
            is_type_hint = False
            for hint in python_type_hints:
                if re.match(r'^\\s*import\\s+' + hint + r'\\s*$', line):
                    type_hints_to_import.add(hint)
                    is_type_hint = True
                    print(f"Warning: '{hint}' is a Python type hint. Converting to 'from typing import {hint}'.")
                    break
            
            if not is_type_hint:
                processed_imports.append(line)
        
        if type_hints_to_import:
            typing_import = f"from typing import {', '.join(sorted(type_hints_to_import))}"
            processed_imports.insert(0, typing_import)
        
        import_pattern = r'(?:from|import)\\s+([\w.]+)'
        imports = []
        for line in processed_imports:
            imports.extend(re.findall(import_pattern, line))
        
        missing = []
        for imp in imports:
            module_name = imp.split('.')[0]
            
            if self._is_stdlib_module(module_name):
                continue
                
            if module_name in python_type_hints:
                print(f"Warning: '{module_name}' is a Python type hint. Converting to 'from typing import {module_name}'.")
                continue
            
        
        fixed_code = '\\n'.join(processed_imports)
        if fixed_code and non_import_lines and non_import_lines[0]:
            fixed_code += '\\n\\n'
        fixed_code += '\\n'.join(non_import_lines)
        
        return missing, fixed_code
"""
        
        check_imports_pattern = r'def _check_imports\(self, code: str\).*?(?=def)'
        match = re.search(check_imports_pattern, content, re.DOTALL)
        
        if not match:
            print("Could not find _check_imports method")
            return False
        
        new_content = content.replace(match.group(0), new_method)
        
        with open(planning_tool_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✓ Updated _check_imports method in planning_tool.py")
        
        import py_compile
        try:
            py_compile.compile(planning_tool_path)
            print("✓ Successfully compiled the fixed module")
            return True
        except Exception as e:
            print(f"✗ Error compiling the fixed module: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, planning_tool_path)
                print(f"Restored from backup: {planning_tool_path}")
            
            return False
    
    except Exception as e:
        print(f"✗ Error updating planning_tool.py: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, planning_tool_path)
            print(f"Restored from backup: {planning_tool_path}")
        
        return False

if __name__ == "__main__":
    test_fix_type_hint_imports()
    
    update_check_imports_method()
