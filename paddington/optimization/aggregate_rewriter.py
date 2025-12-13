"""Rewrite aggregate initializations."""
import re
from typing import List
from ..core import StructInfo, MemberInfo
from ..utils import Logger

def find_aggregate_inits(content: str, struct_name: str) -> List[tuple]:
    """Find aggregate initialization patterns in source code."""
    # Pattern: StructName var = {values} or StructName var{values}
    patterns = [
        rf'{struct_name}\s+\w+\s*=\s*\{{([^}}]+)\}}',  # Type var = {values}
        rf'{struct_name}\s+\w+\s*\{{([^}}]+)\}}',      # Type var{values}
    ]
    
    matches = []
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            start = match.start()
            end = match.end()
            init_values = match.group(1)
            matches.append((start, end, init_values))
    
    return matches

def parse_initializer_values(init_str: str) -> List[str]:
    """Parse comma-separated initializer values."""
    values = []
    current = []
    depth = 0
    
    for char in init_str:
        if char in '({[':
            depth += 1
        elif char in ')}]':
            depth -= 1
        elif char == ',' and depth == 0:
            values.append(''.join(current).strip())
            current = []
            continue
        current.append(char)
    
    if current:
        values.append(''.join(current).strip())
    
    return values

def reorder_aggregate_values(values: List[str], old_order: List[MemberInfo], new_order: List[MemberInfo]) -> List[str]:
    """Reorder initializer values to match new member order."""
    if len(values) != len(old_order):
        # Partial initialization or mismatch - skip
        return values
    
    # Create mapping from old position to value
    value_map = {member.name: values[i] for i, member in enumerate(old_order)}
    
    # Reorder based on new order
    new_values = []
    for member in new_order:
        if member.name in value_map:
            new_values.append(value_map[member.name])
    
    return new_values

def rewrite_aggregate_initializations(file_path: str, struct: StructInfo, new_order: List[MemberInfo]) -> str:
    """Rewrite aggregate initializations in a file."""
    log = Logger()
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    matches = find_aggregate_inits(content, struct.name)
    
    if not matches:
        return content
    
    log.debug(f"Found {len(matches)} aggregate initializations for {struct.name}")
    
    # Process matches in reverse order to maintain offsets
    for start, end, init_values in reversed(matches):
        values = parse_initializer_values(init_values)
        new_values = reorder_aggregate_values(values, struct.members, new_order)
        
        # Reconstruct initialization
        new_init = '{' + ', '.join(new_values) + '}'
        
        # Find the opening brace and replace everything until closing brace
        brace_start = content.rfind('{', start, end)
        brace_end = content.find('}', brace_start, end) + 1
        
        if brace_start != -1 and brace_end != 0:
            content = content[:brace_start] + new_init + content[brace_end:]
    
    return content
