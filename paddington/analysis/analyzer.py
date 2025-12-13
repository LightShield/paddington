"""Main analysis orchestration."""

from pathlib import Path
from typing import Optional, List
from ..utils import find_cpp_files, Logger
from ..utils.validation import (
    validate_path_exists,
    validate_libclang_available,
    validate_cpp_files_exist,
)
from ..core import init_libclang, parse_file
from .reporter import report_analysis


def analyze_files(
    path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    verbosity: int = 1,
) -> None:
    """Analyze C++ files for struct padding.

    Args:
        path: File or directory path to analyze
        include_patterns: Only process files matching these patterns
        exclude_patterns: Skip files matching these patterns
        verbosity: Logging verbosity level (1=WARNING, 2=INFO, 3=DEBUG)

    Raises:
        FileNotFoundError: If path doesn't exist
        ValueError: If no C++ files found
        RuntimeError: If libclang not available
    """
    log = Logger()

    # Map verbosity to log level
    if verbosity >= 3:
        log.set_level("DEBUG")
    elif verbosity >= 2:
        log.set_level("INFO")
    else:
        log.set_level("WARNING")

    # Validate inputs
    try:
        validate_path_exists(path)
        validate_libclang_available()
        validate_cpp_files_exist(path)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        log.error(str(e))
        return

    files = find_cpp_files(path)

    # Check for compilation database
    from ..utils.compilation_database import (
        find_compilation_database,
        get_files_from_compilation_database,
        get_compile_args_for_file,
    )

    compile_db = find_compilation_database(path)
    if compile_db:
        log.info(f"Using compilation database: {compile_db}")
        db_files = get_files_from_compilation_database(compile_db)
        if db_files:
            files = db_files
            log.debug(f"Using {len(files)} files from compilation database")

    # Apply include/exclude filters
    if include_patterns or exclude_patterns:
        from ..utils.file_filter import filter_files

        original_count = len(files)
        files = filter_files(files, include_patterns, exclude_patterns)
        log.info(f"Filtered {original_count} files to {len(files)} files")
        if include_patterns:
            log.debug(f"Include patterns: {include_patterns}")
        if exclude_patterns:
            log.debug(f"Exclude patterns: {exclude_patterns}")

    log.debug(f"Found {len(files)} C++ files")
    init_libclang()

    all_structs = []
    for file in files:
        try:
            log.debug(f"Parsing {file}")

            # Get compile args from database if available
            compile_args = None
            if compile_db:
                compile_args = get_compile_args_for_file(compile_db, file)

            structs = parse_file(file, compile_args)
            all_structs.extend(structs)
        except Exception as e:
            log.error(f"Error parsing {file}: {e}")

    report_analysis(all_structs, verbosity)
