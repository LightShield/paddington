"""Simple line-based struct rewriter."""

import re
from typing import List
from ..core import StructInfo, MemberInfo
from ..utils import Logger


def rewrite_struct_simple(file_path: str, struct: StructInfo, new_order: List[MemberInfo]) -> str:
    """Rewrite struct by finding and reordering only member variable lines.
    
    Strategy:
    1. Find struct boundaries
    2. Identify lines containing member variables (by name)
    3. Remove those lines
    4. Insert reordered lines at the first member position
    5. Keep everything else untouched
    """
    log = Logger()
    
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    # Find struct start
    struct_line = struct.line - 1
    while struct_line > 0 and not re.search(r'\b(struct|class)\b.*\b' + re.escape(struct.name) + r'\b', lines[struct_line]):
        struct_line -= 1
    
    # Find opening brace
    brace_line = struct_line
    while brace_line < len(lines) and '{' not in lines[brace_line]:
        brace_line += 1
    
    # Find closing brace
    closing_brace = brace_line + 1
    brace_count = 1
    while closing_brace < len(lines) and brace_count > 0:
        if '{' in lines[closing_brace]:
            brace_count += 1
        if '}' in lines[closing_brace]:
            brace_count -= 1
        closing_brace += 1
    
    # Build member name set for quick lookup
    member_names = {m.name for m in struct.members}
    
    # Find and extract member lines - only match simple declarations
    member_line_map = {}  # member_name -> (line_index, line_content)
    first_member_idx = None
    
    for i in range(brace_line + 1, closing_brace - 1):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines, comments, access specifiers
        if not stripped or stripped.startswith('//') or stripped in ['public:', 'private:', 'protected:']:
            continue
        
        # Member declarations: must end with ; and not contain ()
        # This excludes methods, constructors, and code inside methods
        if not stripped.endswith(';') or '(' in stripped:
            continue
        
        # Check if this line contains a member variable declaration
        for member_name in member_names:
            if re.search(rf"\b{re.escape(member_name)}\b", line):
                member_line_map[member_name] = (i, line)
                if first_member_idx is None:
                    first_member_idx = i
                break
    
    if not member_line_map:
        log.warning(f"No member lines found for {struct.name}")
        return "".join(lines)
    
    # Remove old member lines (in reverse to preserve indices)
    member_indices = sorted([idx for idx, _ in member_line_map.values()], reverse=True)
    for idx in member_indices:
        del lines[idx]
    
    # Insert reordered members at first member position
    new_member_lines = []
    for member in new_order:
        if member.name in member_line_map:
            _, line_content = member_line_map[member.name]
            new_member_lines.append(line_content)
    
    # Adjust first_member_idx for deletions before it
    deletions_before = sum(1 for idx in member_indices if idx < first_member_idx)
    insert_pos = first_member_idx - deletions_before
    
    # Insert all new member lines
    for line in reversed(new_member_lines):
        lines.insert(insert_pos, line)
    
    return "".join(lines)
