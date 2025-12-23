"""Reporting utilities for analysis results."""

from typing import List
from ..core import StructInfo
from ..utils import Logger


def report_analysis(structs: List[StructInfo], verbosity: int = 1) -> None:
    """Report analysis results.

    Args:
        structs: List of analyzed struct/class definitions
        verbosity: Logging verbosity level (1=minimal, 2=detailed, 3=debug)
    """
    log = Logger()

    total_padding = 0
    total_savings = 0
    optimizable_count = 0

    for struct in structs:
        if not struct.members or struct.size == 0:
            continue
        if any(m.size == 0 for m in struct.members):
            continue
            
        padding = struct.calculate_padding()
        optimal_size = struct.calculate_optimal_size()
        savings = struct.size - optimal_size

        total_padding += padding

        if savings > 0:
            optimizable_count += 1
            total_savings += savings

            if verbosity >= 1:
                print(
                    f"[PADDING] {struct.name}: {struct.size} bytes "
                    f"({padding} bytes padding, {savings} bytes savable)"
                )

            if verbosity >= 2:
                log.info(f"Optimal size: {optimal_size} bytes")
                log.info(f"Members: {', '.join(m.name for m in struct.members)}")
        elif verbosity >= 3:
            log.debug(
                f"{struct.name}: {struct.size} bytes (already optimal)"
            )

    print(
        f"\nTotal: {len(structs)} struct(s)/class(es) analyzed, {optimizable_count} can be optimized"
    )
    print(f"Total padding: {total_padding} bytes")
    print(f"Potential savings: {total_savings} bytes")
