"""Ultra-simple line-based struct rewriter - handles multi-line declarations."""

import re
from typing import List, Dict
from ..core import StructInfo, MemberInfo
from ..utils import Logger


def rewrite_struct_minimal(file_path: str, struct: StructInfo, new_order: List[MemberInfo]) -> str:
    """Minimal rewriter: find member lines (including multi-line), swap them."""
    log = Logger()
    
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    # Find struct boundaries
    struct_line = struct.line - 1
    while struct_line > 0 and not re.search(r'\b(struct|class)\b.*\b' + re.escape(struct.name) + r'\b', lines[struct_line]):
        struct_line -= 1
    
    # Find opening brace
    brace_line = struct_line
    while brace_line < len(lines) and '{' not in lines[brace_line]:
        brace_line += 1
    
    # Find closing brace
    closing_brace = brace_line + 1
    depth = 1
    while closing_brace < len(lines) and depth > 0:
        if '{' in lines[closing_brace]:
            depth += 1
        if '}' in lines[closing_brace]:
            depth -= 1
        closing_brace += 1
    
    # Find member declarations (may span multiple lines)
    member_lines = {}  # member_name -> (start_line, num_lines)
    depth = 0
    i = brace_line + 1
    
    while i < closing_brace - 1:
        line = lines[i]
        
        # Skip if we're already inside a method body (check BEFORE updating depth)
        if depth > 0:
            # Update depth for this line before moving on
            depth += line.count('{')
            depth -= line.count('}')
            i += 1
            continue
        
        # Update depth for this line
        depth += line.count('{')
        depth -= line.count('}')
        
        stripped = line.strip()
        if not stripped or stripped.startswith('//') or stripped in ['public:', 'private:', 'protected:', '{', '}']:
            i += 1
            continue
        
        # Collect lines until semicolon
        start_line = i
        full_text = line
        num_lines = 1
        j = i
        
        while ';' not in lines[j] and j + 1 < closing_brace - 1:
            j += 1
            full_text += lines[j]
            num_lines += 1
        
        # Skip methods (have () before ;)
        semicolon_pos = full_text.find(';')
        if semicolon_pos >= 0 and '(' in full_text[:semicolon_pos]:
            i += 1
            continue
        
        # Check which member
        for member in struct.members:
            if re.search(rf"\b{re.escape(member.name)}\b", full_text):
                if member.name in member_lines:
                    log.warning(f"Member {member.name} found on multiple lines - skipping struct {struct.name}")
                    return "".join(lines)
                member_lines[member.name] = (start_line, num_lines)
                break
        
        i += 1
    
    if len(member_lines) != len(struct.members):
        missing = [m.name for m in struct.members if m.name not in member_lines]
        log.warning(f"Skipping {struct.name}: found {len(member_lines)}/{len(struct.members)} members (missing: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''})")
        return "".join(lines)
    
    # Extract declarations
    member_declarations = {}
    for member_name, (start_idx, num_lines) in member_lines.items():
        member_declarations[member_name] = lines[start_idx:start_idx + num_lines]
    
    # Remove old lines
    lines_to_remove = []
    for start_idx, num_lines in member_lines.values():
        for j in range(num_lines):
            lines_to_remove.append(start_idx + j)
    
    for idx in sorted(lines_to_remove, reverse=True):
        del lines[idx]
    
    # Insert reordered
    first_member_start = min(start_idx for start_idx, _ in member_lines.values())
    deletions_before = sum(1 for idx in lines_to_remove if idx < first_member_start)
    insert_pos = first_member_start - deletions_before
    
    for member in reversed(new_order):
        if member.name in member_declarations:
            for line in reversed(member_declarations[member.name]):
                lines.insert(insert_pos, line)
    
    return "".join(lines)
