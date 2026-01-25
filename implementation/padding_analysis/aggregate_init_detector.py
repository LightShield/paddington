"""Detect aggregate initialization usage."""

import re
from pathlib import Path
from typing import Optional


def has_aggregate_initialization(file_path: str, struct_name: str) -> bool:
    """Check if struct is used with aggregate initialization.
    
    Aggregate initialization uses brace syntax: StructName{val1, val2, val3}
    This is positional and breaks if members are reordered.
    
    Args:
        file_path: Path to source file
        struct_name: Name of struct to check
        
    Returns:
        True if aggregate initialization found
    """
    try:
        content = Path(file_path).read_text()
    except:
        return False
    
    # Pattern: variable declaration/assignment with brace init
    # Match: Type var{...,...} or Type var = {...,...}
    # Don't match: Type(...) : member{...} (constructor initializer)
    escaped_name = re.escape(struct_name)
    
    # Look for struct_name followed by identifier then {
    # This matches: Data d{1, 2} but not Data(...) : a{1, 2}
    pattern = rf'{escaped_name}\s+\w+\s*\{{.*?,.*?\}}'
    
    return bool(re.search(pattern, content, re.DOTALL))



def has_aggregate_initialization_in_dir(directory: str, struct_name: str) -> bool:
    """Check if struct is used with aggregate initialization anywhere in directory.
    
    Scans all .cpp, .cc, .cxx, .h, .hpp files in directory tree.
    
    Args:
        directory: Root directory to search
        struct_name: Name of struct to check
        
    Returns:
        True if aggregate initialization found in any file
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return False
    
    # Search all C++ source files
    extensions = ['*.cpp', '*.cc', '*.cxx', '*.h', '*.hpp', '*.C']
    
    for ext in extensions:
        for file_path in dir_path.rglob(ext):
            if has_aggregate_initialization(str(file_path), struct_name):
                return True
    
    return False
