"""Pure functions for calculating padding in structs."""

from typing import List
from ..struct_data import MemberInfo


def calculate_padding(members: List[MemberInfo], total_size: int) -> int:
    """Calculate total padding bytes in a struct.
    
    Args:
        members: List of struct members
        total_size: Total size of the struct
        
    Returns:
        Total padding bytes
    """
    if not members:
        return total_size
    
    total_member_size = sum(member.size for member in members)
    return total_size - total_member_size


def calculate_internal_padding(members: List[MemberInfo]) -> int:
    """Calculate internal padding between members.
    
    Args:
        members: List of struct members sorted by offset
        
    Returns:
        Internal padding bytes
    """
    if len(members) < 2:
        return 0
    
    # Sort by offset to ensure correct order
    sorted_members = sorted(members, key=lambda m: m.offset)
    
    internal_padding = 0
    for i in range(len(sorted_members) - 1):
        current = sorted_members[i]
        next_member = sorted_members[i + 1]
        
        expected_next_offset = current.offset + current.size
        actual_gap = next_member.offset - expected_next_offset
        internal_padding += actual_gap
    
    return internal_padding


def calculate_trailing_padding(members: List[MemberInfo], total_size: int) -> int:
    """Calculate trailing padding after the last member.
    
    Args:
        members: List of struct members
        total_size: Total size of the struct
        
    Returns:
        Trailing padding bytes
    """
    if not members:
        return total_size
    
    # Find the last member by offset
    last_member = max(members, key=lambda m: m.offset)
    last_member_end = last_member.offset + last_member.size
    
    return total_size - last_member_end