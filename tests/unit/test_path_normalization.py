"""Test path normalization in planning stage."""

import pytest
from implementation.pipeline.planning.stage import PlanningStage
from implementation.struct_data import StructInfo, MemberInfo, OptimizationPlan


@pytest.mark.unit
class TestPathNormalization:
    """Test that absolute paths are normalized to relative paths."""
    
    def test_normalize_snapshot_path(self):
        """Test that snapshot paths are converted to relative paths."""
        stage = PlanningStage()
        
        # Absolute path from pahole
        absolute = "/scratch/build/snapshot/common/caml/test.h"
        relative = stage._normalize_path(absolute)
        
        assert relative == "common/caml/test.h"
    
    def test_normalize_already_relative(self):
        """Test that relative paths are unchanged."""
        stage = PlanningStage()
        
        relative = "common/caml/test.h"
        result = stage._normalize_path(relative)
        
        assert result == relative
    
    def test_header_modifications_use_relative_paths(self):
        """Test that header modifications use relative paths."""
        stage = PlanningStage()
        
        struct = StructInfo(
            name="Test",
            size=16,
            members=(
                MemberInfo("a", "char", 1, 0, "public"),
                MemberInfo("b", "int", 4, 4, "public")
            ),
            file_path="/build/snapshot/common/test.h",  # Absolute
            line=10
        )
        
        plan = OptimizationPlan(
            struct=struct,
            original_order=struct.members,
            optimal_order=(struct.members[1], struct.members[0]),
            padding_saved=3,
            skip_reason=None
        )
        
        mods = stage._create_header_modifications(plan)
        
        assert len(mods) == 1
        assert mods[0].file_path == "common/test.h"  # Relative!


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
