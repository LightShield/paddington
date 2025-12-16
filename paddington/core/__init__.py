"""Core data structures and parsing."""

from .models import MemberInfo, StructInfo
from .dwarf_parser import parse_object_files, identify_leaves_and_order

# Legacy clang parser (deprecated)
from .parser import init_libclang, parse_file, parse_struct

__all__ = [
    "MemberInfo",
    "StructInfo",
    "parse_object_files",
    "identify_leaves_and_order",
    # Legacy
    "init_libclang",
    "parse_file",
    "parse_struct",
]
