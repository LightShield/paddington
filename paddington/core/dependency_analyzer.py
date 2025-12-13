"""Analyze struct dependencies for bottom-up optimization."""

from typing import List, Dict, Set
from .models import StructInfo


def get_member_types(struct: StructInfo) -> Set[str]:
    """Get all custom types used as members (excluding native types)."""
    native_types = {
        "char",
        "signed char",
        "unsigned char",
        "short",
        "unsigned short",
        "int",
        "unsigned int",
        "long",
        "unsigned long",
        "long long",
        "unsigned long long",
        "float",
        "double",
        "long double",
        "bool",
        "_Bool",
        "int8_t",
        "uint8_t",
        "int16_t",
        "uint16_t",
        "int32_t",
        "uint32_t",
        "int64_t",
        "uint64_t",
        "size_t",
        "ssize_t",
        "ptrdiff_t",
    }

    custom_types = set()
    for member in struct.members:
        # Remove const/volatile/pointers/references
        base_type = (
            member.type_name.replace("const", "").replace("volatile", "").strip()
        )
        base_type = base_type.rstrip("*&").strip()

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
    """Sort structs in dependency order (leaves first, roots last).

    Simple approach: Repeatedly find and process structs with no dependencies.

    Args:
        structs: List of struct definitions

    Returns:
        Structs sorted with leaves first (no dependencies on other structs)
    """
    graph = build_dependency_graph(structs)
    struct_map = {s.name: s for s in structs}

    result = []
    remaining = set(graph.keys())

    while remaining:
        # Find structs with no dependencies (or all dependencies already processed)
        leaves = []
        for name in remaining:
            deps = graph[name]
            # Check if all dependencies are already processed
            if all(dep not in remaining for dep in deps):
                leaves.append(name)

        if not leaves:
            # Circular dependency - add remaining in arbitrary order
            leaves = list(remaining)

        # Sort for deterministic output
        leaves.sort()

        # Add leaves to result and remove from remaining
        for leaf in leaves:
            result.append(struct_map[leaf])
            remaining.remove(leaf)

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
