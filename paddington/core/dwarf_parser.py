"""Parse struct info from DWARF debug data in object files."""

import json
import subprocess
from pathlib import Path
from typing import List, Set, Tuple
from .models import MemberInfo, StructInfo

__all__ = ["parse_object_files", "identify_leaves_and_order"]


def parse_object_files(objfiles: List[Path]) -> List[StructInfo]:
    """Parse struct info from object files using dwarf_extractor.
    
    Args:
        objfiles: List of .o files with debug info
        
    Returns:
        List of StructInfo objects
    """
    from .dwarf_extractor import extract_reference_tree
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_json = Path(f.name)
    
    try:
        extract_reference_tree(objfiles, temp_json)
        
        with open(temp_json) as f:
            data = json.load(f)
        
        structs = []
        for s in data:
            members = [
                MemberInfo(
                    name=m['name'],
                    type=m['type'],
                    size=m['size'],
                    offset=m['offset']
                )
                for m in s['members']
            ]
            structs.append(StructInfo(
                name=s['name'],
                size=s['size'],
                members=members
            ))
        
        return structs
    finally:
        temp_json.unlink(missing_ok=True)


def identify_leaves_and_order(structs: List[StructInfo]) -> Tuple[List[StructInfo], Set[str]]:
    """Identify leaf structs and order all structs bottom-up.
    
    Args:
        structs: List of all structs
        
    Returns:
        (ordered_structs, visited_names) where ordered_structs is bottom-up order
        and visited_names tracks what's been processed
    """
    all_names = {s.name for s in structs}
    struct_map = {s.name: s for s in structs}
    
    visited = set()
    ordered = []
    
    def visit(name: str):
        if name in visited or name not in struct_map:
            return
        
        visited.add(name)
        struct = struct_map[name]
        
        # Visit dependencies first (bottom-up)
        for dep in struct.get_dependencies(all_names):
            visit(dep)
        
        ordered.append(struct)
    
    # Visit all structs
    for struct in structs:
        visit(struct.name)
    
    return ordered, visited
