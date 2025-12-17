"""Main analysis orchestration."""

import hashlib
from pathlib import Path
from typing import Optional, List
from ..utils import Logger
from ..core import parse_object_files
from .reporter import report_analysis


def deduplicate_objfiles(objfiles: List[Path], log) -> List[Path]:
    """Deduplicate .o files by full content hash."""
    log.info("Deduplicating .o files by content...")
    
    seen_hashes = {}
    unique = []
    
    for idx, objfile in enumerate(objfiles, 1):
        if idx % 100 == 0:
            log.info(f"  Hashing: {idx}/{len(objfiles)}")
        
        try:
            # Hash full file
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


def analyze_files(
    path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    cache_dir: Optional[Path] = None,
    deduplicate: bool = False,
    verbosity: int = 1,
) -> None:
    """Analyze object files for struct padding."""
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
    log.info(f"Finding .o files in {path}...")
    if path.is_file():
        objfiles = [path]
    else:
        objfiles = list(path.rglob("*.o"))
    
    log.info(f"Found {len(objfiles)} .o files")

    if not objfiles:
        log.error(f"No .o files found in {path}")
        return

    # Apply filters
    if include_patterns or exclude_patterns:
        log.info("Applying filters...")
        from ..utils.file_filter import filter_files
        original_count = len(objfiles)
        objfiles = filter_files(objfiles, include_patterns, exclude_patterns)
        log.info(f"Filtered {original_count} files to {len(objfiles)} files")

    # Deduplicate by content
    if deduplicate:
        objfiles = deduplicate_objfiles(objfiles, log)

    log.info(f"Analyzing {len(objfiles)} object files...")
    
    all_structs = parse_object_files(objfiles, cache_dir, log)
    
    report_analysis(all_structs, verbosity)
