"""Optimization orchestration."""

import hashlib
from pathlib import Path
from typing import List, Optional
from ..utils import Logger
from ..core import parse_object_files, identify_leaves_and_order
from .optimizer import needs_optimization, get_optimal_member_order
from .rewriter import rewrite_struct_definition, rewrite_constructors, write_file


def remap_path(original_path: str, from_prefix: str, to_prefix: str) -> str:
    """Remap file path from build location to source location."""
    if original_path.startswith(from_prefix):
        return original_path.replace(from_prefix, to_prefix, 1)
    return original_path


def deduplicate_objfiles(objfiles: List[Path], log) -> List[Path]:
    """Deduplicate .o files by full content hash."""
    log.info("Deduplicating .o files by content...")
    
    seen_hashes = {}
    unique = []
    
    for idx, objfile in enumerate(objfiles, 1):
        if idx % 100 == 0:
            log.info(f"  Hashing: {idx}/{len(objfiles)}")
        
        try:
            hasher = hashlib.md5()
            with open(objfile, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            content_hash = hasher.hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes[content_hash] = objfile
                unique.append(objfile)
            else:
                log.debug(f"  Duplicate: {objfile.name} (same as {seen_hashes[content_hash].name})")
        except:
            unique.append(objfile)
    
    log.info(f"Deduplicated: {len(objfiles)} -> {len(unique)} files ({len(objfiles) - len(unique)} duplicates removed)")
    return unique


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
    remap_from: Optional[str] = None,
    remap_to: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    deduplicate: bool = False,
    use_pahole: bool = False,
    verbosity: int = 1,
) -> None:
    """Optimize struct padding from object files."""
    log = Logger()

    if verbosity >= 4:
        log.set_level("TRACE")
    elif verbosity >= 3:
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

    if remap_from and remap_to:
        log.info(f"Path remapping enabled: {remap_from} -> {remap_to}")
    
    if cache_dir:
        log.info(f"Using cache directory: {cache_dir}")
    
    if use_pahole:
        log.info("Using pahole for extraction (100x faster)")

    # Find .o files
    log.info(f"Finding .o files in {path}...")
    if path.is_file():
        objfiles = [path]
    else:
        objfiles = list(path.rglob("*.o"))
    
    log.info(f"Found {len(objfiles)} .o files")

    if not objfiles:
        log.error(f"No .o files found in {path}")
        return

    if include_patterns or exclude_patterns:
        log.info("Applying filters...")
        from ..utils.file_filter import filter_files
        original_count = len(objfiles)
        objfiles = filter_files(objfiles, include_patterns, exclude_patterns)
        log.info(f"Filtered {original_count} files to {len(objfiles)} files")

    # Deduplicate by content
    if deduplicate:
        objfiles = deduplicate_objfiles(objfiles, log)

    log.info(f"Extracting structs from {len(objfiles)} object files...")
    
    # Choose extractor
    if use_pahole:
        from ..core.pahole_parser import parse_object_files_with_pahole
        all_structs = parse_object_files_with_pahole(objfiles, log)
    else:
        all_structs = parse_object_files(objfiles, cache_dir, log)
    
    # Filter to only project files (under build root)
    original_count = len(all_structs)
    project_root = str(path.resolve())
    all_structs = [s for s in all_structs if s.file_path and 
                   (s.file_path.startswith(project_root) or 
                    (remap_from and s.file_path.startswith(remap_from)))]
    if original_count > len(all_structs):
        log.info(f"Filtered to project files: {len(all_structs)}/{original_count} structs")
    
    log.info(f"Ordering {len(all_structs)} structs by dependencies...")
    ordered_structs, visited = identify_leaves_and_order(all_structs)

    log.info("Note: Only updating struct definitions and initializer lists (not constructor signatures)")

    optimized_count = 0
    total_savings = 0
    processed = set()
    patch_files = []

    for struct in ordered_structs:
        if struct.name in processed:
            continue
        processed.add(struct.name)
        
        if not struct.members or any(m.size == 0 for m in struct.members):
            continue
        
        if not struct.file_path or not struct.line:
            log.debug(f"Skipping {struct.name}: no source location")
            continue
        
        source_path = struct.file_path
        if remap_from and remap_to:
            source_path = remap_path(source_path, remap_from, remap_to)
            
        if not Path(source_path).exists():
            log.debug(f"Skipping {struct.name}: source file not found at {source_path}")
            continue
        
        should_optimize, skip_reason = needs_optimization(struct)
        if not should_optimize and not force:
            if isinstance(skip_reason, tuple):
                reason, details = skip_reason
                log.debug(f"Skipping {struct.name}: {reason} ({', '.join(details[:3])}{'...' if len(details) > 3 else ''})")
            else:
                log.debug(f"Skipping {struct.name}: {skip_reason}")
            continue

        optimal_order = get_optimal_member_order(struct)
        padding = struct.calculate_padding()
        # Note: We can't accurately calculate optimal size due to alignment complexity
        # So we report padding that could potentially be saved
        
        if dry_run:
            log.info(f"[DRY-RUN] Would optimize {struct.name}: {struct.size} bytes ({padding} bytes padding)")
            log.info(f"  File: {source_path}:{struct.line}")
            optimized_count += 1
            total_savings += padding
        else:
            log.info(f"Optimizing {struct.name}: {struct.size} bytes ({padding} bytes padding)")
            
            # Rewrite struct definition using minimal line-swap approach
            from .rewriter_minimal import rewrite_struct_minimal
            new_content = rewrite_struct_minimal(source_path, struct, optimal_order)
            write_file(source_path, new_content)
            
            # Reorder constructor initializer lists in header file
            from .rewriter import rewrite_constructors
            new_content = rewrite_constructors(source_path, struct, optimal_order)
            write_file(source_path, new_content)
            
            # Also check corresponding .cpp file for out-of-line constructors
            cpp_path = Path(source_path).with_suffix('.cpp')
            if cpp_path.exists():
                new_content = rewrite_constructors(str(cpp_path), struct, optimal_order)
                write_file(str(cpp_path), new_content)
            
            log.info(f"  Updated {source_path}")
            
            # Generate patch if requested
            if patch_dir:
                from .patch_generator import create_patch, generate_commit_message
                # Include both .h and .cpp files in patch if .cpp exists
                files_to_patch = [source_path]
                cpp_path = Path(source_path).with_suffix('.cpp')
                if cpp_path.exists():
                    files_to_patch.append(str(cpp_path))
                
                patch_file = create_patch(files_to_patch, struct, patch_dir, f"struct_{optimized_count:03d}", 1)
                if patch_file:
                    patch_files.append(patch_file)
                    commit_msg_file = patch_file.with_suffix(".msg")
                    with open(commit_msg_file, "w") as f:
                        f.write(generate_commit_message(struct, padding))
            
            optimized_count += 1
            total_savings += padding

    print(f"\nOptimized {optimized_count} struct(s)/class(es)")
    print(f"Total savings: {total_savings} bytes")
    
    if patch_dir and patch_files:
        from .patch_generator import write_apply_order
        write_apply_order(patch_dir, patch_files)
        print(f"\nGenerated {len(patch_files)} patches in {patch_dir}")
        print(f"See {patch_dir}/APPLY_ORDER.txt for application sequence")
    
    # Print statistics summary
    print(f"\n{'='*60}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total structs analyzed: {len(ordered_structs)}")
    print(f"Structs optimized: {optimized_count}")
    print(f"Structs skipped: {len(ordered_structs) - optimized_count}")
    print(f"Total padding identified: {total_savings} bytes")
    if optimized_count > 0:
        print(f"Average padding per struct: {total_savings // optimized_count} bytes")
    print(f"{'='*60}")
