"""Analysis stage with iterative size propagation."""

from typing import List, Dict, Optional
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
from ...padding_analysis.source_scanner import SourceScanner
from ...utils.logger import log


class AnalysisStage(Stage[List[StructInfo], List[OptimizationPlan]]):
    """Analyze structs iteratively with size propagation."""
    
    def __init__(self, min_savings: int = 0, access_modifier_strategy: str = "preserve", source_file: str = "", struct_names: list = None, source_root: str = None, exclude_patterns: list = None, workspace_dir: str = None):
        self.min_savings = min_savings
        self.access_modifier_strategy = access_modifier_strategy
        self.source_file = source_file
        self.struct_names = struct_names or []
        self.source_root = source_root
        # One-time scanner for all checks
        self._scanner: Optional[SourceScanner] = None
        if source_root:
            self._scanner = SourceScanner(source_root, exclude_patterns or [], workspace_dir)
    
    def process(self, structs: List[StructInfo]) -> List[OptimizationPlan]:
        """Process structs in dependency order with size propagation."""
        if not structs:
            return []
        
        # Scan source tree once if scanner is available
        if self._scanner:
            self._scanner.scan()
        
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
        log.info(f"Analyzing {len(ordered_names)} structs in dependency order")
        
        for i, struct_name in enumerate(ordered_names, 1):
            if struct_name not in struct_map:
                continue
            
            # Show progress for large numbers
            if i % 100 == 0 or (i % 10 == 0 and len(ordered_names) < 100):
                log.info(f"  Analyzing: {i}/{len(ordered_names)}")
            
            struct = struct_map[struct_name]
            log.debug(f"Analyzing {struct.name}: size={struct.size} bytes")
            
            # Skip structs with 0 or 1 members (nothing to reorder)
            if len(struct.members) <= 1:
                log.debug(f"Skipping {struct.name}: only {len(struct.members)} member(s)")
                plan = OptimizationPlan(
                    struct=struct,
                    original_order=tuple(struct.members),
                    optimal_order=tuple(struct.members),
                    padding_saved=0,
                    skip_reason=f"only {len(struct.members)} member(s)"
                )
                plans.append(plan)
                type_sizes[struct_name] = struct.size
                continue
            
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
            if self._scanner:
                constructor_deps = self._scanner.get_constructor_dependencies(struct_name)
                if constructor_deps:
                    log.debug(f"Found constructor deps for {struct_name}: {constructor_deps}")
            elif self.source_file:
                constructor_deps = detect_constructor_dependencies(self.source_file, struct_name)
            
            # Check if struct has static members (can cause dependency issues)
            # Check both from pahole (locked flag) and from source scanner
            has_static_from_pahole = any(m.locked for m in updated_members)
            has_static_from_source = self._scanner and self._scanner.has_static_const_members(struct_name)
            
            if has_static_from_pahole or has_static_from_source:
                plan = OptimizationPlan(
                    struct=struct,
                    original_order=tuple(updated_members),
                    optimal_order=tuple(updated_members),
                    padding_saved=0,
                    skip_reason="has static members"
                )
                plans.append(plan)
                type_sizes[struct_name] = actual_size
                continue
            
            # Check for nested types
            if self._scanner and struct_name in self._scanner.structs_with_nested_types:
                plan = OptimizationPlan(
                    struct=struct,
                    original_order=tuple(updated_members),
                    optimal_order=tuple(updated_members),
                    padding_saved=0,
                    skip_reason="nested types"
                )
                plans.append(plan)
                type_sizes[struct_name] = actual_size
                continue
            
            # Check for preprocessor directives
            if self._scanner and self._scanner.has_preprocessor_directives(struct_name):
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
            elif not self._scanner and struct.file_path and has_preprocessor_directives(struct.file_path, struct_name):
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
            
            # Check for aggregate initialization
            if self._scanner and self._scanner.has_aggregate_initialization(struct_name):
                plan = OptimizationPlan(
                    struct=struct,
                    original_order=tuple(updated_members),
                    optimal_order=tuple(updated_members),
                    padding_saved=0,
                    skip_reason="aggregate initialization"
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
                # Has constructor dependencies - check if reordering would violate them
                log.debug(f"Checking constructor deps for {struct_name}")
                optimal_members = get_optimal_order(updated_members, self.access_modifier_strategy)
                log.debug(f"Original order: {[m.name for m in updated_members]}")
                log.debug(f"Optimal order: {[m.name for m in optimal_members]}")
                if _violates_dependencies(updated_members, optimal_members, constructor_deps):
                    # Reordering would break constructor - skip optimization
                    log.debug(f"Reordering violates dependencies - skipping {struct_name}")
                    plan = OptimizationPlan(
                        struct=struct,
                        original_order=tuple(updated_members),
                        optimal_order=tuple(updated_members),
                        padding_saved=0,
                        skip_reason="constructor dependencies"
                    )
                    type_sizes[struct_name] = actual_size
                else:
                    # Constructor dependencies don't prevent this reordering
                    optimal_size = calculate_struct_size(optimal_members)
                    padding_saved = actual_size - optimal_size
                    
                    if padding_saved < 0:
                        plan = OptimizationPlan(
                            struct=struct,
                            original_order=tuple(updated_members),
                            optimal_order=tuple(updated_members),
                            padding_saved=0,
                            skip_reason=f"reordering increases size by {-padding_saved} bytes"
                        )
                        type_sizes[struct_name] = actual_size
                    else:
                        plan = OptimizationPlan(
                            struct=struct,
                            original_order=tuple(updated_members),
                            optimal_order=tuple(optimal_members),
                            padding_saved=padding_saved,
                            skip_reason=None
                        )
                        type_sizes[struct_name] = optimal_size
            else:
                # No constructor dependencies - optimize freely
                optimal_members = get_optimal_order(updated_members, self.access_modifier_strategy)
                optimal_size = calculate_struct_size(optimal_members)
                padding_saved = actual_size - optimal_size
                
                # Check if already optimal
                if optimal_members == updated_members:
                    plan = OptimizationPlan(
                        struct=struct,
                        original_order=tuple(updated_members),
                        optimal_order=tuple(optimal_members),
                        padding_saved=0,
                        skip_reason="already optimal"
                    )
                    type_sizes[struct_name] = actual_size
                elif padding_saved < 0:
                    plan = OptimizationPlan(
                        struct=struct,
                        original_order=tuple(updated_members),
                        optimal_order=tuple(updated_members),
                        padding_saved=0,
                        skip_reason=f"reordering increases size by {-padding_saved} bytes"
                    )
                    type_sizes[struct_name] = actual_size
                else:
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
