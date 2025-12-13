"""File filtering utilities."""

import fnmatch
from pathlib import Path
from typing import List, Optional


def matches_pattern(file_path: Path, pattern: str) -> bool:
    """Check if file matches a glob pattern.

    Args:
        file_path: File path to check
        pattern: Glob pattern (e.g., '*/core/*', '*.cpp', 'test_*')

    Returns:
        True if file matches pattern
    """
    # Match against full path and filename
    return fnmatch.fnmatch(str(file_path), pattern) or fnmatch.fnmatch(
        file_path.name, pattern
    )


def filter_files(
    files: List[Path],
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> List[Path]:
    """Filter files based on include/exclude patterns.

    Args:
        files: List of files to filter
        include_patterns: If provided, only include files matching these patterns
        exclude_patterns: If provided, exclude files matching these patterns

    Returns:
        Filtered list of files
    """
    result = files

    # Apply include patterns (if any)
    if include_patterns:
        result = [
            f
            for f in result
            if any(matches_pattern(f, pattern) for pattern in include_patterns)
        ]

    # Apply exclude patterns (if any)
    if exclude_patterns:
        result = [
            f
            for f in result
            if not any(matches_pattern(f, pattern) for pattern in exclude_patterns)
        ]

    return result
