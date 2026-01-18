"""Analysis stage with iterative size propagation."""

from typing import List, Dict
from ..stage import Stage
from ...struct_data.struct_info import StructInfo
from ...struct_data.optimization_plan import OptimizationPlan
from ...padding_analysis.dependency_graph import build_dependency_graph, topological_sort
from ...padding_analysis.padding_calculator import calculate_padding
from ...padding_analysis.member_reorderer import get_optimal_order
from ...padding_analysis.size_calculator import calculate_struct_size
from ...padding_analysis.constructor_dependency_detector import detect_constructor_dependencies
from ...padding_analysis.preprocessor_detector import has_preprocessor_directives
from ...padding_analysis.directive_parser import parse_directives


class AnalysisStage(Stage[List[StructInfo], List[OptimizationPlan]]):
    """Analyze structs iteratively with size propagation."""
    
    def __init__(self, min_savings: int = 0, access_modifier_strategy: str = "preserve", source_file: str = "", struct_names: list = None):
        self.min_savings = min_savings
        self.access_modifier_strategy = access_modifier_strategy
        self.source_file = source_file
        self.struct_names = struct_names or []
    
    def process(self, structs: List[StructInfo]) -> List[OptimizationPlan]:
        """Process structs in dependency order with size propagation."""
        if not structs:
            return []
        
        # Filter out system headers
        structs = [s for s in structs if s.file_path and not self._is_system_header(s.file_path)]
        
        # Filter by struct names if specified
        if self.struct_names:
            import fnmatch
            structs = [s for s in structs if any(fnmatch.fnmatch(s.name, pattern) for pattern in self.struct_names)]
        
        if not structs:
            return []
        
        # Parse directives if source file provided
        directives = {}
        if self.source_file:
            directives = parse_directives(self.source_file)
        
        # Filter out ignored structs
        ignored_structs = directives.get('ignored_structs', set())
        filtered_structs = [s for s in structs if s.name not in ignored_structs]
        
        # Build dependency graph and sort
        graph = build_dependency_graph(filtered_structs)
        ordered_names = topological_sort(graph)
        struct_map = {s.name: s for s in filtered_structs}
        
        # Initialize type sizes with original sizes
        type_sizes: Dict[str, int] = {s.name: s.size for s in filtered_structs}
        plans = []
        
        # Iterative analysis in dependency order
        for struct_name in ordered_names:
            if struct_name not in struct_map:
                continue
            
            struct = struct_map[struct_name]
            
            # Update member sizes from type table and apply locked members
            locked_members = directives.get('locked_members', {}).get(struct_name, set())
            updated_members = []
            for member in struct.members:
                is_locked = member.name in locked_members
                if member.type in type_sizes:
                    # Use potentially updated size
                    updated_member = member.__class__(
                        name=member.name,
                        type=member.type,
                        size=type_sizes[member.type],
                        optimized_size=member.optimized_size,
                        offset=member.offset,
                        access_modifier=member.access_modifier,
                        locked=is_locked or member.locked
                    )
                    updated_members.append(updated_member)
                else:
                    updated_member = member.__class__(
                        name=member.name,
                        type=member.type,
                        size=member.size,
                        optimized_size=member.optimized_size,
                        offset=member.offset,
                        access_modifier=member.access_modifier,
                        locked=is_locked or member.locked
                    )
                    updated_members.append(updated_member)
            
            # Calculate padding
            actual_size = calculate_struct_size(updated_members)
            padding = calculate_padding(updated_members, actual_size)
            
            # Check constructor dependencies
            constructor_deps = {}
            if self.source_file:
                constructor_deps = detect_constructor_dependencies(self.source_file, struct_name)
            
            # Check for preprocessor directives
            if struct.file_path and has_preprocessor_directives(struct.file_path, struct_name):
                plan = OptimizationPlan(
                    struct=struct,
                    original_order=tuple(updated_members),
                    optimal_order=tuple(updated_members),
                    padding_saved=0,
                    skip_reason="preprocessor directives"
                )
                plans.append(plan)
                type_sizes[struct_name] = actual_size
                continue
            
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
            elif constructor_deps:
                # Check if reordering would violate constructor dependencies
                optimal_members = get_optimal_order(updated_members, self.access_modifier_strategy)
                if _violates_dependencies(updated_members, optimal_members, constructor_deps):
                    # Try to find a safe reordering that respects dependencies
                    safe_members = _get_dependency_safe_order(updated_members, constructor_deps, self.access_modifier_strategy)
                    if safe_members != updated_members:
                        safe_size = calculate_struct_size(safe_members)
                        padding_saved = actual_size - safe_size
                        plan = OptimizationPlan(
                            struct=struct,
                            original_order=tuple(updated_members),
                            optimal_order=tuple(safe_members),
                            padding_saved=padding_saved,
                            skip_reason=None
                        )
                        type_sizes[struct_name] = safe_size
                    else:
                        plan = OptimizationPlan(
                            struct=struct,
                            original_order=tuple(updated_members),
                            optimal_order=tuple(updated_members),
                            padding_saved=0,
                            skip_reason="constructor dependencies"
                        )
                        type_sizes[struct_name] = actual_size
                else:
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
    
    def _is_system_header(self, file_path: str) -> bool:
        """Check if file is a system header."""
        system_paths = [
            '/usr/include/',
            '/usr/local/include/',
            '/Library/Developer/',
            '/Applications/Xcode.app/',
        ]
        return any(file_path.startswith(path) for path in system_paths)


def _violates_dependencies(original_members, optimal_members, dependencies):
    """Check if reordering violates constructor dependencies."""
    # Create position maps
    original_pos = {m.name: i for i, m in enumerate(original_members)}
    optimal_pos = {m.name: i for i, m in enumerate(optimal_members)}
    
    # Check each dependency
    for dependent, deps in dependencies.items():
        if dependent not in optimal_pos:
            continue
        
        for dependency in deps:
            if dependency not in optimal_pos:
                continue
            
            # In optimal order, dependency must come before dependent
            if optimal_pos[dependency] >= optimal_pos[dependent]:
                return True
    
    return False


def _get_dependency_safe_order(members, dependencies, access_modifier_strategy):
    """Get optimal order that respects constructor dependencies."""
    from ...padding_analysis.member_reorderer import get_optimal_order
    
    # Start with optimal order
    optimal_members = get_optimal_order(members, access_modifier_strategy)
    
    # If no violations, return optimal
    if not _violates_dependencies(members, optimal_members, dependencies):
        return optimal_members
    
    # Create dependency constraints
    constraints = set()
    for dependent, deps in dependencies.items():
        for dep in deps:
            constraints.add((dep, dependent))  # dep must come before dependent
    
    # Try to find a valid ordering using topological sort with size optimization
    member_map = {m.name: m for m in members}
    
    # Build dependency graph
    graph = {m.name: set() for m in members}
    in_degree = {m.name: 0 for m in members}
    
    for dep, dependent in constraints:
        if dep in graph and dependent in graph:
            graph[dep].add(dependent)
            in_degree[dependent] += 1
    
    # Topological sort with size-based tie breaking
    result = []
    available = [name for name, degree in in_degree.items() if degree == 0]
    
    while available:
        # Sort by size (largest first for better packing)
        available.sort(key=lambda name: member_map[name].size, reverse=True)
        current = available.pop(0)
        result.append(member_map[current])
        
        # Update dependencies
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                available.append(neighbor)
    
    return result
