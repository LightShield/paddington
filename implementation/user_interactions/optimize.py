"""Optimize operation - optimize structs to minimize padding."""

from pathlib import Path
from typing import List, Optional


def run(args):
    """Run optimize operation.
    
    Args:
        args: Parsed command-line arguments with:
            - path: Path to object files
            - apply: Whether to apply changes (default: False for dry-run)
            - min_savings: Minimum bytes to optimize
            - access_modifier_strategy: "preserve", "split", or "ignore"
            - extractor: "pahole" or "dwarf"
            - transformer: "srcml" or "line-swap"
            - output: "patch" or "file"
            - patch_dir: Directory for patches
            - include: List of include patterns
            - exclude: List of exclude patterns
            - verbose: Verbosity level
    """
    from implementation.pipeline import Pipeline
    from implementation.pipeline.extraction import ExtractionStage, MockExtractor
    from implementation.pipeline.analysis import AnalysisStage
    from implementation.pipeline.planning import PlanningStage
    from implementation.pipeline.transformation import TransformationStage, MockTransformer
    from implementation.pipeline.output import OutputStage, MockOutputWriter
    from implementation.utils import Logger
    
    # Set up logging
    log = Logger()
    if args.verbose >= 3:
        log.set_level('DEBUG')
    elif args.verbose >= 2:
        log.set_level('INFO')
    elif args.verbose >= 1:
        log.set_level('USER')  # Show user-facing output
    else:
        log.set_level('USER')  # Default: show user output
    
    # Set up log file
    log_file = Path.cwd() / "paddington.log"
    log.set_log_file(str(log_file))
    log.info(f"Logging to {log_file}")
    
    # Show mode
    if args.apply:
        log.user("APPLYING CHANGES")
    else:
        log.user("DRY-RUN MODE: No changes will be made")
    
    # Find object files
    path = Path(args.path)
    log.debug(f"Searching for .o files in: {path}")
    
    if path.is_file():
        objfiles = [path]
        log.debug(f"Single file mode: {path}")
    else:
        # Use os.walk instead of rglob for better performance
        import os
        objfiles = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.o'):
                    objfiles.append(Path(root) / file)
        log.debug(f"Directory mode: found {len(objfiles)} .o files")
    
    # Apply filters
    if args.include or args.exclude:
        original_count = len(objfiles)
        objfiles = _filter_files(objfiles, args.include, args.exclude)
        log.info(f"Filtered {original_count} files to {len(objfiles)} files")
        if args.include:
            log.debug(f"Include patterns: {args.include}")
        if args.exclude:
            log.debug(f"Exclude patterns: {args.exclude}")
    
    log.user(f"Found {len(objfiles)} object files")
    
    # Select providers
    log.debug(f"Selecting providers...")
    
    if args.extractor == "pahole":
        from implementation.pipeline.extraction import PaholeExtractor
        extractor = PaholeExtractor()
        log.info("Extractor: PaholeExtractor (100x faster)")
    elif args.extractor == "dwarf":
        from implementation.pipeline.extraction.dwarf import DwarfExtractor
        extractor = DwarfExtractor()
        log.info("Extractor: DwarfExtractor")
    else:  # auto
        # Auto-select best extractor for platform
        import sys
        if sys.platform == 'darwin':
            from implementation.pipeline.extraction import MachoExtractor
            extractor = MachoExtractor()
            log.info("Extractor: MachoExtractor (auto-selected for macOS)")
        else:
            # Linux: Use pahole (100x faster than dwarf)
            from implementation.pipeline.extraction import PaholeExtractor
            extractor = PaholeExtractor()
            log.info("Extractor: PaholeExtractor (auto-selected for Linux, 100x faster)")
    
    if args.transformer == "srcml":
        from implementation.pipeline.transformation import SrcMLTransformer
        transformer = SrcMLTransformer(source_root=args.source_root)
        log.info("Transformer: srcML (recommended)")
    else:
        from implementation.pipeline.transformation import LineSwapTransformer
        transformer = LineSwapTransformer()
        log.info("Transformer: line-swap")
        transformer = LineSwapTransformer()
    
    if args.output == "patch":
        from implementation.pipeline.output import GitPatchGenerator
        writer = GitPatchGenerator(output_dir=args.patch_dir)
    else:
        from implementation.pipeline.output import DirectFileWriter
        writer = DirectFileWriter(dry_run=not args.apply)
    
    # Build pipeline
    extraction_stage = ExtractionStage(extractor)
    analysis_stage = AnalysisStage(min_savings=args.min_savings, 
                                   access_modifier_strategy=args.access_modifier_strategy,
                                   struct_names=args.struct_names or [],
                                   source_root=str(args.source_root) if args.source_root else None,
                                   exclude_patterns=args.exclude or [],
                                   workspace_dir=str(args.workspace))
    planning_stage = PlanningStage(access_modifier_strategy=args.access_modifier_strategy)
    transformation_stage = TransformationStage(transformer)
    output_stage = OutputStage(writer)
    
    pipeline = Pipeline([
        extraction_stage,
        analysis_stage,
        planning_stage,
        transformation_stage,
        output_stage
    ])
    
    # Run pipeline
    log.debug("Building pipeline...")
    log.debug(f"  1. Extraction ({extractor.__class__.__name__})")
    log.debug(f"  2. Analysis (min_savings={args.min_savings}, strategy={args.access_modifier_strategy})")
    log.debug(f"  3. Planning")
    log.debug(f"  4. Transformation ({transformer.__class__.__name__})")
    log.debug(f"  5. Output ({writer.__class__.__name__})")
    
    try:
        log.info("Starting pipeline...")
        
        # Run extraction and analysis separately to capture optimization plans
        log.debug("Stage 1: Extracting structs...")
        structs = extraction_stage.process(objfiles)
        
        # Get extraction stats
        extraction_stats = {}
        if hasattr(extractor, 'get_extraction_stats'):
            extraction_stats = extractor.get_extraction_stats()
        
        structs_after_extraction = len(structs)
        log.info(f"Extracted {structs_after_extraction} structs")
        
        # Filter structs by file_path using exclude patterns
        structs_before_filter = len(structs)
        if args.exclude:
            log.debug(f"Filtering {structs_before_filter} structs with patterns: {args.exclude}")
            structs = _filter_structs(structs, args.exclude)
            structs_filtered = structs_before_filter - len(structs)
            if structs_filtered > 0:
                log.info(f"Filtered out {structs_filtered} structs by file path")
            else:
                log.debug("No structs filtered by file path")
        else:
            structs_filtered = 0
        
        # Pass compilation data to planning stage if available
        compilation_data_count = 0
        if hasattr(extractor, 'get_compilation_data'):
            compilation_data = extractor.get_compilation_data()
            compilation_data_count = len(compilation_data)
            log.info(f"Extractor provided compilation data for {compilation_data_count} structs")
            if compilation_data and hasattr(planning_stage, 'set_compilation_data'):
                planning_stage.set_compilation_data(compilation_data)
                log.info(f"Passed compilation data to planning stage")
            elif not compilation_data:
                log.warning("Compilation data is empty - constructor modifications will be skipped")
        else:
            log.warning("Extractor does not provide compilation data")
        
        log.debug("Stage 2: Analyzing structs...")
        structs_before_analysis = len(structs)
        optimization_plans = analysis_stage.process(structs)
        structs_after_analysis = len(optimization_plans)
        system_headers_filtered = structs_before_analysis - structs_after_analysis
        log.info(f"Analyzed {structs_after_analysis} structs")
        
        # Run remaining stages manually (not via pipeline.run) to preserve compilation data
        log.debug("Stage 3: Planning...")
        modifications = planning_stage.process(optimization_plans)
        modifications_planned = len(modifications)
        log.info(f"Planned {modifications_planned} modifications")
        
        log.debug("Stage 4: Transformation...")
        transformed = transformation_stage.process(modifications)
        sources_transformed = len(transformed)
        log.info(f"Transformed {sources_transformed} sources")
        
        log.debug("Stage 5: Output...")
        results = output_stage.process(transformed)
        log.info(f"Pipeline complete: {len(results)} changes")
        
        # Collect stats for report
        unique_patches = len(set(r.patch_path for r in results if hasattr(r, 'patch_path')))
        
        stats = {
            'objfiles_count': len(objfiles),
            'structs_raw': extraction_stats.get('total_before_dedup', structs_after_extraction),
            'structs_after_dedup': extraction_stats.get('total_after_dedup', structs_after_extraction),
            'duplicates_removed': extraction_stats.get('duplicates_removed', 0),
            'structs_after_filter': structs_before_analysis,
            'structs_filtered': structs_filtered,
            'system_headers_filtered': system_headers_filtered,
            'structs_analyzed': len(optimization_plans),
            'compilation_data_count': compilation_data_count,
            'modifications_planned': modifications_planned,
            'sources_transformed': sources_transformed,
            'transformation_failures': modifications_planned - sources_transformed,
            'patches_created': unique_patches if unique_patches > 0 else len(results),
            'files_modified': len(results)
        }
        
        _report_optimization(results, optimization_plans, args.verbose, log, stats)
    except Exception as e:
        log.error(f"Pipeline failed: {e}")
        if args.verbose >= 3:
            import traceback
            traceback.print_exc()
        return 1
    
    log.info("Optimization complete")
    return 0


def _filter_files(files: List[Path], include: Optional[List[str]], exclude: Optional[List[str]]) -> List[Path]:
    """Filter files by patterns."""
    if include:
        import fnmatch
        files = [f for f in files if any(fnmatch.fnmatch(str(f), pattern) for pattern in include)]
    
    if exclude:
        from implementation.utils.path_exclusion import should_exclude_path
        files = [f for f in files if not should_exclude_path(f, exclude)]
    
    return files


def _filter_structs(structs, exclude: Optional[List[str]]):
    """Filter structs by file_path using exclude patterns."""
    if not exclude:
        return structs
    
    from implementation.utils.path_exclusion import should_exclude_path
    filtered = []
    for struct in structs:
        if not struct.file_path:
            filtered.append(struct)
            continue
        
        if not should_exclude_path(Path(struct.file_path), exclude):
            filtered.append(struct)
    
    return filtered


def _report_optimization(results, optimization_plans, verbosity: int, log, stats: dict = None):
    """Report optimization results."""
    from collections import Counter
    
    log.user("Optimization complete: {} changes applied".format(len(results)))
    
    # Report skipped structs
    skipped_plans = [plan for plan in optimization_plans if plan.skip_reason]
    optimized_plans = [plan for plan in optimization_plans if not plan.skip_reason]
    
    # Get struct names that actually got patches
    patched_files = {result.file_path for result in results}
    actually_patched = [p for p in optimized_plans if p.struct.file_path in patched_files]
    
    # Count structs that have padding_saved > 0 (actually benefited from optimization)
    structs_with_savings = [p for p in optimization_plans if p.padding_saved > 0]
    
    # Calculate total savings from ALL plans (including those that were analyzed but not patched)
    total_savings = sum(p.padding_saved for p in optimization_plans if p.padding_saved > 0)
    
    log.info(f"Summary: {len(actually_patched)} patched, {len(optimized_plans) - len(actually_patched)} analyzed but not patched, {len(skipped_plans)} skipped")
    log.info(f"Total padding saved: {total_savings} bytes")
    
    # Generate detailed summary report
    skip_reasons = Counter(plan.skip_reason for plan in skipped_plans)
    
    # Categorize skip reasons
    cannot_optimize = ['only 0 member(s)', 'only 1 member(s)']
    already_optimal_reasons = ['already optimal']
    unhandled_cases = ['preprocessor directives', 'aggregate initialization', 'constructor dependencies']
    
    cannot_optimize_count = sum(skip_reasons[r] for r in cannot_optimize if r in skip_reasons)
    already_optimal_count = sum(skip_reasons[r] for r in already_optimal_reasons if r in skip_reasons)
    unhandled_count = sum(skip_reasons[r] for r in unhandled_cases if r in skip_reasons)
    
    report_lines = [
        "",
        "=" * 80,
        "PADDINGTON OPTIMIZATION SUMMARY - PIPELINE FLOW",
        "=" * 80,
        "",
    ]
    
    # Add pipeline flow if stats available
    if stats:
        report_lines.extend([
            "EXTRACTION STAGE:",
            f"  From {stats['objfiles_count']} .o files",
            f"  → Extracted {stats['structs_raw']} structs (raw)",
            f"  → After deduplication: {stats['structs_after_dedup']} structs ({stats['duplicates_removed']} duplicates removed)",
            f"  → After path exclusions: {stats['structs_after_filter']} structs ({stats['structs_filtered']} excluded)",
            f"  → After system header filter: {stats['structs_analyzed']} structs ({stats['system_headers_filtered']} system headers removed)",
            "",
            "ANALYSIS STAGE:",
            f"  Input: {stats['structs_analyzed']} structs",
            f"  → Cannot optimize: {cannot_optimize_count} structs (0 or 1 members)",
            f"  → Already optimal: {already_optimal_count} structs (no reordering needed)",
            f"  → Unhandled cases: {unhandled_count} structs (preprocessor/aggregate/constructor)",
            f"  → Needs optimization: {len(optimized_plans)} structs",
            "",
            "  Skip reasons (cannot optimize):",
        ])
        
        for reason in cannot_optimize:
            if reason in skip_reasons:
                report_lines.append(f"    {skip_reasons[reason]:5d} - {reason}")
        
        report_lines.append("")
        report_lines.append("  Skip reasons (already optimal):")
        for reason in already_optimal_reasons:
            if reason in skip_reasons:
                report_lines.append(f"    {skip_reasons[reason]:5d} - {reason}")
        
        report_lines.append("")
        report_lines.append("  Skip reasons (unhandled cases - potential future improvements):")
        
        # Add explanations for each unhandled case
        reason_explanations = {
            'preprocessor directives': 'conditional members affect struct layout',
            'aggregate initialization': 'positional init {a,b,c} breaks with reordering',
            'constructor dependencies': 'member init order matters (e.g., buffer(size))'
        }
        
        for reason in unhandled_cases:
            if reason in skip_reasons:
                explanation = reason_explanations.get(reason, '')
                if explanation:
                    report_lines.append(f"    {skip_reasons[reason]:5d} - {reason} ({explanation})")
                else:
                    report_lines.append(f"    {skip_reasons[reason]:5d} - {reason}")
        
        # Add any other skip reasons
        other_reasons = [r for r in skip_reasons if r not in cannot_optimize + already_optimal_reasons + unhandled_cases]
        if other_reasons:
            report_lines.append("")
            report_lines.append("  Other skip reasons:")
            for reason in other_reasons:
                report_lines.append(f"    {skip_reasons[reason]:5d} - {reason}")
        
        report_lines.extend([
            "",
            "PLANNING STAGE:",
            f"  Input: {len(optimized_plans)} structs needing optimization",
            f"  → Modifications planned: {stats['modifications_planned']} (includes .h and .cpp files)",
            f"  → Compilation data available: {stats['compilation_data_count']} structs have .cpp mappings",
            "",
            "TRANSFORMATION STAGE:",
            f"  Input: {stats['modifications_planned']} modifications",
            f"  → Successfully transformed: {stats['sources_transformed']} sources",
            f"  → Transformation failures: {stats['transformation_failures']} sources",
            f"  → Success rate: {stats['sources_transformed']*100//stats['modifications_planned'] if stats['modifications_planned'] > 0 else 0}%",
            "",
            "OUTPUT STAGE:",
            f"  Input: {stats['sources_transformed']} transformed sources",
            f"  → Patches created: {stats['patches_created']} patch files",
            f"  → Files modified: {stats['files_modified']} files",
            f"  → Files per patch: {stats['files_modified'] / stats['patches_created']:.1f} average" if stats['patches_created'] > 0 else "  → Files per patch: N/A",
            "",
            "FINAL RESULTS:",
            f"  Total padding saved: {total_savings} bytes",
            f"  Structs with padding savings: {len(structs_with_savings)}",
            f"  Average savings per struct: {total_savings // len(structs_with_savings) if structs_with_savings else 0} bytes",
        ])
    else:
        report_lines.extend([
            "EXTRACTION:",
            f"  Structs extracted from .o files: {stats['structs_extracted']}",
            f"  Structs filtered by exclusions: {stats['structs_filtered']}",
            f"  Structs analyzed: {stats['structs_analyzed']}",
            "",
            "ANALYSIS:",
            f"  Structs with optimization potential: {len(optimized_plans)}",
            f"  Structs skipped: {len(skipped_plans)}",
            "",
            "SKIP REASONS:",
        ])
        
        for reason, count in skip_reasons.most_common():
            report_lines.append(f"    {count:5d} - {reason}")
        
        report_lines.extend([
            "",
            "PLANNING:",
            f"  Modifications planned: {stats['modifications_planned']}",
            f"  Compilation data available: {stats['compilation_data_count']} structs",
            "",
            "TRANSFORMATION:",
            f"  Sources transformed: {stats['sources_transformed']}",
            f"  Transformation failures: {stats['transformation_failures']}",
            f"  Success rate: {stats['sources_transformed']*100//stats['modifications_planned'] if stats['modifications_planned'] > 0 else 0}%",
            "",
            "OUTPUT:",
            f"  Patches created: {stats['patches_created']}",
            f"  Files modified: {len(patched_files)}",
            "",
            "RESULTS:",
            f"  Total padding saved: {total_savings} bytes",
            f"  Average per struct: {total_savings // len(actually_patched) if actually_patched else 0} bytes",
        ])
    
    report_lines.extend(["", "=" * 80, ""])
    
    # Write to console
    for line in report_lines:
        log.user(line)
    
    # Write to summary file
    try:
        from pathlib import Path
        summary_file = Path.cwd() / "paddington_summary.txt"
        with open(summary_file, 'w') as f:
            f.write('\n'.join(report_lines))
        log.info(f"Summary report written to: {summary_file}")
    except Exception as e:
        log.warning(f"Failed to write summary file: {e}")
    
    for plan in skipped_plans:
        log.user(f"SKIPPED {plan.struct.name}: {plan.skip_reason}")
    
    # Only report structs that actually got patches
    for plan in actually_patched:
        if plan.padding_saved > 0:
            log.user(f"Optimized {plan.struct.name}: saved {plan.padding_saved} bytes")
            log.debug(f"  File: {plan.struct.file_path}")
    
    # Report analyzed but not patched (e.g., template instantiations)
    not_patched = len(optimized_plans) - len(actually_patched)
    if not_patched > 0:
        log.info(f"Note: {not_patched} structs analyzed but not patched (likely template instantiations without source)")
    
    for result in results:
        log.info(f"  Modified: {result.file_path}")
