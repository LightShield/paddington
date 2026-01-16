"""Optimize operation - optimize structs to minimize padding."""

from pathlib import Path
from typing import List, Optional


def run(args):
    """Run optimize operation.
    
    Args:
        args: Parsed command-line arguments with:
            - path: Path to object files
            - apply: Whether to apply changes
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
    
    # Find object files
    path = Path(args.path)
    if path.is_file():
        objfiles = [path]
    else:
        objfiles = list(path.rglob("*.o"))
    
    # Apply filters
    if args.include or args.exclude:
        objfiles = _filter_files(objfiles, args.include, args.exclude)
    
    print(f"Found {len(objfiles)} object files")
    
    # Select providers
    if args.extractor == "pahole":
        extractor = MockExtractor()  # TODO: Use real PaholeExtractor
    else:
        from implementation.pipeline.extraction.dwarf import DwarfExtractor
        extractor = DwarfExtractor()
    
    if args.transformer == "srcml":
        from implementation.pipeline.transformation import SrcMLTransformer
        transformer = SrcMLTransformer()
    else:
        from implementation.pipeline.transformation import LineSwapTransformer
        transformer = LineSwapTransformer()
    
    if args.output == "patch":
        from implementation.pipeline.output import GitPatchGenerator
        writer = GitPatchGenerator(output_dir=args.patch_dir)
    else:
        from implementation.pipeline.output import DirectFileWriter
        writer = DirectFileWriter(dry_run=not args.apply)
    
    # Build pipeline
    pipeline = Pipeline([
        ExtractionStage(extractor),
        AnalysisStage(min_savings=args.min_savings, 
                      access_modifier_strategy=args.access_modifier_strategy),
        PlanningStage(),
        TransformationStage(transformer),
        OutputStage(writer)
    ])
    
    # Run pipeline
    try:
        results = pipeline.run(objfiles)
        _report_optimization(results, args.verbose)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def _filter_files(files: List[Path], include: Optional[List[str]], exclude: Optional[List[str]]) -> List[Path]:
    """Filter files by patterns."""
    return files


def _report_optimization(results, verbosity: int):
    """Report optimization results."""
    print(f"\nOptimization complete:")
    print(f"  Changes applied: {len(results)}")
    
    if verbosity >= 2:
        for result in results:
            print(f"  {result.file_path}")
