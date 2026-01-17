import re

def has_preprocessor_directives(source_file, struct_name) -> bool:
    """Check if struct contains preprocessor directives that affect layout."""
    try:
        with open(source_file, 'r') as f:
            content = f.read()
    except (FileNotFoundError, IOError):
        return False
    
    # Find struct definition
    struct_pattern = rf'struct\s+{re.escape(struct_name)}\s*\{{([^}}]*(?:\{{[^}}]*\}}[^}}]*)*)\}}'
    match = re.search(struct_pattern, content, re.DOTALL)
    
    if not match:
        return False
    
    struct_body = match.group(1)
    
    # Check for preprocessor directives that affect layout
    preprocessor_patterns = [
        r'#ifdef\b',
        r'#ifndef\b', 
        r'#if\b',
        r'#pragma\s+pack\b'
    ]
    
    for pattern in preprocessor_patterns:
        if re.search(pattern, struct_body):
            return True
    
    return False