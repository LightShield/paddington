"""Analyze struct dependencies for bottom-up optimization."""
from typing import List, Dict, Set
from .models import StructInfo

def get_member_types(struct: StructInfo) -> Set[str]:
    """Get all custom types used as members (excluding native types)."""
    native_types = {
        'char', 'signed char', 'unsigned char',
        'short', 'unsigned short', 'int', 'unsigned int',
        'long', 'unsigned long', 'long long', 'unsigned long long',
        'float', 'double', 'long double',
        'bool', '_Bool',
        'int8_t', 'uint8_t', 'int16_t', 'uint16_t',
        'int32_t', 'uint32_t', 'int64_t', 'uint64_t',
        'size_t', 'ssize_t', 'ptrdiff_t'
    }
    
    custom_types = set()
    for member in struct.members:
        # Remove const/volatile/pointers/references
        base_type = member.type_name.replace('const', '').replace('volatile', '').strip()
        base_type = base_type.rstrip('*&').strip()
        
        if base_type not in native_types:
            custom_types.add(base_type)
    
    return custom_types

def build_dependency_graph(structs: List[StructInfo]) -> Dict[str, Set[str]]:
    """Build dependency graph: struct_name -> set of structs it depends on."""
    graph = {}
    struct_names = {s.name for s in structs}
    
    for struct in structs:
        dependencies = get_member_types(struct)
        # Only include dependencies that are in our struct list
        graph[struct.name] = dependencies & struct_names
    
    return graph

def topological_sort(structs: List[StructInfo]) -> List[StructInfo]:
    """Sort structs in dependency order (leaves first, roots last)."""
    graph = build_dependency_graph(structs)
    struct_map = {s.name: s for s in structs}
    
    # Kahn's algorithm for topological sort
    in_degree = {name: 0 for name in graph}
    for deps in graph.values():
        for dep in deps:
            if dep in in_degree:
                in_degree[dep] += 1
    
    # Start with nodes that have no dependencies
    queue = [name for name, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        # Sort for deterministic output
        queue.sort()
        current = queue.pop(0)
        result.append(struct_map[current])
        
        # Reduce in-degree for dependents
        for name, deps in graph.items():
            if current in deps:
                in_degree[name] -= 1
                if in_degree[name] == 0:
                    queue.append(name)
    
    # Check for cycles
    if len(result) != len(structs):
        # Some structs have circular dependencies
        # Add remaining structs (they won't be optimized)
        remaining = [s for s in structs if s.name not in {r.name for r in result}]
        result.extend(remaining)
    
    return result

def has_circular_dependency(structs: List[StructInfo]) -> bool:
    """Check if there are circular dependencies."""
    graph = build_dependency_graph(structs)
    
    visited = set()
    rec_stack = set()
    
    def has_cycle(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    for node in graph:
        if node not in visited:
            if has_cycle(node):
                return True
    
    return False
