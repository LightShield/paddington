"""Struct optimization logic."""

from typing import List, Optional, Set
from ..core import StructInfo, MemberInfo


def get_optimal_member_order(struct: StructInfo) -> List[MemberInfo]:
    """Return members in optimal order (largest to smallest)."""
    return sorted(struct.members, key=lambda m: (m.size, -m.offset), reverse=True)


def is_leaf_struct(struct: StructInfo, all_struct_names: Set[str]) -> bool:
    """Check if struct contains only native types (no other structs)."""
    return struct.is_leaf(all_struct_names)


def needs_optimization(struct: StructInfo) -> bool:
    """Check if struct can benefit from optimization."""
    if not struct.members or struct.size == 0:
        return False
    if any(m.size == 0 for m in struct.members):
        return False
        
    optimal_size = struct.calculate_optimal_size()
    return struct.size > optimal_size
