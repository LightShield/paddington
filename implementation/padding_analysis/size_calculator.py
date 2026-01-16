"""Pure functions for calculating struct sizes with alignment."""

from typing import List
from ..struct_data import MemberInfo


def calculate_struct_size(members: List[MemberInfo]) -> int:
    """Calculate struct size with proper alignment.
    
    Args:
        members: List of struct members in their current order
        
    Returns:
        Total struct size including padding
    """
    if not members:
        return 0
    
    current_offset = 0
    max_alignment = 1
    
    for member in members:
        # Calculate alignment requirement (assume size equals alignment for simplicity)
        alignment = _get_alignment(member.size)
        max_alignment = max(max_alignment, alignment)
        
        # Align current offset
        current_offset = _align_to(current_offset, alignment)
        current_offset += member.size
    
    # Align final size to largest member alignment
    return _align_to(current_offset, max_alignment)


def calculate_optimal_size(members: List[MemberInfo]) -> int:
    """Calculate struct size if members were optimally ordered.
    
    Args:
        members: List of struct members
        
    Returns:
        Optimal struct size with members sorted by size
    """
    if not members:
        return 0
    
    # Sort by size (descending) for optimal packing
    sorted_members = sorted(members, key=lambda m: m.size, reverse=True)
    
    return calculate_struct_size(sorted_members)


def _get_alignment(size: int) -> int:
    """Get alignment requirement for a given size.
    
    Args:
        size: Size of the member
        
    Returns:
        Alignment requirement
    """
    # Common alignment rules: 1, 2, 4, 8 bytes
    if size >= 8:
        return 8
    elif size >= 4:
        return 4
    elif size >= 2:
        return 2
    else:
        return 1


def _align_to(offset: int, alignment: int) -> int:
    """Align offset to the specified alignment.
    
    Args:
        offset: Current offset
        alignment: Required alignment
        
    Returns:
        Aligned offset
    """
    return (offset + alignment - 1) // alignment * alignment