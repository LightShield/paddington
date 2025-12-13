"""C++ parsing using libclang."""

from pathlib import Path
from typing import List, Optional
import clang.cindex as clang
from .models import MemberInfo, StructInfo

# Constants
BITS_PER_BYTE = 8


def init_libclang():
    """Initialize libclang library."""
    clang.Config.set_library_file(
        "/Library/Developer/CommandLineTools/usr/lib/libclang.dylib"
    )


def parse_struct(cursor: clang.Cursor) -> Optional[StructInfo]:
    """Parse a struct/class cursor into StructInfo."""
    # Handle regular structs/classes and templates
    if cursor.kind not in [
        clang.CursorKind.STRUCT_DECL,
        clang.CursorKind.CLASS_DECL,
        clang.CursorKind.CLASS_TEMPLATE,
    ]:
        return None

    if not cursor.is_definition():
        return None

    if has_ignore_annotation(cursor):
        return None

    if has_preprocessor_directives(cursor):
        return None

    members = []
    for child in cursor.get_children():
        if child.kind == clang.CursorKind.FIELD_DECL:
            member_type = child.type
            members.append(
                MemberInfo(
                    name=child.spelling,
                    type_name=member_type.spelling,
                    size=member_type.get_size(),
                    alignment=member_type.get_align(),
                    offset=cursor.type.get_offset(child.spelling) // BITS_PER_BYTE,
                )
            )

    if not members:
        return None

    # For templates, we can't get accurate size/offset info without instantiation
    # But we can still reorder the template definition
    is_template = cursor.kind == clang.CursorKind.CLASS_TEMPLATE

    return StructInfo(
        name=cursor.spelling,
        file_path=str(cursor.location.file),
        line=cursor.location.line,
        members=members,
        total_size=cursor.type.get_size() if not is_template else 0,
        is_class=(
            cursor.kind
            in [clang.CursorKind.CLASS_DECL, clang.CursorKind.CLASS_TEMPLATE]
        ),
        is_template=is_template,
    )


def has_preprocessor_directives(cursor: clang.Cursor) -> bool:
    """Check if struct contains preprocessor directives like #ifdef.
    
    Args:
        cursor: Struct/class cursor
        
    Returns:
        True if struct body contains #ifdef, #ifndef, #if, etc.
    """
    file = cursor.location.file
    if not file:
        return False

    try:
        with open(file.name, "r") as f:
            lines = f.readlines()

        # Get struct body range (approximate)
        start_line = cursor.location.line
        # Scan ~50 lines (typical struct size)
        end_line = min(start_line + 50, len(lines))

        for i in range(start_line, end_line):
            line = lines[i].strip()
            if line.startswith("#if"):  # Matches #ifdef, #ifndef, #if
                return True
            if line.startswith("};"):  # End of struct
                break

    except (IOError, IndexError):
        pass

    return False


def has_ignore_annotation(cursor: clang.Cursor) -> bool:
    """Check if cursor has paddington-ignore annotation."""
    comment = cursor.raw_comment
    if comment and "paddington-ignore" in comment:
        return True

    file = cursor.location.file
    if not file:
        return False

    try:
        with open(file.name, "r") as f:
            lines = f.readlines()
            if cursor.location.line > 1:
                prev_line = lines[cursor.location.line - 2].strip()
                if "paddington-ignore" in prev_line:
                    return True
    except (IOError, IndexError):
        pass

    return False


def find_structs(translation_unit: clang.TranslationUnit, main_file: str) -> List[StructInfo]:
    """Find all struct definitions in translation unit from the main file only.
    
    Args:
        translation_unit: Parsed translation unit
        main_file: Path to the main file being analyzed (exclude system/third-party)
        
    Returns:
        List of structs defined in main_file (not from includes)
    """
    structs = []

    def visit(cursor):
        struct_info = parse_struct(cursor)
        if struct_info:
            # Only include structs from the main file, not from includes
            if cursor.location.file and cursor.location.file.name == main_file:
                structs.append(struct_info)

        for child in cursor.get_children():
            visit(child)

    visit(translation_unit.cursor)
    return structs


def parse_file(file_path: Path, compile_args: Optional[List[str]] = None) -> List[StructInfo]:
    """Parse a single C++ file and return struct definitions.
    
    Args:
        file_path: Path to C++ file to parse
        compile_args: Optional compile arguments from compilation database
        
    Returns:
        List of structs defined in this file (excludes system/third-party includes)
    """
    index = clang.Index.create()
    
    # Use provided compile args or default
    if compile_args:
        args = compile_args
    else:
        include_dir = f"-I{file_path.parent}"
        args = ["-std=c++17", include_dir]

    try:
        tu = index.parse(str(file_path), args=args)
    except clang.TranslationUnitLoadError:
        # Some files (especially headers) may not parse standalone
        return []

    # Check for parse errors (but allow missing includes if structs are parseable)
    if tu.diagnostics:
        errors = [
            d
            for d in tu.diagnostics
            if d.severity >= clang.Diagnostic.Error
            and "file not found" not in d.spelling.lower()
        ]
        if errors:
            return []

    return find_structs(tu, str(file_path))
