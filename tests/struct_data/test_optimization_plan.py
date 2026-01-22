"""Unit tests for OptimizationPlan dataclass."""

import pytest

from implementation.struct_data.optimization_plan import OptimizationPlan
from implementation.struct_data.struct_info import StructInfo
from implementation.struct_data.member_info import MemberInfo


@pytest.mark.unit
class TestOptimizationPlan:
    """Test cases for OptimizationPlan dataclass."""
    
    def test_creation_with_required_fields(self):
        """Test creating OptimizationPlan with required fields."""
        members = (
            MemberInfo("field1", "int", 4, 0, "public"),
            MemberInfo("field2", "char", 1, 4, "public"),
        )
        struct = StructInfo("TestStruct", 8, members)
        original_order = members
        optimal_order = (members[1], members[0])  # Reordered
        
        plan = OptimizationPlan(
            struct=struct,
            original_order=original_order,
            optimal_order=optimal_order,
            padding_saved=3
        )
        
        assert plan.struct == struct
        assert plan.original_order == original_order
        assert plan.optimal_order == optimal_order
        assert plan.padding_saved == 3
        assert plan.skip_reason is None
    
    def test_creation_with_skip_reason(self):
        """Test creating OptimizationPlan with skip reason."""
        members = (MemberInfo("field1", "int", 4, 0, "public"),)
        struct = StructInfo("TestStruct", 4, members)
        
        plan = OptimizationPlan(
            struct=struct,
            original_order=members,
            optimal_order=members,
            padding_saved=0,
            skip_reason="Already optimal"
        )
        
        assert plan.skip_reason == "Already optimal"
    
    def test_immutability(self):
        """Test that OptimizationPlan is immutable."""
        members = (MemberInfo("field1", "int", 4, 0, "public"),)
        struct = StructInfo("TestStruct", 4, members)
        
        plan = OptimizationPlan(
            struct=struct,
            original_order=members,
            optimal_order=members,
            padding_saved=0
        )
        
        with pytest.raises(AttributeError):
            plan.padding_saved = 5
    
    def test_negative_padding_saved(self):
        """Test auto-fix of negative padding saved."""
        members = (MemberInfo("field1", "int", 4, 0, "public"),)
        struct = StructInfo("TestStruct", 4, members)
        
        # Negative padding should be auto-fixed
        plan = OptimizationPlan(
            struct=struct,
            original_order=members,
            optimal_order=members,
            padding_saved=-1
        )
        
        # Should be auto-fixed to 0 with skip reason
        assert plan.padding_saved == 0
        assert plan.skip_reason is not None
        assert "reordering increases size by 1 bytes" in plan.skip_reason
    
    def test_mismatched_member_sets(self):
        """Test validation of mismatched member sets."""
        member1 = MemberInfo("field1", "int", 4, 0, "public")
        member2 = MemberInfo("field2", "char", 1, 4, "public")
        member3 = MemberInfo("field3", "double", 8, 8, "public")
        
        struct = StructInfo("TestStruct", 16, (member1, member2))
        original_order = (member1, member2)
        optimal_order = (member1, member3)  # Different member
        
        with pytest.raises(ValueError, match="Original and optimal orders must contain the same members"):
            OptimizationPlan(
                struct=struct,
                original_order=original_order,
                optimal_order=optimal_order,
                padding_saved=0
            )
    
    def test_reordered_members_validation_passes(self):
        """Test that reordered but same members pass validation."""
        member1 = MemberInfo("field1", "int", 4, 0, "public")
        member2 = MemberInfo("field2", "char", 1, 4, "public")
        
        struct = StructInfo("TestStruct", 8, (member1, member2))
        original_order = (member1, member2)
        optimal_order = (member2, member1)  # Reordered
        
        # Should not raise an exception
        plan = OptimizationPlan(
            struct=struct,
            original_order=original_order,
            optimal_order=optimal_order,
            padding_saved=3
        )
        
        assert plan.original_order == original_order
        assert plan.optimal_order == optimal_order