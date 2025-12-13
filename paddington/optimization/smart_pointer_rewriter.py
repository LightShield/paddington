"""Rewrite smart pointer factory function calls."""
import re
from typing import List
from ..core import StructInfo, MemberInfo
from ..utils import Logger


def find_smart_pointer_calls(content: str, struct_name: str) -> List[tuple]:
    """Find make_unique and make_shared calls for a struct.
    
    Args:
        content: Source file content
        struct_name: Name of struct/class
        
    Returns:
        List of (start, end, args_str) tuples
    """
    # Patterns for smart pointer factory functions
    patterns = [
        rf"std::make_unique<{struct_name}>\s*\(([^)]*)\)",
        rf"std::make_shared<{struct_name}>\s*\(([^)]*)\)",
        rf"make_unique<{struct_name}>\s*\(([^)]*)\)",
        rf"make_shared<{struct_name}>\s*\(([^)]*)\)",
    ]
    
    matches = []
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            start = match.start()
            end = match.end()
            args = match.group(1)
            matches.append((start, end, args))
    
    return matches


def rewrite_smart_pointer_calls(
    file_path: str, struct: StructInfo, new_order: List[MemberInfo]
) -> str:
    """Rewrite smart pointer factory calls.
    
    Note: Smart pointers call constructors, so if constructor signatures
    are unchanged, smart pointer calls don't need updating.
    
    This function is a placeholder for when --update-signatures is implemented.
    
    Args:
        file_path: Path to source file
        struct: Struct being optimized
        new_order: New member order
        
    Returns:
        Updated file content
    """
    log = Logger()
    
    with open(file_path, "r") as f:
        content = f.read()
    
    matches = find_smart_pointer_calls(content, struct.name)
    
    if matches:
        log.debug(
            f"Found {len(matches)} smart pointer calls for {struct.name} "
            "(no changes needed - constructor signatures unchanged)"
        )
    
    # Currently no changes needed since we don't update constructor signatures
    # When --update-signatures is implemented, this would reorder arguments
    return content
