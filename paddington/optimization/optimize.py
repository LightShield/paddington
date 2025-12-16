"""Optimization orchestration."""

from pathlib import Path
from typing import List, Optional
from ..utils import Logger
from ..core import parse_object_files, identify_leaves_and_order
from .optimizer import needs_optimization, get_optimal_member_order
from .rewriter import rewrite_struct_definition, rewrite_constructors, write_file
from .patch_generator import create_patch, write_apply_order


def optimize_files(
    path: Path,
    dry_run: bool = True,
    force: bool = False,
    update_signatures: bool = False,
    patch_dir: Optional[Path] = None,
    build_command: Optional[str] = None,
    verify: bool = False,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    verbosity: int = 1,
) -> None:
    """Optimize struct padding from object files.

    Args:
        path: Object file or directory to optimize
        dry_run: If True, only report what would be done
        force: If True, reorder even if no size savings
        update_signatures: If True, update constructor signatures and call sites
        patch_dir: If provided, generate patches instead of modifying files
        build_command: If provided, run after each optimization to verify build
        verify: If True, verify compilation after changes
        include_patterns: Only process files matching these patterns
        exclude_patterns: Skip files matching these patterns
        verbosity: Logging verbosity level
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

    if patch_dir:
        dry_run = False
        patch_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Generating patches in {patch_dir}")

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

    log.info(f"Extracting structs from {len(objfiles)} object files...")
    all_structs = parse_object_files(objfiles)
    
    log.info(f"Ordering {len(all_structs)} structs by dependencies...")
    ordered_structs, visited = identify_leaves_and_order(all_structs)

    if not update_signatures:
        log.info("Note: Only updating initializer lists. Use --update-signatures to also update constructor signatures and call sites.")

    optimized_count = 0
    total_savings = 0
    processed = set()

    for struct in ordered_structs:
        if struct.name in processed:
            continue
        processed.add(struct.name)
        
        # Skip if no members or zero-sized members
        if not struct.members or any(m.size == 0 for m in struct.members):
            continue
            
        if not needs_optimization(struct) and not force:
            log.debug(f"Skipping {struct.name}: no optimization needed")
            continue

        padding = struct.calculate_padding()
        optimal_order = get_optimal_member_order(struct)
        optimal_size = struct.calculate_optimal_size()
        savings = struct.size - optimal_size
        
        if dry_run:
            log.info(f"[DRY-RUN] Would optimize {struct.name}: {struct.size} bytes -> {optimal_size} bytes ({savings} bytes saved, {padding} bytes padding)")
            optimized_count += 1
            total_savings += savings
        else:
            log.error(f"Source code rewriting not yet implemented for DWARF-extracted structs")
            log.error(f"Need source file location for {struct.name}")
            break

    print(f"\nOptimized {optimized_count} struct(s)/class(es)")
    print(f"Total savings: {total_savings} bytes")
