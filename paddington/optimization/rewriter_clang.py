"""Clang-based struct rewriter using AST for accurate access specifier handling."""

import clang.cindex
from typing import List, Dict, Tuple
from ..core import StructInfo, MemberInfo
from ..utils import Logger


def init_libclang():
    """Initialize libclang."""
    if not clang.cindex.Config.loaded:
        try:
            clang.cindex.Config.set_library_file('/usr/lib64/libclang.so.20.1')
        except:
            try:
                clang.cindex.Config.set_library_file('/usr/lib/llvm-14/lib/libclang.so.1')
            except:
                pass


def rewrite_struct_clang(file_path: str, struct: StructInfo, new_order: List[MemberInfo], compile_commands_dir: str = None) -> str:
    """Rewrite struct preserving access specifiers using clang AST.
    
    Args:
        file_path: Path to source file
        struct: Struct info from pahole
        new_order: New member order
        compile_commands_dir: Directory containing compile_commands.json
    """
    log = Logger()
    init_libclang()
    
    # Use compilation database to get proper compile flags
    index = clang.cindex.Index.create()
    
    if compile_commands_dir:
        try:
            compdb = clang.cindex.CompilationDatabase.fromDirectory(compile_commands_dir)
            # Try to find compile commands for this file or any .cpp that includes it
            commands = list(compdb.getAllCompileCommands())
            
            if commands:
                # Use the first command's flags as a baseline
                args = []
                for arg in commands[0].arguments:
                    arg_str = str(arg)
                    # Skip output files and source files
                    if arg_str in ['c++', 'g++', 'clang++'] or arg_str.endswith('.cpp') or arg_str.endswith('.o'):
                        continue
                    if arg_str in ['-c', '-o']:
                        continue
                    args.append(arg_str)
                
                log.debug(f"Using {len(args)} compile flags from compilation database")
                tu = index.parse(file_path, args=args)
            else:
                log.warning(f"No compile commands found in {compile_commands_dir}")
                tu = index.parse(file_path, args=['-std=c++17'])
        except Exception as e:
            log.warning(f"Could not load compilation database: {e}")
            tu = index.parse(file_path, args=['-std=c++17'])
    else:
        tu = index.parse(file_path, args=['-std=c++17'])
    
    if not tu:
        log.warning(f"Could not parse {file_path} with clang")
        with open(file_path) as f:
            return f.read()
    
    # Check for parse errors
    if list(tu.diagnostics):
        log.debug(f"Clang parse warnings for {file_path}: {len(list(tu.diagnostics))} diagnostics")
        # Continue anyway - warnings are often acceptable
    
    # Find struct
    struct_cursor = find_struct(tu.cursor, struct.name)
    if not struct_cursor:
        log.warning(f"Could not find {struct.name} in AST")
        with open(file_path) as f:
            return f.read()
    
    # Extract members with access specifiers
    members_info = {}  # member_name -> (access_spec, extent)
    current_access = 'public' if struct_cursor.kind == clang.cindex.CursorKind.STRUCT_DECL else 'private'
    
    for child in struct_cursor.get_children():
        if child.kind == clang.cindex.CursorKind.CXX_ACCESS_SPEC_DECL:
            current_access = str(child.access_specifier).split('.')[-1].lower()
        elif child.kind == clang.cindex.CursorKind.FIELD_DECL:
            if child.spelling in [m.name for m in struct.members]:
                members_info[child.spelling] = (current_access, child.extent)
    
    if len(members_info) != len(struct.members):
        missing = [m.name for m in struct.members if m.name not in members_info]
        log.warning(f"Clang found {len(members_info)}/{len(struct.members)} members (missing: {', '.join(missing[:3])})")
        with open(file_path) as f:
            return f.read()
    
    # Read file
    with open(file_path) as f:
        lines = f.readlines()
    
    # Extract member source text
    member_sources = {}  # member_name -> (source_text, access_spec)
    for member_name, (access_spec, extent) in members_info.items():
        start_line = extent.start.line - 1
        end_line = extent.end.line
        source_lines = lines[start_line:end_line]
        member_sources[member_name] = (''.join(source_lines), access_spec)
    
    # Remove old member declarations
    lines_to_remove = set()
    for _, extent in members_info.values():
        for line_num in range(extent.start.line - 1, extent.end.line):
            lines_to_remove.add(line_num)
    
    for idx in sorted(lines_to_remove, reverse=True):
        del lines[idx]
    
    # Find insertion point (where first member was)
    first_member_line = min(extent.start.line - 1 for _, extent in members_info.values())
    deletions_before = sum(1 for idx in lines_to_remove if idx < first_member_line)
    insert_pos = first_member_line - deletions_before
    
    # Insert reordered members with access specifiers
    current_access = None
    for member in reversed(new_order):
        if member.name in member_sources:
            source_text, access_spec = member_sources[member.name]
            
            # Insert access specifier if changed
            if access_spec != current_access:
                lines.insert(insert_pos, f"  {access_spec}:\n")
                current_access = access_spec
            
            # Insert member
            lines.insert(insert_pos, source_text)
    
    return ''.join(lines)


def find_struct(cursor, name):
    """Find struct/class cursor by name."""
    if cursor.spelling == name and cursor.kind in [
        clang.cindex.CursorKind.STRUCT_DECL,
        clang.cindex.CursorKind.CLASS_DECL,
        clang.cindex.CursorKind.CLASS_TEMPLATE
    ]:
        return cursor
    
    for child in cursor.get_children():
        result = find_struct(child, name)
        if result:
            return result
    
    return None
