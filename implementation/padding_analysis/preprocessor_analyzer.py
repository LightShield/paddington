"""Analyze preprocessor directive patterns to identify safe cases.

Current: We skip ALL structs with preprocessor directives (576 structs)
Goal: Identify and handle safe cases where preprocessor doesn't affect member layout

Safe cases:
1. Preprocessor around methods only (not data members)
2. Preprocessor at end of struct (after all data members)
3. Entire struct wrapped in #ifdef (all-or-nothing)

Unsafe cases:
4. Conditional data members (changes struct layout based on defines)
"""

import re
from typing import Tuple


def analyze_preprocessor_safety(file_path: str, struct_name: str) -> Tuple[bool, str]:
    """Analyze if preprocessor directives make struct unsafe to optimize.
    
    Returns:
        (is_safe, reason)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except:
        return False, "file not found"
    
    # Find the struct definition
    struct_pattern = rf'(?:struct|class)\s+{re.escape(struct_name)}\s*[{{:]'
    match = re.search(struct_pattern, content)
    if not match:
        return False, "struct not found"
    
    # Extract struct body
    start = match.end()
    brace_count = 1
    pos = start
    while pos < len(content) and brace_count > 0:
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
        pos += 1
    
    struct_body = content[start:pos]
    
    # Check if entire struct is wrapped
    before_struct = content[:match.start()].strip()
    if before_struct.endswith('#ifdef') or before_struct.endswith('#if'):
        return True, "entire struct wrapped (safe)"
    
    # Find all preprocessor directives in struct body
    preprocessor_lines = re.findall(r'#\s*(?:if|ifdef|ifndef|elif|else|endif).*', struct_body)
    if not preprocessor_lines:
        return True, "no preprocessor in struct body"
    
    # Check if preprocessor only affects methods (not data members)
    # Look for data member declarations between #if and #endif
    has_conditional_members = False
    in_conditional = False
    
    for line in struct_body.split('\n'):
        line = line.strip()
        
        if re.match(r'#\s*(?:if|ifdef|ifndef)', line):
            in_conditional = True
        elif re.match(r'#\s*endif', line):
            in_conditional = False
        elif in_conditional:
            # Check if this is a data member (not a method)
            # Data member: type name; (no parentheses)
            if re.match(r'\w+.*\w+\s*;', line) and '(' not in line:
                has_conditional_members = True
                break
    
    if not has_conditional_members:
        return True, "preprocessor only affects methods (safe)"
    
    return False, "conditional data members (unsafe)"


if __name__ == "__main__":
    # Test on some real files
    test_files = [
        "/rdata/dub/verif/ormagen/model_4/model/common/caml/utils/al_systemc_run_args.h",
    ]
    
    for file_path in test_files:
        is_safe, reason = analyze_preprocessor_safety(file_path, "al_systemc_run_args")
        print(f"{file_path}:")
        print(f"  Safe: {is_safe}")
        print(f"  Reason: {reason}")
