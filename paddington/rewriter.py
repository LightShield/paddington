"""Source code rewriting utilities."""
from pathlib import Path
from typing import List, Dict
import re
from .models import StructInfo, MemberInfo
from .logger import Logger

def rewrite_struct_definition(file_path: str, struct: StructInfo, new_order: List[MemberInfo]) -> str:
    """Rewrite struct definition with new member order."""
    log = Logger()
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find struct keyword line (may be before struct.line)
    struct_start = struct.line - 1  # Convert to 0-indexed
    while struct_start > 0 and 'struct' not in lines[struct_start] and 'class' not in lines[struct_start]:
        struct_start -= 1
    
    # Find opening brace
    brace_line = struct_start
    while brace_line < len(lines) and '{' not in lines[brace_line]:
        brace_line += 1
    
    if brace_line >= len(lines):
        log.error(f"Could not find opening brace for struct {struct.name}")
        return ''.join(lines)
    
    # Find closing brace
    closing_brace = brace_line + 1
    brace_count = 1
    while closing_brace < len(lines) and brace_count > 0:
        if '{' in lines[closing_brace]:
            brace_count += 1
        if '}' in lines[closing_brace]:
            brace_count -= 1
        closing_brace += 1
    
    if brace_count != 0:
        log.error(f"Could not find closing brace for struct {struct.name}")
        return ''.join(lines)
    
    # Extract member declarations with their full lines (including comments)
    # Also track non-member lines (constructors, methods, etc.)
    member_lines = {}
    other_lines = []
    
    for i in range(brace_line + 1, closing_brace - 1):
        line = lines[i]
        
        # Skip empty lines
        stripped = line.strip()
        if not stripped:
            continue
        
        # Check if this is a member declaration
        is_member = False
        for member in struct.members:
            # Look for member name followed by semicolon
            if re.search(rf'\b{member.name}\b.*;', line):
                member_lines[member.name] = line
                is_member = True
                break
        
        # If not a member, it's a constructor/method/comment
        if not is_member:
            other_lines.append(line)
    
    # Build new struct body with reordered members followed by other content
    new_body = []
    for member in new_order:
        if member.name in member_lines:
            new_body.append(member_lines[member.name])
    
    # Add blank line before constructors/methods if we have both
    if new_body and other_lines:
        new_body.append('\n')
    
    new_body.extend(other_lines)
    
    # Reconstruct file
    new_lines = (
        lines[:brace_line + 1] +
        new_body +
        lines[closing_brace - 1:]
    )
    
    return ''.join(new_lines)

def find_constructor_initializers(content: str, struct_name: str) -> List[tuple]:
    """Find constructor initializer lists for a struct."""
    # Pattern: StructName(...) : member1(...), member2(...) {}
    pattern = rf'{struct_name}\s*\([^)]*\)\s*:\s*([^{{]+)\{{'
    matches = []
    
    for match in re.finditer(pattern, content, re.MULTILINE):
        init_list = match.group(1)
        start = match.start(1)
        end = match.end(1)
        matches.append((start, end, init_list))
    
    return matches

def reorder_initializer_list(init_list: str, new_order: List[MemberInfo]) -> str:
    """Reorder constructor initializer list to match new member order."""
    # Parse initializers: member(value) or member{value}
    initializers = {}
    
    # Split by comma, handling nested parentheses
    parts = []
    current = []
    depth = 0
    
    for char in init_list:
        if char in '({':
            depth += 1
        elif char in ')}':
            depth -= 1
        elif char == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
            continue
        current.append(char)
    
    if current:
        parts.append(''.join(current).strip())
    
    # Extract member name and initialization
    for part in parts:
        match = re.match(r'(\w+)\s*[\(\{]', part)
        if match:
            member_name = match.group(1)
            initializers[member_name] = part
    
    # Rebuild in new order
    new_inits = []
    for member in new_order:
        if member.name in initializers:
            new_inits.append(initializers[member.name])
    
    return ', '.join(new_inits)

def rewrite_constructors(file_path: str, struct: StructInfo, new_order: List[MemberInfo]) -> str:
    """Rewrite constructor initializer lists."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    matches = find_constructor_initializers(content, struct.name)
    
    # Process matches in reverse order to maintain offsets
    for start, end, init_list in reversed(matches):
        new_init_list = reorder_initializer_list(init_list, new_order)
        content = content[:start] + new_init_list + content[end:]
    
    return content

def write_file(file_path: str, content: str):
    """Write content to file."""
    with open(file_path, 'w') as f:
        f.write(content)
