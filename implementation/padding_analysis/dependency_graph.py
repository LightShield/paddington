"""Pure functions for building and analyzing struct dependency graphs."""

from typing import Dict, Set, List
from ..struct_data import StructInfo


def build_dependency_graph(structs: List[StructInfo]) -> Dict[str, Set[str]]:
    """Build dependency graph from struct information.
    
    Args:
        structs: List of struct information
        
    Returns:
        Dictionary mapping struct names to their dependencies
    """
    graph = {}
    
    for struct in structs:
        graph[struct.name] = struct.get_dependencies()
    
    return graph


def topological_sort(graph: Dict[str, Set[str]]) -> List[str]:
    """Perform topological sort on dependency graph.
    
    Args:
        graph: Dependency graph (node -> set of dependencies)
        
    Returns:
        List of nodes in topological order (dependencies first)
        
    Raises:
        ValueError: If circular dependencies are detected
    """
    # Check for circular dependencies first
    cycles = detect_circular_dependencies(graph)
    if cycles:
        raise ValueError(f"Circular dependencies detected: {cycles}")
    
    # Kahn's algorithm - build reverse graph for correct ordering
    in_degree = {node: 0 for node in graph}
    
    # Calculate in-degrees (how many nodes depend on this node)
    for node in graph:
        for dependency in graph[node]:
            if dependency in in_degree:
                in_degree[node] += 1
    
    # Find nodes with no dependencies (in-degree 0)
    queue = [node for node, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        node = queue.pop(0)
        result.append(node)
        
        # For each node that depends on the current node
        for other_node in graph:
            if node in graph[other_node]:
                in_degree[other_node] -= 1
                if in_degree[other_node] == 0:
                    queue.append(other_node)
    
    return result


def detect_circular_dependencies(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Detect circular dependencies in the graph.
    
    Args:
        graph: Dependency graph (node -> set of dependencies)
        
    Returns:
        List of cycles, where each cycle is a list of nodes
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    colors = {node: WHITE for node in graph}
    cycles = []
    
    def dfs(node: str, path: List[str]) -> None:
        if colors[node] == GRAY:
            # Found a cycle
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        
        if colors[node] == BLACK:
            return
        
        colors[node] = GRAY
        path.append(node)
        
        for dependency in graph[node]:
            if dependency in graph:  # Only follow dependencies that exist in our graph
                dfs(dependency, path)
        
        path.pop()
        colors[node] = BLACK
    
    for node in graph:
        if colors[node] == WHITE:
            dfs(node, [])
    
    return cycles