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
        objfiles = list(path.rglob("*.o"))
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
        extractor = MockExtractor()  # TODO: Use real PaholeExtractor
        log.info("Extractor: pahole (mock)")
    else:
        # Auto-select based on platform
        import sys
        if sys.platform == 'darwin':
            from implementation.pipeline.extraction import MachoExtractor
            extractor = MachoExtractor()
            log.info("Extractor: MachoExtractor (macOS)")
        else:
            from implementation.pipeline.extraction.dwarf import DwarfExtractor
            extractor = DwarfExtractor()
            log.info("Extractor: DwarfExtractor (Linux)")
    
    if args.transformer == "srcml":
        from implementation.pipeline.transformation import SrcMLTransformer
        transformer = SrcMLTransformer()
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
                                   struct_names=args.struct_names or [])
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
        log.info(f"Extracted {len(structs)} structs")
        
        log.debug("Stage 2: Analyzing structs...")
        optimization_plans = analysis_stage.process(structs)
        log.info(f"Analyzed {len(optimization_plans)} structs")
        
        # Continue with full pipeline
        log.debug("Stage 3-5: Planning, Transformation, Output...")
        results = pipeline.run(objfiles)
        log.info(f"Pipeline complete: {len(results)} changes")
        
        _report_optimization(results, optimization_plans, args.verbose, log)
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
    import fnmatch
    
    if include:
        files = [f for f in files if any(fnmatch.fnmatch(str(f), pattern) for pattern in include)]
    if exclude:
        files = [f for f in files if not any(fnmatch.fnmatch(str(f), pattern) for pattern in exclude)]
    return files


def _report_optimization(results, optimization_plans, verbosity: int, log):
    """Report optimization results."""
    log.user("Optimization complete: {} changes applied".format(len(results)))
    
    # Report skipped structs
    skipped_plans = [plan for plan in optimization_plans if plan.skip_reason]
    optimized_plans = [plan for plan in optimization_plans if not plan.skip_reason]
    
    log.info(f"Summary: {len(optimized_plans)} optimized, {len(skipped_plans)} skipped")
    
    total_savings = sum(p.padding_saved for p in optimized_plans)
    log.info(f"Total padding saved: {total_savings} bytes")
    
    for plan in skipped_plans:
        log.info(f"SKIPPED {plan.struct.name}: {plan.skip_reason}")
    
    for plan in optimized_plans:
        if plan.padding_saved > 0:
            log.info(f"Optimized {plan.struct.name}: saved {plan.padding_saved} bytes")
            log.debug(f"  File: {plan.struct.file_path}")
    
    for result in results:
        log.info(f"  Modified: {result.file_path}")
