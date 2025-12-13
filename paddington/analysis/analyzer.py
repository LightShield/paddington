"""Main analysis orchestration."""

from pathlib import Path
from ..utils import find_cpp_files, Logger
from ..utils.validation import (
    validate_path_exists,
    validate_libclang_available,
    validate_cpp_files_exist,
)
from ..core import init_libclang, parse_file
from .reporter import report_analysis


def analyze_files(path: Path, verbosity: int = 1) -> None:
    """Analyze C++ files for struct padding.

    Args:
        path: File or directory path to analyze
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

    log.debug(f"Found {len(files)} C++ files")
    init_libclang()

    all_structs = []
    for file in files:
        try:
            log.debug(f"Parsing {file}")
            structs = parse_file(file)
            all_structs.extend(structs)
        except Exception as e:
            log.error(f"Error parsing {file}: {e}")

    report_analysis(all_structs, verbosity)
