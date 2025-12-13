"""Reporting utilities for analysis results."""
from typing import List
from .models import StructInfo

def report_analysis(structs: List[StructInfo], verbosity: int = 1):
    """Report analysis results."""
    total_padding = 0
    total_savings = 0
    optimizable_count = 0
    
    for struct in structs:
        padding = struct.calculate_padding()
        optimal_size = struct.calculate_optimal_size()
        savings = struct.total_size - optimal_size
        
        total_padding += padding
        
        if savings > 0:
            optimizable_count += 1
            total_savings += savings
            
            if verbosity >= 1:
                print(f"[PADDING] struct {struct.name}: {struct.total_size} bytes "
                      f"({padding} bytes padding, {savings} bytes savable)")
            
            if verbosity >= 2:
                print(f"  Location: {struct.file_path}:{struct.line}")
                print(f"  Optimal size: {optimal_size} bytes")
                print(f"  Members: {', '.join(m.name for m in struct.members)}")
        elif verbosity >= 3:
            print(f"[OK] struct {struct.name}: {struct.total_size} bytes (already optimal)")
    
    print(f"\nTotal: {len(structs)} structs analyzed, {optimizable_count} can be optimized")
    print(f"Total padding: {total_padding} bytes")
    print(f"Potential savings: {total_savings} bytes")
