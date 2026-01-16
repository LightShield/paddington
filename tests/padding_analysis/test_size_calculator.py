"""Unit tests for size_calculator module."""

import pytest
from implementation.struct_data import MemberInfo
from implementation.padding_analysis.size_calculator import (
    calculate_struct_size,
    calculate_optimal_size,
)


@pytest.mark.unit
def test_calculate_struct_size_empty():
    """Test struct size calculation with no members."""
    result = calculate_struct_size([])
    assert result == 0


@pytest.mark.unit
def test_calculate_struct_size_single_member():
    """Test struct size calculation with single member."""
    members = [MemberInfo("a", "int", 4, 0, "public")]
    result = calculate_struct_size(members)
    assert result == 4


@pytest.mark.unit
def test_calculate_struct_size_aligned_members():
    """Test struct size calculation with aligned members."""
    members = [
        MemberInfo("a", "int", 4, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
    ]
    result = calculate_struct_size(members)
    assert result == 8


@pytest.mark.unit
def test_calculate_struct_size_with_padding():
    """Test struct size calculation requiring padding."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
    ]
    result = calculate_struct_size(members)
    # char (1) + padding (3) + int (4) = 8, aligned to 4-byte boundary
    assert result == 8


@pytest.mark.unit
def test_calculate_struct_size_mixed_sizes():
    """Test struct size calculation with mixed member sizes."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "short", 2, 2, "public"),
        MemberInfo("c", "int", 4, 4, "public"),
    ]
    result = calculate_struct_size(members)
    # char (1) + padding (1) + short (2) + int (4) = 8, aligned to 4-byte boundary
    assert result == 8


@pytest.mark.unit
def test_calculate_struct_size_large_alignment():
    """Test struct size calculation with 8-byte alignment."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "double", 8, 8, "public"),
    ]
    result = calculate_struct_size(members)
    # char (1) + padding (7) + double (8) = 16, aligned to 8-byte boundary
    assert result == 16


@pytest.mark.unit
def test_calculate_struct_size_trailing_padding():
    """Test struct size calculation with trailing padding."""
    members = [
        MemberInfo("a", "int", 4, 0, "public"),
        MemberInfo("b", "char", 1, 4, "public"),
    ]
    result = calculate_struct_size(members)
    # int (4) + char (1) + padding (3) = 8, aligned to 4-byte boundary
    assert result == 8


@pytest.mark.unit
def test_calculate_optimal_size_empty():
    """Test optimal size calculation with no members."""
    result = calculate_optimal_size([])
    assert result == 0


@pytest.mark.unit
def test_calculate_optimal_size_already_optimal():
    """Test optimal size calculation when already optimal."""
    members = [
        MemberInfo("a", "double", 8, 0, "public"),
        MemberInfo("b", "int", 4, 8, "public"),
        MemberInfo("c", "char", 1, 12, "public"),
    ]
    result = calculate_optimal_size(members)
    # Already in optimal order: double, int, char
    assert result == 16  # 8 + 4 + 1 + 3 padding = 16


@pytest.mark.unit
def test_calculate_optimal_size_needs_reordering():
    """Test optimal size calculation when reordering helps."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
        MemberInfo("c", "double", 8, 8, "public"),
    ]
    result = calculate_optimal_size(members)
    # Optimal order: double, int, char = 8 + 4 + 1 + 3 padding = 16
    assert result == 16


@pytest.mark.unit
def test_calculate_optimal_size_complex_case():
    """Test optimal size calculation with complex member arrangement."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "char", 1, 1, "public"),
        MemberInfo("c", "short", 2, 2, "public"),
        MemberInfo("d", "int", 4, 4, "public"),
        MemberInfo("e", "double", 8, 8, "public"),
    ]
    result = calculate_optimal_size(members)
    # Optimal order: double (8), int (4), short (2), char (1), char (1)
    # = 8 + 4 + 2 + 1 + 1 + 0 padding = 16
    assert result == 16