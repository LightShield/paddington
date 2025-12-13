"""C++ parsing using libclang."""
from pathlib import Path
from typing import List, Optional
import clang.cindex as clang
from .models import MemberInfo, StructInfo

def init_libclang():
    """Initialize libclang library."""
    clang.Config.set_library_file('/Library/Developer/CommandLineTools/usr/lib/libclang.dylib')

def parse_struct(cursor: clang.Cursor) -> Optional[StructInfo]:
    """Parse a struct/class cursor into StructInfo."""
    if cursor.kind not in [clang.CursorKind.STRUCT_DECL, clang.CursorKind.CLASS_DECL]:
        return None
    
    if not cursor.is_definition():
        return None
    
    if has_ignore_annotation(cursor):
        return None
    
    members = []
    for child in cursor.get_children():
        if child.kind == clang.CursorKind.FIELD_DECL:
            member_type = child.type
            members.append(MemberInfo(
                name=child.spelling,
                type_name=member_type.spelling,
                size=member_type.get_size(),
                alignment=member_type.get_align(),
                offset=cursor.type.get_offset(child.spelling) // 8
            ))
    
    if not members:
        return None
    
    return StructInfo(
        name=cursor.spelling,
        file_path=str(cursor.location.file),
        line=cursor.location.line,
        members=members,
        total_size=cursor.type.get_size(),
        is_class=(cursor.kind == clang.CursorKind.CLASS_DECL)
    )

def has_ignore_annotation(cursor: clang.Cursor) -> bool:
    """Check if cursor has paddington-ignore annotation."""
    comment = cursor.raw_comment
    if comment and 'paddington-ignore' in comment:
        return True
    
    file = cursor.location.file
    if not file:
        return False
    
    try:
        with open(file.name, 'r') as f:
            lines = f.readlines()
            if cursor.location.line > 1:
                prev_line = lines[cursor.location.line - 2].strip()
                if 'paddington-ignore' in prev_line:
                    return True
    except:
        pass
    
    return False

def find_structs(translation_unit: clang.TranslationUnit) -> List[StructInfo]:
    """Find all struct definitions in translation unit."""
    structs = []
    
    def visit(cursor):
        struct_info = parse_struct(cursor)
        if struct_info:
            structs.append(struct_info)
        
        for child in cursor.get_children():
            visit(child)
    
    visit(translation_unit.cursor)
    return structs

def parse_file(file_path: Path) -> List[StructInfo]:
    """Parse a single C++ file and return struct definitions."""
    index = clang.Index.create()
    include_dir = f"-I{file_path.parent}"
    
    tu = index.parse(str(file_path), args=['-std=c++17', include_dir])
    
    # Check for parse errors
    if tu.diagnostics:
        errors = [d for d in tu.diagnostics if d.severity >= clang.Diagnostic.Error]
        if errors:
            return []
    
    return find_structs(tu)
