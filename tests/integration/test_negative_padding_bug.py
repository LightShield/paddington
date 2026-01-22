"""Test for negative padding bug where reordering makes struct larger."""

import pytest
from implementation.struct_data.struct_info import StructInfo
from implementation.struct_data.member_info import MemberInfo
from implementation.struct_data.optimization_plan import OptimizationPlan
from implementation.pipeline.analysis.stage import AnalysisStage


def test_analysis_stage_negative_padding_fixed():
    """Test that the analysis stage now handles negative padding gracefully."""
    # Create a struct where reordering would make it larger
    members = [
        MemberInfo(name="a", type="char", size=1, offset=0, access_modifier="public"),
        MemberInfo(name="b", type="double", size=8, offset=8, access_modifier="public"),
        MemberInfo(name="c", type="char", size=1, offset=16, access_modifier="public"),
    ]
    
    struct = StructInfo(
        name="ProblematicStruct",
        size=20,  # Artificially small size
        members=tuple(members),
        file_path="/test/file.h",
        line=10
    )
    
    # Mock the size calculator to force negative padding scenario
    def mock_calculate_struct_size(members_list):
        # If this is the optimal reordering (double first), make it larger
        if len(members_list) >= 2 and members_list[0].type == "double":
            return 24  # Larger than original size of 20
        else:
            return 20  # Original order
    
    # Patch the size calculator in the analysis stage module
    import implementation.pipeline.analysis.stage as analysis_stage_module
    
    original_calculate = analysis_stage_module.calculate_struct_size
    analysis_stage_module.calculate_struct_size = mock_calculate_struct_size
    
    try:
        analysis_stage = AnalysisStage(min_savings=0)
        plans = analysis_stage.process([struct])
        
        # Verify the fix worked
        assert len(plans) == 1
        plan = plans[0]
        assert plan.padding_saved == 0  # Should be 0, not negative
        assert plan.skip_reason is not None  # Should have a skip reason
        assert "increases size" in plan.skip_reason  # Should mention size increase
        
    finally:
        # Restore original function
        analysis_stage_module.calculate_struct_size = original_calculate


def test_negative_padding_edge_case():
    """Test edge case where optimal reordering increases struct size."""
    # Create a more complex case that definitely triggers negative padding
    members = [
        MemberInfo(name="flag", type="bool", size=1, offset=0, access_modifier="public"),
        MemberInfo(name="data", type="double", size=8, offset=8, access_modifier="public"),  # 8-byte aligned
        MemberInfo(name="count", type="char", size=1, offset=16, access_modifier="public"),
    ]
    
    struct = StructInfo(
        name="TestStruct", 
        size=24,  # Original size with padding
        members=tuple(members),
        file_path="/test/file.h",
        line=20
    )
    
    # Direct test of OptimizationPlan with negative padding - should auto-fix
    plan = OptimizationPlan(
        struct=struct,
        original_order=tuple(members),
        optimal_order=tuple(members),  # Same order
        padding_saved=-8  # Negative padding should be auto-fixed
    )
    
    # Verify auto-fix worked
    assert plan.padding_saved == 0  # Should be auto-fixed to 0
    assert plan.skip_reason is not None  # Should have skip reason
    assert "reordering increases size by 8 bytes" in plan.skip_reason


def test_zero_padding_should_work():
    """Test that zero padding is acceptable."""
    members = [
        MemberInfo(name="a", type="int", size=4, offset=0, access_modifier="public"),
        MemberInfo(name="b", type="int", size=4, offset=4, access_modifier="public"),
    ]
    
    struct = StructInfo(
        name="TestStruct",
        size=8,
        members=tuple(members),
        file_path="/test/file.h", 
        line=30
    )
    
    # Zero padding should be fine
    plan = OptimizationPlan(
        struct=struct,
        original_order=tuple(members),
        optimal_order=tuple(members),
        padding_saved=0
    )
    
    assert plan.padding_saved == 0
    assert plan.skip_reason is None