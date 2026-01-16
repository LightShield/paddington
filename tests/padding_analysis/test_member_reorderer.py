"""Unit tests for member_reorderer module."""

import pytest
from implementation.struct_data import MemberInfo
from implementation.padding_analysis.member_reorderer import (
    reorder_by_size,
    reorder_within_access_modifiers,
    reorder_with_split_access_modifiers,
    reorder_ignore_access_modifiers,
    get_optimal_order,
)


@pytest.mark.unit
def test_reorder_by_size_empty():
    """Test reordering empty list."""
    result = reorder_by_size([])
    assert result == []


@pytest.mark.unit
def test_reorder_by_size_single():
    """Test reordering single member."""
    members = [MemberInfo("a", "int", 4, 0, "public")]
    result = reorder_by_size(members)
    assert result == members


@pytest.mark.unit
def test_reorder_by_size_multiple():
    """Test reordering multiple members by size."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 1, "public"),
        MemberInfo("c", "short", 2, 5, "public"),
    ]
    result = reorder_by_size(members)
    expected = [members[1], members[2], members[0]]  # int, short, char
    assert result == expected


@pytest.mark.unit
def test_reorder_within_access_modifiers_empty():
    """Test reordering within access modifiers with empty list."""
    result = reorder_within_access_modifiers([])
    assert result == []


@pytest.mark.unit
def test_reorder_within_access_modifiers_single_group():
    """Test reordering within single access modifier group."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 1, "public"),
        MemberInfo("c", "short", 2, 5, "public"),
    ]
    result = reorder_within_access_modifiers(members)
    expected = [members[1], members[2], members[0]]  # int, short, char
    assert result == expected


@pytest.mark.unit
def test_reorder_within_access_modifiers_multiple_groups():
    """Test reordering within multiple access modifier groups."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 1, "private"),
        MemberInfo("c", "short", 2, 5, "public"),
        MemberInfo("d", "double", 8, 8, "private"),
    ]
    result = reorder_within_access_modifiers(members)
    # Should preserve group order: public first, then private
    # Within public: short (2), char (1)
    # Within private: double (8), int (4)
    expected = [members[2], members[0], members[3], members[1]]
    assert result == expected


@pytest.mark.unit
def test_reorder_with_split_access_modifiers_empty():
    """Test split access modifier reordering with empty list."""
    result = reorder_with_split_access_modifiers([])
    assert result == []


@pytest.mark.unit
def test_reorder_with_split_access_modifiers_multiple_groups():
    """Test split access modifier reordering."""
    members = [
        MemberInfo("a", "char", 1, 0, "private"),
        MemberInfo("b", "int", 4, 1, "public"),
        MemberInfo("c", "short", 2, 5, "private"),
        MemberInfo("d", "double", 8, 8, "public"),
    ]
    result = reorder_with_split_access_modifiers(members)
    # Should group by access modifier in order: public, protected, private, none
    # Public: double (8), int (4)
    # Private: short (2), char (1)
    expected = [members[3], members[1], members[2], members[0]]
    assert result == expected


@pytest.mark.unit
def test_reorder_ignore_access_modifiers():
    """Test ignoring access modifiers completely."""
    members = [
        MemberInfo("a", "char", 1, 0, "private"),
        MemberInfo("b", "int", 4, 1, "public"),
        MemberInfo("c", "short", 2, 5, "protected"),
        MemberInfo("d", "double", 8, 8, "none"),
    ]
    result = reorder_ignore_access_modifiers(members)
    expected = [members[3], members[1], members[2], members[0]]  # double, int, short, char
    assert result == expected


@pytest.mark.unit
def test_get_optimal_order_preserve():
    """Test get_optimal_order with preserve strategy."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 1, "private"),
    ]
    result = get_optimal_order(members, "preserve")
    expected = reorder_within_access_modifiers(members)
    assert result == expected


@pytest.mark.unit
def test_get_optimal_order_split():
    """Test get_optimal_order with split strategy."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 1, "private"),
    ]
    result = get_optimal_order(members, "split")
    expected = reorder_with_split_access_modifiers(members)
    assert result == expected


@pytest.mark.unit
def test_get_optimal_order_ignore():
    """Test get_optimal_order with ignore strategy."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 1, "private"),
    ]
    result = get_optimal_order(members, "ignore")
    expected = reorder_ignore_access_modifiers(members)
    assert result == expected


@pytest.mark.unit
def test_get_optimal_order_invalid_strategy():
    """Test get_optimal_order with invalid strategy."""
    members = [MemberInfo("a", "int", 4, 0, "public")]
    with pytest.raises(ValueError, match="Unknown strategy: invalid"):
        get_optimal_order(members, "invalid")