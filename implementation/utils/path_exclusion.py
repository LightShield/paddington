"""Centralized path exclusion utility for filtering paths based on patterns."""

from pathlib import Path
from typing import List


def should_exclude_path(path: Path, exclude_patterns: List[str], root: Path = None) -> bool:
    """
    Check if a path should be excluded based on patterns.
    
    Uses path.parts matching by extracting key segments from patterns
    (splitting on '/' and removing '*') and checking if all segments
    appear in the path's parts.
    
    Args:
        path: Path to check
        exclude_patterns: List of exclusion patterns
        root: Optional root path for relative pattern matching
        
    Returns:
        True if path should be excluded, False otherwise
    """
    if not exclude_patterns:
        return False
        
    # Convert to relative path if root is provided
    check_path = path
    if root and path.is_absolute():
        try:
            check_path = path.relative_to(root)
        except ValueError:
            return False  # Path not under root, cannot match relative patterns
    
    path_parts = check_path.parts
    
    for pattern in exclude_patterns:
        is_absolute_pattern = pattern.startswith('/')
        
        # Handle absolute patterns (starting with '/')
        if is_absolute_pattern:
            pattern = pattern[1:]  # Remove leading slash
            
        # Split pattern into segments
        pattern_parts = [seg for seg in pattern.split('/') if seg]
        
        if not pattern_parts:
            continue
            
        # For absolute patterns, match from start of path
        if is_absolute_pattern:
            if _match_absolute_pattern(path_parts, pattern_parts):
                return True
        else:
            # For relative patterns, match anywhere in path
            if _match_relative_pattern(path_parts, pattern_parts):
                return True
            
    return False


def should_exclude_directory(dir_path: Path, exclude_patterns: List[str], root: Path = None) -> bool:
    """
    Check if a directory should be excluded.
    
    Returns True if the directory itself or any of its parents should be excluded.
    
    Args:
        dir_path: Directory path to check
        exclude_patterns: List of exclusion patterns
        root: Optional root path for relative pattern matching
        
    Returns:
        True if directory should be excluded, False otherwise
    """
    if not exclude_patterns:
        return False
        
    # Check the directory itself
    if should_exclude_path(dir_path, exclude_patterns, root):
        return True
        
    # Check all parent directories
    current = dir_path
    while current.parent != current:  # Stop at filesystem root
        current = current.parent
        if should_exclude_path(current, exclude_patterns, root):
            return True
            
    return False


def _match_absolute_pattern(path_parts: tuple, pattern_parts: List[str]) -> bool:
    """Match pattern from the start of path (absolute pattern)."""
    if len(pattern_parts) > len(path_parts):
        return False
        
    pattern_idx = 0
    path_idx = 0
    
    while pattern_idx < len(pattern_parts) and path_idx < len(path_parts):
        if pattern_parts[pattern_idx] == '*':
            pattern_idx += 1
            path_idx += 1
        elif pattern_parts[pattern_idx] == path_parts[path_idx]:
            pattern_idx += 1
            path_idx += 1
        else:
            return False
            
    return pattern_idx == len(pattern_parts)


def _match_relative_pattern(path_parts: tuple, pattern_parts: List[str]) -> bool:
    """Match pattern anywhere in path (relative pattern)."""
    # Special case: if pattern is only wildcards, it should not match
    if all(part == '*' for part in pattern_parts):
        return False
        
    # For patterns without leading wildcards, they should match from path boundaries
    # e.g., "platforms/*/regs/*" should match "platforms/arm/regs/file" but not "other/platforms/arm/regs/file"
    
    # If pattern starts with a literal (not *), it should match from start of path or after a path separator
    if pattern_parts and pattern_parts[0] != '*':
        # Try matching from start of path
        if _match_pattern_at_position(path_parts, pattern_parts, 0):
            return True
        return False
    else:
        # Pattern starts with wildcard, can match anywhere
        for start_idx in range(len(path_parts)):
            if _match_pattern_at_position(path_parts, pattern_parts, start_idx):
                return True
        return False


def _match_pattern_at_position(path_parts: tuple, pattern_parts: List[str], start_idx: int) -> bool:
    """Try to match pattern starting at specific position in path."""
    if start_idx + len(pattern_parts) > len(path_parts):
        # Not enough remaining parts to match pattern
        remaining_wildcards = sum(1 for p in pattern_parts if p == '*')
        remaining_literals = len(pattern_parts) - remaining_wildcards
        remaining_path = len(path_parts) - start_idx
        if remaining_literals > remaining_path:
            return False
    
    pattern_idx = 0
    path_idx = start_idx
    
    while pattern_idx < len(pattern_parts) and path_idx < len(path_parts):
        if pattern_parts[pattern_idx] == '*':
            pattern_idx += 1
            path_idx += 1
        elif pattern_parts[pattern_idx] == path_parts[path_idx]:
            pattern_idx += 1
            path_idx += 1
        else:
            return False
            
    return pattern_idx == len(pattern_parts)