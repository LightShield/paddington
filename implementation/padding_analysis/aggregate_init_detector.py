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
