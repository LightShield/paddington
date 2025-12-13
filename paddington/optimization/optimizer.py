"""Struct optimization logic."""

from typing import List, Tuple, Optional
from ..core import StructInfo, MemberInfo


def get_optimal_member_order(struct: StructInfo) -> List[MemberInfo]:
    """Return members in optimal order (largest to smallest).

    For templates, template parameters with unknown size go last.
    """
    # Separate known-size members from template parameters
    known_size = [m for m in struct.members if m.size > 0]
    unknown_size = [m for m in struct.members if m.size <= 0]

    # Sort known-size members by size descending
    known_size.sort(key=lambda m: (m.size, m.alignment), reverse=True)

    # Template parameters go last
    return known_size + unknown_size


def is_leaf_struct(struct: StructInfo, all_struct_names: Optional[set] = None) -> bool:
    """Check if struct contains only native types (no other structs).

    If all_struct_names is provided, checks against known structs.
    Otherwise, uses heuristic based on type names.
    """
    native_types = {
        "char",
        "signed char",
        "unsigned char",
        "short",
        "unsigned short",
        "int",
        "unsigned int",
        "long",
        "unsigned long",
        "long long",
        "unsigned long long",
        "float",
        "double",
        "long double",
        "bool",
        "_Bool",
        "int8_t",
        "uint8_t",
        "int16_t",
        "uint16_t",
        "int32_t",
        "uint32_t",
        "int64_t",
        "uint64_t",
        "size_t",
        "ssize_t",
        "ptrdiff_t",
    }

    for member in struct.members:
        # Remove const/volatile qualifiers and pointers/references
        base_type = (
            member.type_name.replace("const", "").replace("volatile", "").strip()
        )
        base_type = base_type.rstrip("*&").strip()

        if base_type not in native_types:
            # If we have a list of known structs, check against it
            if all_struct_names and base_type in all_struct_names:
                return False
            # Otherwise, assume it's a custom type
            elif not all_struct_names:
                return False

    return True


def needs_optimization(struct: StructInfo) -> bool:
    """Check if struct can benefit from optimization."""
    optimal_size = struct.calculate_optimal_size()
    return struct.total_size > optimal_size
