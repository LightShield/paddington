#!/usr/bin/env python3
"""Extract struct layout from object files using DWARF debug info."""

import json
import hashlib
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFRelocationError


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


def get_cache_path(objfile: Path, cache_dir: Path) -> Path:
    """Get cache file path for an object file."""
    path_hash = hashlib.md5(str(objfile).encode()).hexdigest()[:16]
    return cache_dir / f"{objfile.stem}_{path_hash}.json"


def get_error_cache_path(objfile: Path, cache_dir: Path) -> Path:
    """Get error cache file path."""
    path_hash = hashlib.md5(str(objfile).encode()).hexdigest()[:16]
    return cache_dir / f"{objfile.stem}_{path_hash}.error"


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError()


def build_global_type_table(objfiles: List[Path], cache_dir: Optional[Path] = None, log=None) -> Tuple[Dict, List]:
    """Build global type table from all object files."""
    from ..utils import Logger
    if log is None:
        log = Logger()
    
    global_table = {}
    cached_count = 0
    parsed_count = 0
    skipped_files = []
    
    log.info(f"Building global type table from {len(objfiles)} object files...")
    
    for idx, objfile in enumerate(objfiles, 1):
        if idx % 10 == 0:
            log.info(f"Type table: {idx}/{len(objfiles)} (cached: {cached_count}, parsed: {parsed_count}, skipped: {len(skipped_files)})")
        
        log.debug(f"Processing type table for {objfile.name}")
        
        # Check error cache first
        if cache_dir:
            error_cache = get_error_cache_path(objfile, cache_dir)
            if error_cache.exists():
                try:
                    with open(error_cache) as f:
                        reason = f.read().strip()
                    skipped_files.append((objfile.name, f"cached_error: {reason}"))
                    log.debug(f"  Skipped: cached error ({reason})")
                    continue
                except:
                    pass
        
        # Check cache
        if cache_dir:
            cache_file = get_cache_path(objfile, cache_dir)
            type_cache = cache_file.parent / f"{cache_file.stem}_types.json"
            if type_cache.exists():
                try:
                    with open(type_cache) as f:
                        file_types = json.load(f)
                        for offset_str, (name, size) in file_types.items():
                            global_table[int(offset_str)] = ('cached', name, size, None)
                        cached_count += 1
                        log.debug(f"  Loaded from cache: {len(file_types)} types")
                        continue
                except Exception as e:
                    log.debug(f"  Cache read failed: {e}")
                    skipped_files.append((objfile.name, f"cache_read_error: {e}"))
                    continue
        
        # Set 60 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)
        
        error_reason = None
        try:
            with open(objfile, 'rb') as f:
                elf = ELFFile(f)
                
                if not elf.has_dwarf_info():
                    error_reason = "no_dwarf_info"
                    skipped_files.append((objfile.name, error_reason))
                    log.debug(f"  Skipped: no DWARF info")
                    signal.alarm(0)
                    continue
                
                dwarf = elf.get_dwarf_info()
                file_types = {}
                
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
                                file_types[str(die.offset)] = (name, size)
                        
                        elif die.tag == 'DW_TAG_typedef':
                            name_attr = die.attributes.get('DW_AT_name')
                            type_attr = die.attributes.get('DW_AT_type')
                            if name_attr and die.offset:
                                name = name_attr.value
                                if isinstance(name, bytes):
                                    name = name.decode()
                                ref = type_attr.value if type_attr else None
                                global_table[die.offset] = ('typedef', name, 0, ref)
                                file_types[str(die.offset)] = (name, 0)
                        
                        elif die.tag == 'DW_TAG_enumeration_type':
                            name_attr = die.attributes.get('DW_AT_name')
                            size_attr = die.attributes.get('DW_AT_byte_size')
                            if name_attr and die.offset:
                                name = name_attr.value
                                if isinstance(name, bytes):
                                    name = name.decode()
                                size = size_attr.value if size_attr else 4
                                global_table[die.offset] = ('enum', name, size, None)
                                file_types[str(die.offset)] = (name, size)
                        
                        elif die.tag in ['DW_TAG_structure_type', 'DW_TAG_class_type']:
                            name_attr = die.attributes.get('DW_AT_name')
                            size_attr = die.attributes.get('DW_AT_byte_size')
                            if name_attr and die.offset:
                                name = name_attr.value
                                if isinstance(name, bytes):
                                    name = name.decode()
                                size = size_attr.value if size_attr else 0
                                global_table[die.offset] = ('struct', name, size, None)
                                file_types[str(die.offset)] = (name, size)
                
                signal.alarm(0)
                
                # Cache types
                if cache_dir:
                    cache_file = get_cache_path(objfile, cache_dir)
                    type_cache = cache_file.parent / f"{cache_file.stem}_types.json"
                    type_cache.parent.mkdir(parents=True, exist_ok=True)
                    with open(type_cache, 'w') as f:
                        json.dump(file_types, f)
                
                parsed_count += 1
                log.debug(f"  Parsed: {len(file_types)} types")
                
        except TimeoutError:
            signal.alarm(0)
            error_reason = "timeout_60s"
            log.warning(f"Timeout (60s) on {objfile.name}")
            skipped_files.append((objfile.name, error_reason))
        except ELFRelocationError as e:
            signal.alarm(0)
            error_reason = f"relocation_error"
            log.debug(f"  Skipped: relocation error")
            skipped_files.append((objfile.name, error_reason))
        except Exception as e:
            signal.alarm(0)
            error_reason = f"parse_error: {type(e).__name__}"
            log.debug(f"  Skipped: {type(e).__name__}")
            skipped_files.append((objfile.name, error_reason))
        
        # Cache error
        if error_reason and cache_dir:
            error_cache = get_error_cache_path(objfile, cache_dir)
            error_cache.parent.mkdir(parents=True, exist_ok=True)
            with open(error_cache, 'w') as f:
                f.write(error_reason)
    
    log.info(f"Type table complete: {cached_count} cached, {parsed_count} parsed, {len(skipped_files)} skipped")
    
    # Resolve typedefs
    log.debug("Resolving typedefs...")
    resolved = {}
    for offset, (kind, name, size, ref) in global_table.items():
        if kind == 'typedef' and ref and ref in global_table:
            _, _, final_size, _ = global_table[ref]
            resolved[offset] = (name, final_size)
        else:
            resolved[offset] = (name, size)
    
    return resolved, skipped_files


def parse_structs_with_type_table(objfiles: List[Path], type_table: Dict, cache_dir: Optional[Path] = None, type_skipped: List = None, log=None) -> Tuple[List, List]:
    """Parse structs from object files using pre-built type table."""
    from ..utils import Logger
    if log is None:
        log = Logger()
    
    structs = []
    cached_count = 0
    parsed_count = 0
    skipped_files = type_skipped or []
    
    log.info("Parsing structs...")
    
    for idx, objfile in enumerate(objfiles, 1):
        if idx % 10 == 0:
            log.info(f"Parsing structs: {idx}/{len(objfiles)} (cached: {cached_count}, parsed: {parsed_count}, skipped: {len(skipped_files)})")
        
        log.debug(f"Processing structs for {objfile.name}")
        
        # Check error cache first
        if cache_dir:
            error_cache = get_error_cache_path(objfile, cache_dir)
            if error_cache.exists():
                log.debug(f"  Skipped: cached error")
                continue
        
        # Check cache
        if cache_dir:
            cache_file = get_cache_path(objfile, cache_dir)
            if cache_file.exists():
                try:
                    with open(cache_file) as f:
                        cached = json.load(f)
                        for s in cached:
                            members = [Member(**m) for m in s['members']]
                            structs.append(Struct(s['name'], s['size'], members, s.get('file_path'), s.get('line')))
                        cached_count += 1
                        log.debug(f"  Loaded from cache: {len(cached)} structs")
                        continue
                except:
                    pass
        
        # Set 60 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)
        
        try:
            with open(objfile, 'rb') as f:
                elf = ELFFile(f)
                
                if not elf.has_dwarf_info():
                    signal.alarm(0)
                    continue
                
                dwarf = elf.get_dwarf_info()
                file_structs = []
                
                for CU in dwarf.iter_CUs():
                    for die in CU.iter_DIEs():
                        if die.tag in ['DW_TAG_structure_type', 'DW_TAG_class_type']:
                            struct = parse_struct(die, CU, type_table)
                            if struct:
                                structs.append(struct)
                                file_structs.append(struct)
                
                signal.alarm(0)
                
                # Save to cache
                if cache_dir:
                    cache_file = get_cache_path(objfile, cache_dir)
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_file, 'w') as f:
                        json.dump([asdict(s) for s in file_structs], f)
                
                parsed_count += 1
                log.debug(f"  Parsed: {len(file_structs)} structs")
                        
        except TimeoutError:
            signal.alarm(0)
            log.warning(f"Timeout (60s) on {objfile.name}")
            # Cache error
            if cache_dir:
                error_cache = get_error_cache_path(objfile, cache_dir)
                error_cache.parent.mkdir(parents=True, exist_ok=True)
                with open(error_cache, 'w') as f:
                    f.write("timeout_60s")
            continue
        except ELFRelocationError:
            signal.alarm(0)
            # Cache error
            if cache_dir:
                error_cache = get_error_cache_path(objfile, cache_dir)
                error_cache.parent.mkdir(parents=True, exist_ok=True)
                with open(error_cache, 'w') as f:
                    f.write("relocation_error")
            continue
        except Exception as e:
            signal.alarm(0)
            # Cache error
            if cache_dir:
                error_cache = get_error_cache_path(objfile, cache_dir)
                error_cache.parent.mkdir(parents=True, exist_ok=True)
                with open(error_cache, 'w') as f:
                    f.write(f"parse_error: {type(e).__name__}")
            continue
    
    log.info(f"Struct parsing complete: {cached_count} cached, {parsed_count} parsed, {len(skipped_files)} skipped")
    return structs, skipped_files


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


def extract_reference_tree(objfiles: List[Path], output: Path, cache_dir: Optional[Path] = None, log=None) -> None:
    """Extract reference tree from object files and save as JSON."""
    from ..utils import Logger
    if log is None:
        log = Logger()
    
    global_type_table, skipped_files = build_global_type_table(objfiles, cache_dir, log)
    log.info(f"Type table has {len(global_type_table)} entries")
    
    all_structs, skipped_files = parse_structs_with_type_table(objfiles, global_type_table, cache_dir, skipped_files, log)
    log.info(f"Found {len(all_structs)} structs total")
    
    all_structs = deduplicate_structs(all_structs)
    log.info(f"After deduplication: {len(all_structs)} unique structs")
    
    # Save skipped files report
    if skipped_files and cache_dir:
        skipped_report = cache_dir / "skipped_files.txt"
        with open(skipped_report, 'w') as f:
            f.write(f"Skipped {len(skipped_files)} files:\n\n")
            for filename, reason in skipped_files:
                f.write(f"{filename}: {reason}\n")
        log.info(f"Skipped files report: {skipped_report}")
    
    tree = [asdict(s) for s in all_structs]
    
    with open(output, 'w') as f:
        json.dump(tree, f, indent=2)
    
    log.info(f"Extracted to {output}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <output.json> <objfile1.o> [objfile2.o ...]")
        print(f"   or: {sys.argv[0]} <output.json> <directory>")
        print(f"   or: {sys.argv[0]} <output.json> <directory> --cache-dir <cache>")
        sys.exit(1)
        
    output = Path(sys.argv[1])
    
    # Check for cache dir flag
    cache_dir = None
    if "--cache-dir" in sys.argv:
        cache_idx = sys.argv.index("--cache-dir")
        cache_dir = Path(sys.argv[cache_idx + 1])
        sys.argv = sys.argv[:cache_idx] + sys.argv[cache_idx+2:]
    
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
        
    extract_reference_tree(objfiles, output, cache_dir)
