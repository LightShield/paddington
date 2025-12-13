"""Optimization orchestration."""
from pathlib import Path
from typing import List, Dict
from ..utils import find_cpp_files, Logger
from ..core import init_libclang, parse_file
from .optimizer import is_leaf_struct, needs_optimization, get_optimal_member_order
from .rewriter import rewrite_struct_definition, rewrite_constructors, write_file

def optimize_files(path: Path, dry_run: bool = True, verbosity: int = 1):
    """Optimize struct padding in C++ files."""
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
    
    # Group structs by file
    file_structs: Dict[str, List] = {}
    
    for file in files:
        try:
            log.debug(f"Parsing {file}")
            structs = parse_file(file)
            
            for struct in structs:
                if struct.file_path not in file_structs:
                    file_structs[struct.file_path] = []
                file_structs[struct.file_path].append(struct)
        except Exception as e:
            log.error(f"Error parsing {file}: {e}")
    
    # Optimize leaf structs only (Phase 2)
    optimized_count = 0
    total_savings = 0
    
    for file_path, structs in file_structs.items():
        for struct in structs:
            if not is_leaf_struct(struct):
                log.debug(f"Skipping {struct.name}: not a leaf struct")
                continue
            
            if not needs_optimization(struct):
                log.debug(f"Skipping {struct.name}: already optimal")
                continue
            
            # Calculate savings
            optimal_size = struct.calculate_optimal_size()
            savings = struct.total_size - optimal_size
            
            type_name = "class" if struct.is_class else "struct"
            log.info(f"Optimizing {type_name} {struct.name}: {struct.total_size} -> {optimal_size} bytes ({savings} saved)")
            
            if not dry_run:
                try:
                    # Get optimal order
                    new_order = get_optimal_member_order(struct)
                    
                    # Rewrite struct definition
                    content = rewrite_struct_definition(file_path, struct, new_order)
                    
                    # Rewrite constructors in the updated content
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    content = rewrite_constructors(file_path, struct, new_order)
                    
                    # Write back
                    write_file(file_path, content)
                    
                    log.info(f"Updated {file_path}")
                except Exception as e:
                    log.error(f"Error optimizing {struct.name}: {e}")
                    continue
            
            optimized_count += 1
            total_savings += savings
    
    mode = "Would optimize" if dry_run else "Optimized"
    print(f"\n{mode} {optimized_count} struct(s)/class(es)")
    print(f"Total savings: {total_savings} bytes")
    
    if dry_run:
        print("\nRun with --apply to make changes")
