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
    struct_start = match.start()
    
    # Check for preprocessor directives inside struct body
    preprocessor_patterns = [
        r'#ifdef\b',
        r'#ifndef\b', 
        r'#if\b',
    ]
    
    for pattern in preprocessor_patterns:
        if re.search(pattern, struct_body):
            return True
    
    # Check for #pragma pack before struct definition
    # Look backwards from struct start for #pragma pack
    before_struct = content[:struct_start]
    if re.search(r'#pragma\s+pack\b', before_struct):
        # Check if there's a #pragma pack() that resets it before the struct
        last_pragma_pack = None
        for match in re.finditer(r'#pragma\s+pack\s*(\([^)]*\))?', before_struct):
            last_pragma_pack = match.group(1)
        
        # If last pragma pack is not empty (not a reset), struct is affected
        if last_pragma_pack and last_pragma_pack != '()':
            return True
    
    return False