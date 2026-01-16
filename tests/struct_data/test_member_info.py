"""Unit tests for MemberInfo dataclass."""

import pytest

from implementation.struct_data.member_info import MemberInfo


@pytest.mark.unit
class TestMemberInfo:
    """Test cases for MemberInfo dataclass."""
    
    def test_creation_with_required_fields(self):
        """Test creating MemberInfo with required fields."""
        member = MemberInfo(
            name="field1",
            type="int",
            size=4,
            offset=0,
            access_modifier="public"
        )
        
        assert member.name == "field1"
        assert member.type == "int"
        assert member.size == 4
        assert member.offset == 0
        assert member.access_modifier == "public"
        assert member.optimized_size is None
        assert member.locked is False
    
    def test_creation_with_all_fields(self):
        """Test creating MemberInfo with all fields."""
        member = MemberInfo(
            name="field1",
            type="double",
            size=8,
            offset=4,
            access_modifier="private",
            optimized_size=8,
            locked=True
        )
        
        assert member.name == "field1"
        assert member.type == "double"
        assert member.size == 8
        assert member.offset == 4
        assert member.access_modifier == "private"
        assert member.optimized_size == 8
        assert member.locked is True
    
    def test_immutability(self):
        """Test that MemberInfo is immutable."""
        member = MemberInfo("field1", "int", 4, 0, "public")
        
        with pytest.raises(AttributeError):
            member.name = "new_name"
    
    def test_invalid_access_modifier(self):
        """Test validation of access modifier."""
        with pytest.raises(ValueError, match="Invalid access_modifier"):
            MemberInfo("field1", "int", 4, 0, "invalid")
    
    def test_negative_size(self):
        """Test validation of negative size."""
        with pytest.raises(ValueError, match="Size cannot be negative"):
            MemberInfo("field1", "int", -1, 0, "public")
    
    def test_negative_offset(self):
        """Test validation of negative offset."""
        with pytest.raises(ValueError, match="Offset cannot be negative"):
            MemberInfo("field1", "int", 4, -1, "public")
    
    def test_negative_optimized_size(self):
        """Test validation of negative optimized size."""
        with pytest.raises(ValueError, match="Optimized size cannot be negative"):
            MemberInfo("field1", "int", 4, 0, "public", optimized_size=-1)
    
    @pytest.mark.parametrize("access_modifier", ["public", "private", "protected", "none"])
    def test_valid_access_modifiers(self, access_modifier):
        """Test all valid access modifiers."""
        member = MemberInfo("field1", "int", 4, 0, access_modifier)
        assert member.access_modifier == access_modifier