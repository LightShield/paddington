"""Main analysis orchestration."""

from pathlib import Path
from typing import Optional, List
from ..utils import Logger
from ..core import parse_object_files
from .reporter import report_analysis


def analyze_files(
    path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    verbosity: int = 1,
) -> None:
    """Analyze object files for struct padding.

    Args:
        path: Object file or directory path to analyze
        include_patterns: Only process files matching these patterns
        exclude_patterns: Skip files matching these patterns
        verbosity: Logging verbosity level (1=WARNING, 2=INFO, 3=DEBUG)
    """
    log = Logger()

    if verbosity >= 3:
        log.set_level("DEBUG")
    elif verbosity >= 2:
        log.set_level("INFO")
    else:
        log.set_level("WARNING")

    if not path.exists():
        log.error(f"Path does not exist: {path}")
        return

    # Find .o files
    if path.is_file():
        objfiles = [path]
    else:
        objfiles = list(path.rglob("*.o"))

    if not objfiles:
        log.error(f"No .o files found in {path}")
        return

    # Apply filters
    if include_patterns or exclude_patterns:
        from ..utils.file_filter import filter_files
        original_count = len(objfiles)
        objfiles = filter_files(objfiles, include_patterns, exclude_patterns)
        log.info(f"Filtered {original_count} files to {len(objfiles)} files")

    log.info(f"Analyzing {len(objfiles)} object files...")
    
    all_structs = parse_object_files(objfiles)
    
    report_analysis(all_structs, verbosity)
