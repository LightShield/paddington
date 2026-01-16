"""Analysis stage with iterative size propagation."""

from typing import List, Dict
from ..stage import Stage
from ...struct_data.struct_info import StructInfo
from ...struct_data.optimization_plan import OptimizationPlan
from ...padding_analysis.dependency_graph import build_dependency_graph, topological_sort
from ...padding_analysis.padding_calculator import calculate_padding
from ...padding_analysis.member_reorderer import get_optimal_order
from ...padding_analysis.size_calculator import calculate_struct_size


class AnalysisStage(Stage[List[StructInfo], List[OptimizationPlan]]):
    """Analyze structs iteratively with size propagation."""
    
    def __init__(self, min_savings: int = 0, access_modifier_strategy: str = "preserve"):
        self.min_savings = min_savings
        self.access_modifier_strategy = access_modifier_strategy
    
    def process(self, structs: List[StructInfo]) -> List[OptimizationPlan]:
        """Process structs in dependency order with size propagation."""
        if not structs:
            return []
        
        # Build dependency graph and sort
        graph = build_dependency_graph(structs)
        ordered_names = topological_sort(graph)
        struct_map = {s.name: s for s in structs}
        
        # Initialize type sizes with original sizes
        type_sizes: Dict[str, int] = {s.name: s.size for s in structs}
        plans = []
        
        # Iterative analysis in dependency order
        for struct_name in ordered_names:
            if struct_name not in struct_map:
                continue
            
            struct = struct_map[struct_name]
            
            # Update member sizes from type table
            updated_members = []
            for member in struct.members:
                if member.type in type_sizes:
                    # Use potentially updated size
                    updated_member = member.__class__(
                        name=member.name,
                        type=member.type,
                        size=type_sizes[member.type],
                        optimized_size=member.optimized_size,
                        offset=member.offset,
                        access_modifier=member.access_modifier,
                        locked=member.locked
                    )
                    updated_members.append(updated_member)
                else:
                    updated_members.append(member)
            
            # Calculate padding
            actual_size = calculate_struct_size(updated_members)
            padding = calculate_padding(updated_members, actual_size)
            
            # Check if should optimize
            if padding < self.min_savings or struct.ignore:
                skip_reason = f"padding {padding} < min_savings {self.min_savings}" if padding < self.min_savings else "marked ignore"
                plan = OptimizationPlan(
                    struct=struct,
                    original_order=tuple(updated_members),
                    optimal_order=tuple(updated_members),
                    padding_saved=0,
                    skip_reason=skip_reason
                )
                type_sizes[struct_name] = actual_size
            else:
                # Get optimal order
                optimal_members = get_optimal_order(updated_members, self.access_modifier_strategy)
                optimal_size = calculate_struct_size(optimal_members)
                padding_saved = actual_size - optimal_size
                
                plan = OptimizationPlan(
                    struct=struct,
                    original_order=tuple(updated_members),
                    optimal_order=tuple(optimal_members),
                    padding_saved=padding_saved,
                    skip_reason=None
                )
                type_sizes[struct_name] = optimal_size
            
            plans.append(plan)
        
        return plans
    
    def validate_input(self, structs: List[StructInfo]) -> bool:
        """Validate input structs."""
        return isinstance(structs, list) and all(isinstance(s, StructInfo) for s in structs)
