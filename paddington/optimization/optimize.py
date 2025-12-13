"""Optimization orchestration."""

from pathlib import Path
from typing import List, Dict, Optional
from ..utils import find_cpp_files, Logger
from ..utils.validation import (
    validate_path_exists,
    validate_libclang_available,
    validate_cpp_files_exist,
    validate_git_repo,
)
from ..core import init_libclang, parse_file
from ..core.dependency_analyzer import (
    topological_sort,
    has_circular_dependency,
    identify_dependency_trees,
)
from .optimizer import is_leaf_struct, needs_optimization, get_optimal_member_order
from .rewriter import rewrite_struct_definition, rewrite_constructors, write_file
from .patch_generator import create_patch, generate_commit_message, write_apply_order


def optimize_files(
    path: Path,
    dry_run: bool = True,
    force: bool = False,
    update_signatures: bool = False,
    patch_dir: Optional[Path] = None,
    build_command: Optional[str] = None,
    verify: bool = False,
    verbosity: int = 1,
) -> None:
    """Optimize struct padding in C++ files.

    Args:
        path: File or directory to optimize
        dry_run: If True, only report what would be done
        force: If True, reorder even if no size savings
        update_signatures: If True, update constructor signatures and call sites
        patch_dir: If provided, generate patches instead of modifying files
        build_command: If provided, run after each optimization to verify build
        verify: If True, use compilation database to verify each file
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

    # Validate inputs
    try:
        validate_path_exists(path)
        validate_libclang_available()
        validate_cpp_files_exist(path)
        
        # Validate git repo if patch generation requested
        if patch_dir:
            validate_git_repo(path)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        log.error(str(e))
        return

    # Patch mode implies not dry-run
    if patch_dir:
        dry_run = False
        patch_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Generating patches in {patch_dir}")

    files = find_cpp_files(path)
    
    # Check for compilation database
    from ..utils.compilation_database import (
        find_compilation_database,
        get_files_from_compilation_database,
    )
    
    compile_db = find_compilation_database(path)
    if compile_db:
        log.info(f"Using compilation database: {compile_db}")
        db_files = get_files_from_compilation_database(compile_db)
        if db_files:
            files = db_files
            log.debug(f"Using {len(files)} files from compilation database")

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
            
            # Get compile args from database if available
            compile_args = None
            if compile_db:
                from ..utils.compilation_database import get_compile_args_for_file
                compile_args = get_compile_args_for_file(compile_db, file)
            
            structs = parse_file(file, compile_args)

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

    # Identify dependency trees for patch generation
    tree_assignment = identify_dependency_trees(all_structs)
    tree_order = {}  # Track order within each tree
    patch_files = []  # Track generated patches

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
                from .smart_pointer_rewriter import rewrite_smart_pointer_calls

                content = rewrite_aggregate_initializations(
                    file_path, struct, new_order
                )
                write_file(file_path, content)

                # Step 4: Check smart pointer calls (currently no-op)
                content = rewrite_smart_pointer_calls(file_path, struct, new_order)
                write_file(file_path, content)

                log.info(f"Updated {file_path}")
                
                # Verify build if requested
                effective_build_command = build_command
                
                # If --verify flag, try to get build command from compilation database
                if verify and compile_db and not effective_build_command:
                    from ..utils.compilation_database import get_build_command_for_file
                    effective_build_command = get_build_command_for_file(compile_db, Path(file_path))
                    if effective_build_command:
                        log.debug(f"Using build command from compilation database")
                
                if effective_build_command:
                    from ..utils.build_verifier import run_build_command
                    
                    build_dir = Path(file_path).parent
                    if not run_build_command(effective_build_command, build_dir):
                        log.error(f"Build failed after optimizing {struct.name}")
                        log.error("Rolling back changes...")
                        # TODO: Implement rollback
                        return
                        
            except Exception as e:
                log.error(f"Error optimizing {struct.name}: {e}")
                import traceback

                log.debug(traceback.format_exc())
                continue

        # Generate patch if in patch mode
        if patch_dir and not dry_run:
            tree_id = tree_assignment.get(struct.name, 0)
            tree_key = f"tree_{tree_id:03d}"
            
            # Track order within tree
            if tree_key not in tree_order:
                tree_order[tree_key] = 0
            tree_order[tree_key] += 1
            
            patch_file = create_patch(
                file_path, struct, patch_dir, tree_key, tree_order[tree_key]
            )
            
            if patch_file:
                patch_files.append(patch_file)
                
                # Write commit message
                commit_msg_file = patch_file.with_suffix(".msg")
                with open(commit_msg_file, "w") as f:
                    f.write(generate_commit_message(struct, savings))

        optimized_count += 1
        total_savings += savings

    mode = "Would optimize" if dry_run else "Optimized"
    print(f"\n{mode} {optimized_count} struct(s)/class(es)")
    print(f"Total savings: {total_savings} bytes")

    if patch_dir and patch_files:
        write_apply_order(patch_dir, patch_files)
        print(f"\nGenerated {len(patch_files)} patches in {patch_dir}")
        print(f"See {patch_dir}/APPLY_ORDER.txt for application sequence")

    if dry_run:
        print("\nRun with --apply to make changes")
