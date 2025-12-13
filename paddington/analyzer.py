"""Main analysis orchestration."""
from pathlib import Path
from .file_utils import find_cpp_files
from .parser import init_libclang, parse_file
from .reporter import report_analysis
from .logger import Logger

def analyze_files(path: Path, verbosity: int = 1):
    """Analyze C++ files for struct padding."""
    log = Logger()
    
    # Map verbosity to log level
    if verbosity >= 3:
        log.set_level("DEBUG")
    elif verbosity >= 2:
        log.set_level("INFO")
    else:
        log.set_level("WARNING")
    
    files = find_cpp_files(path)
    
    if not files:
        log.warning(f"No C++ files found in {path}")
        return
    
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
