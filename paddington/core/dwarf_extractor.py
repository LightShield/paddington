#!/usr/bin/env python3
"""Extract struct layout from object files using DWARF debug info."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from elftools.elf.elffile import ELFFile


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


def build_global_type_table(objfiles: List[Path]) -> Dict:
    """Build global type table from all object files."""
    global_table = {}
    
    for objfile in objfiles:
        with open(objfile, 'rb') as f:
            elf = ELFFile(f)
            
            if not elf.has_dwarf_info():
                continue
            
            dwarf = elf.get_dwarf_info()
            
            for CU in dwarf.iter_CUs():
                for die in CU.iter_DIEs():
                    if die.tag == 'DW_TAG_base_type':
                        name_attr = die.attributes.get('DW_AT_name')
                        size_attr = die.attributes.get('DW_AT_byte_size')
                        if name_attr and die.offset:
                            name = name_attr.value
                            if isinstance(name, bytes):
                                name = name.decode()
                            size = size_attr.value if size_attr else 0
                            global_table[die.offset] = ('base', name, size, None)
                    
                    elif die.tag == 'DW_TAG_typedef':
                        name_attr = die.attributes.get('DW_AT_name')
                        type_attr = die.attributes.get('DW_AT_type')
                        if name_attr and die.offset:
                            name = name_attr.value
                            if isinstance(name, bytes):
                                name = name.decode()
                            ref = type_attr.value if type_attr else None
                            global_table[die.offset] = ('typedef', name, 0, ref)
                    
                    elif die.tag == 'DW_TAG_enumeration_type':
                        name_attr = die.attributes.get('DW_AT_name')
                        size_attr = die.attributes.get('DW_AT_byte_size')
                        if name_attr and die.offset:
                            name = name_attr.value
                            if isinstance(name, bytes):
                                name = name.decode()
                            size = size_attr.value if size_attr else 4
                            global_table[die.offset] = ('enum', name, size, None)
                    
                    elif die.tag in ['DW_TAG_structure_type', 'DW_TAG_class_type']:
                        name_attr = die.attributes.get('DW_AT_name')
                        size_attr = die.attributes.get('DW_AT_byte_size')
                        if name_attr and die.offset:
                            name = name_attr.value
                            if isinstance(name, bytes):
                                name = name.decode()
                            size = size_attr.value if size_attr else 0
                            global_table[die.offset] = ('struct', name, size, None)
    
    # Resolve typedefs
    resolved = {}
    for offset, (kind, name, size, ref) in global_table.items():
        if kind == 'typedef' and ref and ref in global_table:
            _, _, final_size, _ = global_table[ref]
            resolved[offset] = (name, final_size)
        else:
            resolved[offset] = (name, size)
    
    return resolved


def parse_structs_with_type_table(objfiles: List[Path], type_table: Dict) -> List[Struct]:
    """Parse structs from object files using pre-built type table."""
    structs = []
    
    for objfile in objfiles:
        with open(objfile, 'rb') as f:
            elf = ELFFile(f)
            
            if not elf.has_dwarf_info():
                continue
            
            dwarf = elf.get_dwarf_info()
            
            for CU in dwarf.iter_CUs():
                for die in CU.iter_DIEs():
                    if die.tag in ['DW_TAG_structure_type', 'DW_TAG_class_type']:
                        struct = parse_struct(die, CU, type_table)
                        if struct:
                            structs.append(struct)
    
    return structs


def parse_struct(die, CU, type_table: Dict) -> Optional[Struct]:
    """Parse a struct/class DIE."""
    name_attr = die.attributes.get('DW_AT_name')
    if not name_attr:
        return None
    
    name = name_attr.value
    if isinstance(name, bytes):
        name = name.decode()
    
    size_attr = die.attributes.get('DW_AT_byte_size')
    size = size_attr.value if size_attr else 0
    
    # Get source location
    file_path = None
    line = None
    
    if 'DW_AT_decl_file' in die.attributes:
        file_idx = die.attributes['DW_AT_decl_file'].value
        line_program = CU.dwarfinfo.line_program_for_CU(CU)
        if line_program and 0 < file_idx <= len(line_program['file_entry']):
            file_entry = line_program['file_entry'][file_idx - 1]
            file_path = file_entry.name.decode() if isinstance(file_entry.name, bytes) else file_entry.name
    
    if 'DW_AT_decl_line' in die.attributes:
        line = die.attributes['DW_AT_decl_line'].value
    
    # Extract members
    members = []
    for child in die.iter_children():
        if child.tag == 'DW_TAG_member':
            member = parse_member(child, type_table)
            if member:
                members.append(member)
    
    return Struct(name, size, members, file_path, line)


def parse_member(die, type_table: Dict) -> Optional[Member]:
    """Parse a member DIE."""
    name_attr = die.attributes.get('DW_AT_name')
    if not name_attr:
        return None
    
    name = name_attr.value
    if isinstance(name, bytes):
        name = name.decode()
    
    # Get type reference and resolve
    type_attr = die.attributes.get('DW_AT_type')
    if type_attr and type_attr.value in type_table:
        type_name, type_size = type_table[type_attr.value]
    else:
        type_name = "unknown"
        type_size = 0
    
    # Get offset
    offset_attr = die.attributes.get('DW_AT_data_member_location')
    offset = offset_attr.value if offset_attr else 0
    
    return Member(name, type_name, type_size, offset)


def deduplicate_structs(structs: List[Struct]) -> List[Struct]:
    """Remove duplicate struct definitions."""
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
    print(f"Building global type table from {len(objfiles)} object files...")
    global_type_table = build_global_type_table(objfiles)
    print(f"  Type table has {len(global_type_table)} entries")
    
    print(f"\nParsing structs...")
    all_structs = parse_structs_with_type_table(objfiles, global_type_table)
    print(f"  Found {len(all_structs)} structs total")
    
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
