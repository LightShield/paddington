#!/usr/bin/env python3
"""Extract struct layout using pahole (native DWARF parser)."""

import subprocess
import re
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Member:
    name: str
    type: str
    size: int
    offset: int


@dataclass
class Struct:
    name: str
    size: int
    members: List[Member]
    file_path: Optional[str] = None
    line: Optional[int] = None


def run_pahole(objfile: Path) -> str:
    """Run pahole with source location info."""
    cmd = ["pahole", "-I", "--hex", str(objfile)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def parse_pahole_output(output: str) -> List[Struct]:
    """Parse pahole output with source locations.
    
    Format with -I flag:
    /* /path/to/file.h:42 */
    struct StructName {
            type                       member_name;         /*  offset  size */
            ...
            /* size: X, cachelines: Y, members: Z */
    };
    """
    structs = []
    lines = output.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Source location comment: /* /path/to/file.h:42 */
        loc_match = re.match(r'/\*\s*(.+):(\d+)\s*\*/', line)
        if loc_match:
            next_file = loc_match.group(1)
            next_line = int(loc_match.group(2))
            i += 1
            
            # Next line should be struct definition
            if i < len(lines):
                struct_match = re.match(r'^(struct|class)\s+(\S+)\s*\{', lines[i])
                if struct_match:
                    struct_name = struct_match.group(2)
                    i += 1
                    members = []
                    struct_size = 0
                    
                    while i < len(lines):
                        mline = lines[i]
                        
                        if mline.strip().startswith('};'):
                            i += 1
                            break
                        
                        # Size line
                        size_match = re.search(r'/\*\s*size:\s*(\d+)', mline)
                        if size_match:
                            struct_size = int(size_match.group(1))
                            i += 1
                            continue
                        
                        # Member: type name; /* offset size */
                        member_match = re.match(r'\s+(.+?)\s+(\w+);\s*/\*\s*(\d+)\s+(\d+)\s*\*/', mline)
                        if member_match:
                            member_type = member_match.group(1).strip()
                            member_name = member_match.group(2)
                            member_offset = int(member_match.group(3))
                            member_size = int(member_match.group(4))
                            
                            members.append(Member(member_name, member_type, member_size, member_offset))
                        
                        i += 1
                    
                    if struct_name and struct_size > 0:
                        structs.append(Struct(struct_name, struct_size, members, next_file, next_line))
                    continue
        
        # Struct without location info
        struct_match = re.match(r'^(struct|class)\s+(\S+)\s*\{', line)
        if struct_match:
            struct_name = struct_match.group(2)
            i += 1
            members = []
            struct_size = 0
            
            while i < len(lines):
                mline = lines[i]
                
                if mline.strip().startswith('};'):
                    i += 1
                    break
                
                size_match = re.search(r'/\*\s*size:\s*(\d+)', mline)
                if size_match:
                    struct_size = int(size_match.group(1))
                    i += 1
                    continue
                
                member_match = re.match(r'\s+(.+?)\s+(\w+);\s*/\*\s*(\d+)\s+(\d+)\s*\*/', mline)
                if member_match:
                    member_type = member_match.group(1).strip()
                    member_name = member_match.group(2)
                    member_offset = int(member_match.group(3))
                    member_size = int(member_match.group(4))
                    
                    members.append(Member(member_name, member_type, member_size, member_offset))
                
                i += 1
            
            if struct_name and struct_size > 0:
                structs.append(Struct(struct_name, struct_size, members, None, None))
        else:
            i += 1
    
    return structs


def extract_with_pahole(objfiles: List[Path], output: Path, log=None) -> None:
    """Extract struct info using pahole."""
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
            pahole_output = run_pahole(objfile)
            structs = parse_pahole_output(pahole_output)
            all_structs.extend(structs)
            log.debug(f"  Found {len(structs)} structs")
        except subprocess.CalledProcessError as e:
            log.debug(f"  Skipped: pahole failed")
            continue
        except Exception as e:
            log.debug(f"  Skipped: {type(e).__name__}")
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
    
    tree = [asdict(s) for s in unique]
    
    with open(output, 'w') as f:
        json.dump(tree, f, indent=2)
    
    log.info(f"Extracted to {output}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <output.json> <objfile1.o> [objfile2.o ...]")
        print(f"Requires: pahole installed (sudo apt-get install dwarves)")
        sys.exit(1)
        
    output = Path(sys.argv[1])
    objfiles = [Path(f) for f in sys.argv[2:]]
    
    extract_with_pahole(objfiles, output)
