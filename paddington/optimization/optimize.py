"""Optimization orchestration."""

from pathlib import Path
from typing import List, Dict
from ..utils import find_cpp_files, Logger
from ..core import init_libclang, parse_file
from ..core.dependency_analyzer import topological_sort, has_circular_dependency
from .optimizer import is_leaf_struct, needs_optimization, get_optimal_member_order
from .rewriter import rewrite_struct_definition, rewrite_constructors, write_file


def optimize_files(
    path: Path,
    dry_run: bool = True,
    force: bool = False,
    update_signatures: bool = False,
    verbosity: int = 1,
):
    """Optimize struct padding in C++ files.

    Args:
        path: File or directory to optimize
        dry_run: If True, only report what would be done
        force: If True, reorder even if no size savings
        update_signatures: If True, update constructor signatures and call sites
        verbosity: Logging verbosity level
    """
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

    if not update_signatures:
        log.info(
            "Note: Only updating initializer lists. Use --update-signatures to also update constructor signatures and call sites."
        )

    # Group structs by file
    file_structs: Dict[str, List] = {}
    all_structs = []

    for file in files:
        try:
            log.debug(f"Parsing {file}")
            structs = parse_file(file)

            for struct in structs:
                if struct.file_path not in file_structs:
                    file_structs[struct.file_path] = []
                file_structs[struct.file_path].append(struct)
                all_structs.append(struct)
        except Exception as e:
            log.error(f"Error parsing {file}: {e}")

    # Sort structs in dependency order (bottom-up)
    log.debug(f"Sorting {len(all_structs)} structs by dependencies")
    sorted_structs = topological_sort(all_structs)

    # Check for circular dependencies
    if has_circular_dependency(all_structs):
        log.warning(
            "Circular dependencies detected - some structs may not be optimized"
        )

    # Build set of all struct names for leaf detection
    all_struct_names = {s.name for s in all_structs}

    # Optimize in dependency order
    optimized_count = 0
    total_savings = 0

    for struct in sorted_structs:
        file_path = struct.file_path

        # Check if it's a leaf or all dependencies are optimized
        if not is_leaf_struct(struct, all_struct_names):
            log.debug(f"Processing nested struct {struct.name}")

        # Templates need --force flag since we can't calculate size savings
        if struct.is_template and not force:
            log.debug(
                f"Skipping template {struct.name}: use --force to reorder template definitions"
            )
            continue

        # Check if optimization is needed
        has_savings = needs_optimization(struct)

        if not has_savings and not force and not struct.is_template:
            log.debug(f"Skipping {struct.name}: already optimal")
            continue

        # Calculate savings
        optimal_size = struct.calculate_optimal_size()
        savings = struct.total_size - optimal_size if not struct.is_template else 0

        type_name = "class" if struct.is_class else "struct"
        if struct.is_template:
            type_name = f"template {type_name}"

        if savings > 0:
            log.info(
                f"Optimizing {type_name} {struct.name}: {struct.total_size} -> {optimal_size} bytes ({savings} saved)"
            )
        else:
            log.info(
                f"Normalizing {type_name} {struct.name} (reordering for consistency)"
            )

        if not dry_run:
            try:
                # Get optimal order
                new_order = get_optimal_member_order(struct)

                # Step 1: Rewrite struct definition
                content = rewrite_struct_definition(file_path, struct, new_order)
                write_file(file_path, content)

                # Step 2: Rewrite constructors (reads updated file)
                # Note: Currently only updates initializer lists, not signatures
                # TODO: If update_signatures=True, also reorder constructor parameters
                content = rewrite_constructors(file_path, struct, new_order)
                write_file(file_path, content)

                # Step 3: Rewrite aggregate initializations (reads updated file)
                from .aggregate_rewriter import rewrite_aggregate_initializations

                content = rewrite_aggregate_initializations(
                    file_path, struct, new_order
                )
                write_file(file_path, content)

                log.info(f"Updated {file_path}")
            except Exception as e:
                log.error(f"Error optimizing {struct.name}: {e}")
                import traceback

                log.debug(traceback.format_exc())
                continue

        optimized_count += 1
        total_savings += savings

    mode = "Would optimize" if dry_run else "Optimized"
    print(f"\n{mode} {optimized_count} struct(s)/class(es)")
    print(f"Total savings: {total_savings} bytes")

    if dry_run:
        print("\nRun with --apply to make changes")
