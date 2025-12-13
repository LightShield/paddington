"""Analyze inheritance relationships."""

from typing import List, Optional, Set
import clang.cindex as clang
from .models import StructInfo


def get_base_classes(cursor: clang.Cursor) -> List[str]:
    """Get list of base class names for a struct/class."""
    bases = []
    for child in cursor.get_children():
        if child.kind == clang.CursorKind.CXX_BASE_SPECIFIER:
            bases.append(child.type.spelling)
    return bases


def has_inheritance(struct: StructInfo, cursor: clang.Cursor) -> bool:
    """Check if struct has base classes."""
    return len(get_base_classes(cursor)) > 0


def can_optimize_with_inheritance(
    struct: StructInfo, all_structs: List[StructInfo]
) -> bool:
    """Check if struct with inheritance can be optimized.

    We can optimize if:
    - It has no base classes (leaf in inheritance hierarchy)
    - It has base classes but we're only reordering its own members

    We cannot optimize if:
    - Base class layout would be affected
    """
    # For now, we can always optimize - we only reorder the derived class's own members
    # Base class members are laid out first and we don't touch them
    return True


def get_own_members_only(struct: StructInfo, cursor: clang.Cursor) -> List:
    """Get only the members declared in this class, not inherited ones.

    This is important because we should only reorder members declared
    in the current class, not inherited members from base classes.
    """
    # libclang's struct.members already only includes members declared in this class
    # Inherited members are not included in the field list
    return struct.members
