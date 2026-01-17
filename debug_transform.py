#!/usr/bin/env python3
"""Debug script to see what the transformation pipeline produces."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from implementation.pipeline.extraction.dwarf import DwarfExtractor
from implementation.pipeline.analysis.stage import AnalysisStage
from implementation.pipeline.planning.stage import PlanningStage
from implementation.pipeline.transformation.line_swap import LineSwapTransformer

def main():
    # Extract structs
    extractor = DwarfExtractor()
    structs = extractor.extract([Path("test_transform.o")])
    print(f"Extracted {len(structs)} structs:")
    for struct in structs:
        print(f"  {struct.name}: {struct.size} bytes, {len(struct.members)} members")
        for member in struct.members:
            print(f"    {member.name}: {member.type} at offset {member.offset}")
    
    # Analyze for optimization
    analyzer = AnalysisStage(min_savings=0, access_modifier_strategy="preserve")
    plans = analyzer.process(structs)
    print(f"\nGenerated {len(plans)} optimization plans:")
    for plan in plans:
        if plan.skip_reason:
            print(f"  SKIPPED {plan.struct.name}: {plan.skip_reason}")
        else:
            print(f"  {plan.struct.name}: save {plan.padding_saved} bytes")
            print(f"    Original: {[m.name for m in plan.original_order]}")
            print(f"    Optimal:  {[m.name for m in plan.optimal_order]}")
    
    # Convert to source modifications
    planner = PlanningStage()
    modifications = planner.process(plans)
    print(f"\nGenerated {len(modifications)} source modifications:")
    for mod in modifications:
        print(f"  File: {mod.file_path}")
        print(f"  Struct: {mod.struct_name}")
        for m in mod.modifications:
            print(f"    {m.type}: {m.old_content} -> {m.new_content}")
    
    # Transform source
    transformer = LineSwapTransformer()
    transformed = transformer.transform(modifications)
    print(f"\nGenerated {len(transformed)} transformed sources:")
    for t in transformed:
        print(f"  File: {t.file_path}")
        print(f"  Original length: {len(t.original_content)}")
        print(f"  New length: {len(t.new_content)}")
        print(f"  Changed: {t.original_content != t.new_content}")
        if t.original_content != t.new_content:
            print("  DIFF:")
            print("    Original:")
            for i, line in enumerate(t.original_content.split('\n')):
                print(f"      {i+1}: {line}")
            print("    New:")
            for i, line in enumerate(t.new_content.split('\n')):
                print(f"      {i+1}: {line}")

if __name__ == "__main__":
    main()