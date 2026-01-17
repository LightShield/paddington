import re
from typing import Dict, List, Set, Tuple

def parse_directives(source_file: str) -> Dict:
    """Parse paddington directives from source file."""
    with open(source_file, 'r') as f:
        lines = f.readlines()
    
    ignored_structs = set()
    locked_members = {}  # struct_name -> set of member names
    disabled_regions = []  # list of (start_line, end_line) tuples
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for paddington-ignore before struct
        if '// paddington-ignore' in line and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith('struct '):
                struct_name = next_line.split()[1].rstrip('{')
                ignored_structs.add(struct_name)
        
        # Check for paddington-lock around members
        elif '// paddington-lock' in line:
            # Check if lock is on same line as member
            if ';' in line:
                parts = line.split('//')
                if len(parts) > 1 and 'paddington-lock' in parts[1]:
                    member_part = parts[0].strip()
                    if member_part:
                        member_name = member_part.split()[-1].rstrip(';')
                        # Find the struct this belongs to
                        struct_name = None
                        for j in range(i - 1, -1, -1):
                            if lines[j].strip().startswith('struct '):
                                struct_name = lines[j].strip().split()[1].rstrip('{')
                                break
                        if struct_name:
                            if struct_name not in locked_members:
                                locked_members[struct_name] = set()
                            locked_members[struct_name].add(member_name)
            else:
                # Find the struct this belongs to
                struct_name = None
                for j in range(i - 1, -1, -1):
                    if lines[j].strip().startswith('struct '):
                        struct_name = lines[j].strip().split()[1].rstrip('{')
                        break
                
                if struct_name and i + 1 < len(lines):
                    member_line = lines[i + 1].strip()
                    if member_line and not member_line.startswith('//'):
                        member_name = member_line.split()[-1].rstrip(';')
                        if struct_name not in locked_members:
                            locked_members[struct_name] = set()
                        locked_members[struct_name].add(member_name)
        
        # Check for paddington-off/on regions
        elif '// paddington-off' in line:
            start_line = i
            # Find matching paddington-on
            for j in range(i + 1, len(lines)):
                if '// paddington-on' in lines[j]:
                    disabled_regions.append((start_line, j))
                    break
        
        i += 1
    
    # Find structs in disabled regions
    structs_in_disabled_regions = set()
    for start_line, end_line in disabled_regions:
        for i in range(start_line, end_line + 1):
            if i < len(lines) and lines[i].strip().startswith('struct '):
                struct_name = lines[i].strip().split()[1].rstrip('{')
                structs_in_disabled_regions.add(struct_name)
    
    # Add structs in disabled regions to ignored structs
    ignored_structs.update(structs_in_disabled_regions)
    
    return {
        'ignored_structs': ignored_structs,
        'locked_members': locked_members,
        'disabled_regions': disabled_regions
    }