"""Unit tests for padding_calculator module."""

import pytest
from implementation.struct_data import MemberInfo
from implementation.padding_analysis.padding_calculator import (
    calculate_padding,
    calculate_internal_padding,
    calculate_trailing_padding,
)


@pytest.mark.unit
def test_calculate_padding_empty_members():
    """Test padding calculation with no members."""
    result = calculate_padding([], 16)
    assert result == 16


@pytest.mark.unit
def test_calculate_padding_no_padding():
    """Test padding calculation with no padding."""
    members = [
        MemberInfo("a", "int", 4, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
    ]
    result = calculate_padding(members, 8)
    assert result == 0


@pytest.mark.unit
def test_calculate_padding_with_padding():
    """Test padding calculation with padding."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
    ]
    result = calculate_padding(members, 8)
    assert result == 3  # 8 - (1 + 4) = 3


@pytest.mark.unit
def test_calculate_internal_padding_no_members():
    """Test internal padding with no members."""
    result = calculate_internal_padding([])
    assert result == 0


@pytest.mark.unit
def test_calculate_internal_padding_single_member():
    """Test internal padding with single member."""
    members = [MemberInfo("a", "int", 4, 0, "public")]
    result = calculate_internal_padding(members)
    assert result == 0


@pytest.mark.unit
def test_calculate_internal_padding_no_gaps():
    """Test internal padding with no gaps."""
    members = [
        MemberInfo("a", "int", 4, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
    ]
    result = calculate_internal_padding(members)
    assert result == 0


@pytest.mark.unit
def test_calculate_internal_padding_with_gaps():
    """Test internal padding with gaps."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
    ]
    result = calculate_internal_padding(members)
    assert result == 3  # Gap from offset 1 to 4


@pytest.mark.unit
def test_calculate_internal_padding_unordered_members():
    """Test internal padding with unordered members."""
    members = [
        MemberInfo("b", "int", 4, 4, "public"),
        MemberInfo("a", "char", 1, 0, "public"),
    ]
    result = calculate_internal_padding(members)
    assert result == 3  # Should sort by offset first


@pytest.mark.unit
def test_calculate_trailing_padding_empty_members():
    """Test trailing padding with no members."""
    result = calculate_trailing_padding([], 16)
    assert result == 16


@pytest.mark.unit
def test_calculate_trailing_padding_no_padding():
    """Test trailing padding with no trailing padding."""
    members = [
        MemberInfo("a", "int", 4, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
    ]
    result = calculate_trailing_padding(members, 8)
    assert result == 0


@pytest.mark.unit
def test_calculate_trailing_padding_with_padding():
    """Test trailing padding with trailing padding."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "int", 4, 4, "public"),
    ]
    result = calculate_trailing_padding(members, 12)
    assert result == 4  # 12 - (4 + 4) = 4


@pytest.mark.unit
def test_calculate_trailing_padding_multiple_members():
    """Test trailing padding with multiple members."""
    members = [
        MemberInfo("a", "char", 1, 0, "public"),
        MemberInfo("b", "short", 2, 2, "public"),
        MemberInfo("c", "int", 4, 8, "public"),
    ]
    result = calculate_trailing_padding(members, 16)
    assert result == 4  # 16 - (8 + 4) = 4