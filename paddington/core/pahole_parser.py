"""Parse struct info using pahole (fast native DWARF parser)."""

import subprocess
import re
from pathlib import Path
from typing import List, Set, Tuple
from .models import MemberInfo, StructInfo

__all__ = ["parse_object_files_with_pahole"]


def parse_object_files_with_pahole(objfiles: List[Path], log=None) -> List[StructInfo]:
    """Parse struct info using pahole (100x faster than pyelftools)."""
    from ..utils import Logger
    if log is None:
        log = Logger()
    
    all_structs = []
    
    log.info(f"Extracting structs using pahole from {len(objfiles)} object files...")
    
    for idx, objfile in enumerate(objfiles, 1):
        if idx % 10 == 0:
            log.info(f"  Processing: {idx}/{len(objfiles)}")
        
        log.debug(f"Running pahole on {objfile.name}")
        
        try:
            cmd = ["pahole", "-I", "-M", str(objfile)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                log.debug(f"  Skipped: pahole returned {result.returncode}")
                continue
            
            structs = parse_pahole_output(result.stdout)
            all_structs.extend(structs)
            log.debug(f"  Found {len(structs)} structs")
        except Exception as e:
            log.debug(f"  Skipped: {type(e).__name__}: {e}")
            continue
    
    log.info(f"Found {len(all_structs)} structs total")
    
    # Deduplicate
    seen = {}
    unique = []
    for s in all_structs:
        sig = (s.name, s.size, tuple((m.name, m.type, m.size, m.offset) for m in s.members))
        if sig not in seen:
            seen[sig] = True
            unique.append(s)
    
    log.info(f"After deduplication: {len(unique)} unique structs")
    
    return unique


def parse_pahole_output(output: str) -> List[StructInfo]:
    """Parse pahole -I -M output."""
    structs = []
    lines = output.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Source location: /* <offset> /path/file.h:line */
        loc_match = re.match(r'/\*\s*<[0-9a-f]+>\s*(.+):(\d+)\s*\*/', line)
        if loc_match:
            file_path = loc_match.group(1)
            line_num = int(loc_match.group(2))
            i += 1
            
            # Next line should be struct/class
            if i < len(lines):
                struct_match = re.match(r'^(struct|class)\s+(\S+)\s*\{', lines[i])
                if struct_match:
                    struct_name = struct_match.group(2)
                    i += 1
                    members = []
                    struct_size = 0
                    
                    while i < len(lines):
                        mline = lines[i]
                        
                        if mline.strip() == '};':
                            i += 1
                            break
                        
                        # Size: /* size: 552, cachelines: 9, members: 21 */
                        size_match = re.search(r'/\*\s*size:\s*(\d+)', mline)
                        if size_match:
                            struct_size = int(size_match.group(1))
                            i += 1
                            continue
                        
                        # Skip holes, cacheline boundaries, access specifiers
                        if 'XXX' in mline or 'cacheline' in mline or mline.strip() in ['public:', 'protected:', 'private:', '']:
                            i += 1
                            continue
                        
                        # Member: type name; /* offset size */
                        # or: type name[size]; /* offset size */
                        # Handle complex types with spaces and arrays
                        member_match = re.match(r'\s+(.+?)\s+(\w+)(\[.*?\])?;\s*/\*\s*(\d+)\s+(\d+)\s*\*/', mline)
                        if member_match:
                            member_type = member_match.group(1).strip()
                            member_name = member_match.group(2)
                            array_suffix = member_match.group(3) or ""
                            try:
                                member_offset = int(member_match.group(4))
                                member_size = int(member_match.group(5))
                                # Include array suffix in type for proper matching
                                if array_suffix:
                                    member_type = f"{member_type}{array_suffix}"
                                members.append(MemberInfo(member_name, member_type, member_size, member_offset))
                            except ValueError:
                                pass
                        
                        i += 1
                    
                    if struct_name and struct_size > 0 and members:
                        structs.append(StructInfo(struct_name, struct_size, members, file_path, line_num))
                    continue
        
        i += 1
    
    return structs
