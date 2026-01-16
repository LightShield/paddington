"""Pure functions for reordering struct members to minimize padding."""

from typing import List
from ..struct_data import MemberInfo


def reorder_by_size(members: List[MemberInfo]) -> List[MemberInfo]:
    """Reorder members by size (largest first) for optimal packing.
    
    Args:
        members: List of struct members
        
    Returns:
        Members sorted by size (descending)
    """
    return sorted(members, key=lambda m: m.size, reverse=True)


def reorder_within_access_modifiers(members: List[MemberInfo]) -> List[MemberInfo]:
    """Reorder members by size within each access modifier group.
    
    Preserves access modifier grouping while optimizing within groups.
    
    Args:
        members: List of struct members
        
    Returns:
        Members reordered within access modifier groups
    """
    # Group by access modifier while preserving order
    groups = {}
    group_order = []
    
    for member in members:
        if member.access_modifier not in groups:
            groups[member.access_modifier] = []
            group_order.append(member.access_modifier)
        groups[member.access_modifier].append(member)
    
    # Sort within each group by size
    result = []
    for access_modifier in group_order:
        group_members = groups[access_modifier]
        sorted_group = sorted(group_members, key=lambda m: m.size, reverse=True)
        result.extend(sorted_group)
    
    return result


def reorder_with_split_access_modifiers(members: List[MemberInfo]) -> List[MemberInfo]:
    """Reorder members by size, splitting access modifiers for optimal packing.
    
    Groups all members by access modifier, then sorts each group by size.
    
    Args:
        members: List of struct members
        
    Returns:
        Members grouped by access modifier and sorted by size
    """
    # Group by access modifier
    groups = {}
    for member in members:
        if member.access_modifier not in groups:
            groups[member.access_modifier] = []
        groups[member.access_modifier].append(member)
    
    # Sort each group by size and combine
    result = []
    access_order = ["public", "protected", "private", "none"]
    
    for access_modifier in access_order:
        if access_modifier in groups:
            sorted_group = sorted(groups[access_modifier], key=lambda m: m.size, reverse=True)
            result.extend(sorted_group)
    
    return result


def reorder_ignore_access_modifiers(members: List[MemberInfo]) -> List[MemberInfo]:
    """Reorder members by size, ignoring access modifiers completely.
    
    Args:
        members: List of struct members
        
    Returns:
        All members sorted by size (descending)
    """
    return reorder_by_size(members)


def get_optimal_order(members: List[MemberInfo], strategy: str) -> List[MemberInfo]:
    """Get optimal member order using specified strategy.
    
    Args:
        members: List of struct members
        strategy: Reordering strategy ("preserve", "split", "ignore")
        
    Returns:
        Members reordered according to strategy
        
    Raises:
        ValueError: If strategy is not recognized
    """
    if strategy == "preserve":
        return reorder_within_access_modifiers(members)
    elif strategy == "split":
        return reorder_with_split_access_modifiers(members)
    elif strategy == "ignore":
        return reorder_ignore_access_modifiers(members)
    else:
        raise ValueError(f"Unknown strategy: {strategy}. Use 'preserve', 'split', or 'ignore'.")