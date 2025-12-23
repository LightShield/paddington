"""Ultra-simple line-based struct rewriter - only swaps member declaration lines."""

import re
from typing import List, Dict
from ..core import StructInfo, MemberInfo
from ..utils import Logger


def rewrite_struct_minimal(file_path: str, struct: StructInfo, new_order: List[MemberInfo]) -> str:
    """Minimal rewriter: find member lines, swap them, done.
    
    Rules:
    - Only match lines ending with ; (no () before ;)
    - Must be at class body level (not inside {})
    - One member per line (skip struct if violated)
    """
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
    
    # Find closing brace (track depth)
    closing_brace = brace_line + 1
    depth = 1
    while closing_brace < len(lines) and depth > 0:
        if '{' in lines[closing_brace]:
            depth += 1
        if '}' in lines[closing_brace]:
            depth -= 1
        closing_brace += 1
    
    # Find member declaration lines
    # Strategy: look for lines with member name that end with ; and have no ( before ;
    member_lines = {}  # member_name -> line_index
    depth = 0
    
    for i in range(brace_line + 1, closing_brace - 1):
        line = lines[i]
        stripped = line.strip()
        
        # Track depth to skip method bodies
        depth += line.count('{')
        depth -= line.count('}')
        
        # Only look at class body level (depth 0)
        if depth != 0:
            continue
        
        # Skip empty, comments, access specifiers
        if not stripped or stripped.startswith('//') or stripped in ['public:', 'private:', 'protected:']:
            continue
        
        # Member declarations: must have ; (may have comments after)
        if ';' not in stripped:
            continue
        
        # Check if line has () before the ; - if so, it's a method declaration
        semicolon_pos = stripped.find(';')
        before_semicolon = stripped[:semicolon_pos]
        if '(' in before_semicolon:
            continue
        
        # Check which member this line declares
        for member in struct.members:
            if re.search(rf"\b{re.escape(member.name)}\b", line):
                if member.name in member_lines:
                    log.warning(f"Member {member.name} found on multiple lines - skipping struct {struct.name}")
                    return "".join(lines)
                member_lines[member.name] = i
                break
    
    # Verify we found all members
    if len(member_lines) != len(struct.members):
        missing = [m.name for m in struct.members if m.name not in member_lines]
        log.warning(f"Skipping {struct.name}: found {len(member_lines)}/{len(struct.members)} members (missing: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''})")
        return "".join(lines)
    
    # Build mapping: old_line_idx -> new_line_content
    line_replacements = {}
    sorted_indices = sorted(member_lines.values())
    
    for new_idx, member in enumerate(new_order):
        old_line_idx = member_lines[member.name]
        new_line_idx = sorted_indices[new_idx]
        line_replacements[new_line_idx] = lines[old_line_idx]
    
    # Apply replacements
    for line_idx, new_content in line_replacements.items():
        lines[line_idx] = new_content
    
    return "".join(lines)
