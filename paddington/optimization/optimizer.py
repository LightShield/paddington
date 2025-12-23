"""Struct optimization logic."""

from typing import List, Optional, Set
from ..core import StructInfo, MemberInfo


def get_optimal_member_order(struct: StructInfo) -> List[MemberInfo]:
    """Return members in optimal order (largest to smallest)."""
    return sorted(struct.members, key=lambda m: (m.size, -m.offset), reverse=True)


def is_leaf_struct(struct: StructInfo, all_struct_names: Set[str]) -> bool:
    """Check if struct contains only native types (no other structs)."""
    return struct.is_leaf(all_struct_names)


def needs_optimization(struct: StructInfo):
    """Check if struct can benefit from optimization.
    
    Returns:
        (bool, SkipReason or None): (should_optimize, reason_if_skipped)
    """
    from .skip_reason import SkipReason
    
    if not struct.members or struct.size == 0:
        return False, SkipReason.NO_MEMBERS if not struct.members else SkipReason.ZERO_SIZE
    
    if any(m.size == 0 for m in struct.members):
        zero_members = [m.name for m in struct.members if m.size == 0]
        return False, (SkipReason.ZERO_SIZE_MEMBER, zero_members)
    
    # Simple check: if there's any padding, it might be optimizable
    padding = struct.calculate_padding()
    if padding == 0:
        return False, SkipReason.NO_PADDING
    
    return True, None
