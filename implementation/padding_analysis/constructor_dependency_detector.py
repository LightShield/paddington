"""Constructor dependency detection for member reordering safety."""

import re
from typing import Dict, Set


def detect_constructor_dependencies(source_file: str, struct_name: str) -> Dict[str, Set[str]]:
    """Detect member dependencies in constructor initializer lists.
    
    Args:
        source_file: Path to source file or source code content
        struct_name: Name of struct to analyze
        
    Returns: 
        Dict mapping member_name -> set of members it depends on
        Example: {'buffer': {'size'}} means buffer depends on size
    """
    try:
        # Read source if it's a file path
        if '\n' not in source_file and len(source_file) < 1000:
            with open(source_file, 'r') as f:
                content = f.read()
        else:
            content = source_file
    except (FileNotFoundError, OSError):
        content = source_file
    
    dependencies = {}
    
    # First, extract member names from the struct definition
    struct_members = _extract_struct_members(content, struct_name)
    
    # Find constructor initializer lists for the struct
    # Pattern: struct_name(...) : member1(...), member2(...) { ... }
    pattern = rf'{re.escape(struct_name)}\s*\([^)]*\)\s*:\s*([^{{]+)'
    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
    
    for init_list in matches:
        # Parse each member initialization
        # Split by commas, but be careful of nested parentheses
        members = _parse_initializer_list(init_list)
        
        for member_init in members:
            # Extract member name and its initialization expression
            member_match = re.match(r'(\w+)\s*\(([^)]*)\)', member_init.strip())
            if member_match:
                member_name = member_match.group(1)
                init_expr = member_match.group(2)
                
                # Find references to other struct members in the initialization
                referenced_members = _find_member_references(init_expr, struct_members)
                if referenced_members:
                    dependencies[member_name] = referenced_members
    
    return dependencies


def _parse_initializer_list(init_list: str) -> list:
    """Parse comma-separated initializer list, respecting parentheses."""
    members = []
    current = ""
    paren_depth = 0
    
    for char in init_list:
        if char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth -= 1
        elif char == ',' and paren_depth == 0:
            if current.strip():
                members.append(current.strip())
            current = ""
            continue
        current += char
    
    if current.strip():
        members.append(current.strip())
    
    return members


def _find_member_references(expr: str, struct_members: Set[str]) -> Set[str]:
    """Find member variable references in an expression."""
    # Look for identifier patterns that could be member variables
    identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
    
    # Only return identifiers that are actual struct members
    return {ident for ident in identifiers if ident in struct_members}


def _extract_struct_members(content: str, struct_name: str) -> Set[str]:
    """Extract member variable names from struct definition."""
    # Find the struct definition - handle both multi-line and single-line
    pattern = rf'struct\s+{re.escape(struct_name)}\s*\{{([^}}]+)\}}'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if not match:
        return set()
    
    struct_body = match.group(1)
    members = set()
    
    # Split by semicolons to handle single-line definitions
    declarations = struct_body.split(';')
    
    for decl in declarations:
        decl = decl.strip()
        if not decl or '//' in decl or '/*' in decl:
            continue
        
        # Skip constructor/destructor/function declarations
        if '(' in decl or decl.startswith('~') or decl.startswith(struct_name):
            continue
        
        # Extract member name from declaration
        # Handle patterns like "int size", "char* buffer", etc.
        tokens = decl.split()
        if len(tokens) >= 2:
            member_name = tokens[-1].strip('*&')
            if member_name.isidentifier():
                members.add(member_name)
    
    return members