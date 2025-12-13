"""Main analysis orchestration."""
from pathlib import Path
from .file_utils import find_cpp_files
from .parser import init_libclang, parse_file
from .reporter import report_analysis

def analyze_files(path: Path, verbosity: int = 1):
    """Analyze C++ files for struct padding."""
    files = find_cpp_files(path)
    
    if not files:
        print(f"No C++ files found in {path}")
        return
    
    init_libclang()
    
    all_structs = []
    for file in files:
        try:
            structs = parse_file(file)
            all_structs.extend(structs)
        except Exception as e:
            if verbosity >= 3:
                print(f"Error parsing {file}: {e}")
    
    report_analysis(all_structs, verbosity)
