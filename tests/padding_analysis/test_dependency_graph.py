"""Unit tests for dependency_graph module."""

import pytest
from implementation.struct_data import StructInfo, MemberInfo
from implementation.padding_analysis.dependency_graph import (
    build_dependency_graph,
    topological_sort,
    detect_circular_dependencies,
)


@pytest.mark.unit
def test_build_dependency_graph_empty():
    """Test building dependency graph with empty list."""
    result = build_dependency_graph([])
    assert result == {}


@pytest.mark.unit
def test_build_dependency_graph_no_dependencies():
    """Test building dependency graph with no dependencies."""
    structs = [
        StructInfo("A", 8, (
            MemberInfo("x", "int", 4, 0, "public"),
            MemberInfo("y", "int", 4, 4, "public"),
        )),
        StructInfo("B", 4, (
            MemberInfo("z", "int", 4, 0, "public"),
        )),
    ]
    result = build_dependency_graph(structs)
    expected = {"A": set(), "B": set()}
    assert result == expected


@pytest.mark.unit
def test_build_dependency_graph_with_dependencies():
    """Test building dependency graph with dependencies."""
    structs = [
        StructInfo("A", 8, (
            MemberInfo("b", "B", 4, 0, "public"),
            MemberInfo("x", "int", 4, 4, "public"),
        )),
        StructInfo("B", 4, (
            MemberInfo("c", "C", 4, 0, "public"),
        )),
        StructInfo("C", 4, (
            MemberInfo("x", "int", 4, 0, "public"),
        )),
    ]
    result = build_dependency_graph(structs)
    expected = {"A": {"B"}, "B": {"C"}, "C": set()}
    assert result == expected


@pytest.mark.unit
def test_topological_sort_empty():
    """Test topological sort with empty graph."""
    result = topological_sort({})
    assert result == []


@pytest.mark.unit
def test_topological_sort_single_node():
    """Test topological sort with single node."""
    graph = {"A": set()}
    result = topological_sort(graph)
    assert result == ["A"]


@pytest.mark.unit
def test_topological_sort_linear_chain():
    """Test topological sort with linear dependency chain."""
    graph = {"A": {"B"}, "B": {"C"}, "C": set()}
    result = topological_sort(graph)
    assert result == ["C", "B", "A"]


@pytest.mark.unit
def test_topological_sort_multiple_roots():
    """Test topological sort with multiple root nodes."""
    graph = {"A": {"C"}, "B": {"C"}, "C": set()}
    result = topological_sort(graph)
    # C should come first, A and B can be in any order
    assert result[0] == "C"
    assert set(result[1:]) == {"A", "B"}


@pytest.mark.unit
def test_topological_sort_circular_dependency():
    """Test topological sort with circular dependency."""
    graph = {"A": {"B"}, "B": {"A"}}
    with pytest.raises(ValueError, match="Circular dependencies detected"):
        topological_sort(graph)


@pytest.mark.unit
def test_detect_circular_dependencies_empty():
    """Test circular dependency detection with empty graph."""
    result = detect_circular_dependencies({})
    assert result == []


@pytest.mark.unit
def test_detect_circular_dependencies_no_cycles():
    """Test circular dependency detection with no cycles."""
    graph = {"A": {"B"}, "B": {"C"}, "C": set()}
    result = detect_circular_dependencies(graph)
    assert result == []


@pytest.mark.unit
def test_detect_circular_dependencies_self_cycle():
    """Test circular dependency detection with self cycle."""
    graph = {"A": {"A"}}
    result = detect_circular_dependencies(graph)
    assert len(result) == 1
    assert result[0] == ["A", "A"]


@pytest.mark.unit
def test_detect_circular_dependencies_two_node_cycle():
    """Test circular dependency detection with two-node cycle."""
    graph = {"A": {"B"}, "B": {"A"}}
    result = detect_circular_dependencies(graph)
    assert len(result) == 1
    cycle = result[0]
    # Could be either ["A", "B", "A"] or ["B", "A", "B"]
    assert len(cycle) == 3
    assert cycle[0] == cycle[-1]
    assert set(cycle[:-1]) == {"A", "B"}


@pytest.mark.unit
def test_detect_circular_dependencies_three_node_cycle():
    """Test circular dependency detection with three-node cycle."""
    graph = {"A": {"B"}, "B": {"C"}, "C": {"A"}}
    result = detect_circular_dependencies(graph)
    assert len(result) == 1
    cycle = result[0]
    assert len(cycle) == 4
    assert cycle[0] == cycle[-1]
    assert set(cycle[:-1]) == {"A", "B", "C"}


@pytest.mark.unit
def test_detect_circular_dependencies_multiple_cycles():
    """Test circular dependency detection with multiple cycles."""
    graph = {"A": {"B"}, "B": {"A"}, "C": {"D"}, "D": {"C"}}
    result = detect_circular_dependencies(graph)
    assert len(result) == 2
    
    # Extract the cycle nodes (excluding the repeated last node)
    cycle_sets = [set(cycle[:-1]) for cycle in result]
    expected_cycles = [{"A", "B"}, {"C", "D"}]
    
    assert cycle_sets == expected_cycles or cycle_sets == expected_cycles[::-1]


@pytest.mark.unit
def test_detect_circular_dependencies_missing_nodes():
    """Test circular dependency detection with missing dependency nodes."""
    graph = {"A": {"B", "X"}, "B": set()}  # X doesn't exist in graph
    result = detect_circular_dependencies(graph)
    assert result == []  # Should not crash on missing nodes