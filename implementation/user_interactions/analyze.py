"""Analyze operation - analyze structs for padding waste."""

from pathlib import Path
from typing import List, Optional


def run(args):
    """Run analyze operation.
    
    Args:
        args: Parsed command-line arguments with:
            - path: Path to object files
            - extractor: "pahole" or "dwarf"
            - include: List of include patterns
            - exclude: List of exclude patterns
            - verbose: Verbosity level
    """
    from implementation.pipeline import Pipeline
    from implementation.pipeline.extraction import ExtractionStage, MockExtractor
    from implementation.pipeline.analysis import AnalysisStage
    
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
    
    # Select extractor
    if args.extractor == "pahole":
        # For now, use mock (pahole implementation needs completion)
        extractor = MockExtractor()
    else:
        from implementation.pipeline.extraction.dwarf import DwarfExtractor
        extractor = DwarfExtractor()
    
    # Build pipeline
    pipeline = Pipeline([
        ExtractionStage(extractor),
        AnalysisStage(min_savings=0, access_modifier_strategy="preserve")
    ])
    
    # Run pipeline
    try:
        plans = pipeline.run(objfiles)
        _report_analysis(plans, args.verbose)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


def _filter_files(files: List[Path], include: Optional[List[str]], exclude: Optional[List[str]]) -> List[Path]:
    """Filter files by patterns."""
    # Simple implementation for now
    return files


def _report_analysis(plans, verbosity: int):
    """Report analysis results."""
    optimizable = [p for p in plans if not p.skip_reason]
    skipped = [p for p in plans if p.skip_reason]
    total_savings = sum(p.padding_saved for p in optimizable)
    
    print(f"\nAnalysis Results:")
    print(f"  Total structs: {len(plans)}")
    print(f"  Optimizable: {len(optimizable)}")
    print(f"  Skipped: {len(skipped)}")
    print(f"  Potential savings: {total_savings} bytes")
    
    if verbosity >= 2:
        print(f"\nOptimizable structs:")
        for plan in optimizable:
            print(f"  {plan.struct.name}: {plan.padding_saved} bytes")
    
    if verbosity >= 3:
        print(f"\nSkipped structs:")
        for plan in skipped:
            print(f"  {plan.struct.name}: {plan.skip_reason}")
