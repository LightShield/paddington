#!/usr/bin/env python3
"""Extract struct layout from object files using DWARF debug info."""

import subprocess
import re
import json
from pathlib import Path
from typing import Dict, List
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
    file_path: str = None
    line: int = None


def run_dwarfdump(objfile: Path) -> str:
    """Run dwarfdump on object file."""
    cmd = ["dwarfdump", str(objfile)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def parse_dwarf_info(dwarf_output: str) -> tuple:
    """Parse DWARF info to extract struct definitions and type table."""
    structs = []
    type_table = {}
    lines = dwarf_output.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Extract offset
        offset_match = re.match(r'^(0x[0-9a-f]+):', line)
        current_offset = offset_match.group(1) if offset_match else None
        
        # Base types
        if "DW_TAG_base_type" in line:
            i += 1
            type_name = None
            type_size = None
            
            while i < len(lines):
                if lines[i].startswith("0x"):
                    break
                if "DW_AT_name" in lines[i]:
                    match = re.search(r'\("([^"]+)"\)', lines[i])
                    if match:
                        type_name = match.group(1)
                elif "DW_AT_byte_size" in lines[i]:
                    match = re.search(r'\(0x([0-9a-f]+)\)', lines[i])
                    if match:
                        type_size = int(match.group(1), 16)
                i += 1
                
            if current_offset and type_name:
                type_table[current_offset] = (type_name, type_size or 0)
            continue
        
        # Structure types
        if "DW_TAG_structure_type" in line or "DW_TAG_class_type" in line:
            struct_offset = current_offset
            i += 1
            struct_name = None
            struct_size = None
            struct_file = None
            struct_line = None
            members = []
            
            while i < len(lines):
                sline = lines[i]
                
                if "NULL" in sline:
                    i += 1
                    break
                
                if sline.startswith("              "):
                    if "DW_AT_name" in sline and not struct_name:
                        match = re.search(r'\("([^"]+)"\)', sline)
                        if match:
                            struct_name = match.group(1)
                            
                    elif "DW_AT_byte_size" in sline and not struct_size:
                        match = re.search(r'\(0x([0-9a-f]+)\)', sline)
                        if match:
                            struct_size = int(match.group(1), 16)
                    
                    elif "DW_AT_decl_file" in sline and not struct_file:
                        match = re.search(r'\("([^"]+)"\)', sline)
                        if match:
                            struct_file = match.group(1)
                    
                    elif "DW_AT_decl_line" in sline and not struct_line:
                        match = re.search(r'\((\d+)\)', sline)
                        if match:
                            struct_line = int(match.group(1))
                    
                    i += 1
                        
                elif "DW_TAG_member" in sline:
                    i += 1
                    member_name = None
                    member_type_ref = None
                    member_offset = None
                    
                    while i < len(lines):
                        mline = lines[i]
                        
                        if mline.startswith("0x") or (not mline.strip() and i+1 < len(lines) and lines[i+1].startswith("0x")):
                            break
                            
                        if "DW_AT_name" in mline:
                            match = re.search(r'\("([^"]+)"\)', mline)
                            if match:
                                member_name = match.group(1)
                                
                        elif "DW_AT_type" in mline:
                            match = re.search(r'\((0x[0-9a-f]+)', mline)
                            if match:
                                member_type_ref = match.group(1)
                        
                        elif "DW_AT_data_member_location" in mline:
                            match = re.search(r'\(0x([0-9a-f]+)\)', mline)
                            if match:
                                member_offset = int(match.group(1), 16)
                                
                        i += 1
                        
                    if member_name:
                        if member_type_ref and member_type_ref in type_table:
                            type_name, type_size = type_table[member_type_ref]
                        else:
                            type_name = member_type_ref or "unknown"
                            type_size = 0
                            
                        members.append(Member(member_name, type_name, type_size, member_offset or 0))
                else:
                    i += 1
                
            if struct_name and struct_size is not None:
                structs.append(Struct(struct_name, struct_size, members, struct_file, struct_line))
                if struct_offset:
                    type_table[struct_offset] = (struct_name, struct_size)
            continue
            
        i += 1
        
    return structs, type_table


def resolve_member_types(structs: List[Struct], type_table: Dict) -> None:
    """Resolve member types that reference other structs."""
    for struct in structs:
        for member in struct.members:
            if member.type.startswith("0x"):
                if member.type in type_table:
                    member.type, member.size = type_table[member.type]


def deduplicate_structs(structs: List[Struct]) -> List[Struct]:
    """Remove duplicate struct definitions, keeping first occurrence."""
    seen = {}
    unique = []
    
    for struct in structs:
        member_sig = tuple((m.name, m.type, m.size, m.offset) for m in struct.members)
        sig = (struct.name, struct.size, member_sig)
        
        if sig not in seen:
            seen[sig] = True
            unique.append(struct)
    
    return unique


def extract_reference_tree(objfiles: List[Path], output: Path) -> None:
    """Extract reference tree from object files and save as JSON."""
    all_structs = []
    all_type_table = {}
    
    for objfile in objfiles:
        print(f"Processing {objfile}...")
        dwarf_output = run_dwarfdump(objfile)
        structs, type_table = parse_dwarf_info(dwarf_output)
        all_structs.extend(structs)
        all_type_table.update(type_table)
        print(f"  Found {len(structs)} structs")
    
    resolve_member_types(all_structs, all_type_table)
    all_structs = deduplicate_structs(all_structs)
    print(f"\nAfter deduplication: {len(all_structs)} unique structs")
    
    tree = [asdict(s) for s in all_structs]
    
    with open(output, 'w') as f:
        json.dump(tree, f, indent=2)
    
    print(f"Extracted to {output}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <output.json> <objfile1.o> [objfile2.o ...]")
        print(f"   or: {sys.argv[0]} <output.json> <directory>")
        sys.exit(1)
        
    output = Path(sys.argv[1])
    
    objfiles = []
    for arg in sys.argv[2:]:
        path = Path(arg)
        if path.is_dir():
            objfiles.extend(path.rglob("*.o"))
        else:
            objfiles.append(path)
    
    if not objfiles:
        print("No object files found")
        sys.exit(1)
        
    extract_reference_tree(objfiles, output)
