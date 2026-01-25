"""Test for detecting aggregate initialization across files."""

import pytest
import tempfile
from pathlib import Path

from implementation.pipeline.analysis.stage import AnalysisStage
from implementation.struct_data import StructInfo, MemberInfo


@pytest.mark.unit
class TestAggregateInitAcrossFiles:
    """Test that aggregate init in .cpp files is detected."""
    
    def test_skip_struct_with_aggregate_init_in_cpp(self):
        """Test that structs with aggregate init in .cpp are skipped.
        
        Bug: al_address_map_access_info is defined in .h but used with
        aggregate init in .cpp. We only check the .h file.
        
        Solution: Check all files in the codebase, not just the struct's file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create header with struct
            header = tmpdir / "test.h"
            header.write_text("""
struct Data {
    int a;
    int b;
};
""")
            
            # Create cpp that uses aggregate init
            cpp = tmpdir / "test.cpp"
            cpp.write_text("""
#include "test.h"

void func() {
    Data d{1, 2};  // Aggregate initialization
}
""")
            
            # Create struct
            struct = StructInfo(
                name="Data",
                size=8,
                members=(
                    MemberInfo("a", "char", 1, 0, "public"),
                    MemberInfo("b", "int", 4, 4, "public")
                ),
                file_path=str(header),
                line=2
            )
            
            # Analyze without source_file (we'll pass source_root instead)
            analyzer = AnalysisStage()
            
            # Manually check for aggregate init in the directory
            from implementation.padding_analysis.aggregate_init_detector import has_aggregate_initialization_in_dir
            
            # This should detect usage in test.cpp
            has_agg_init = has_aggregate_initialization_in_dir(str(tmpdir), "Data")
            
            assert has_agg_init, "Should detect aggregate init in test.cpp"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
