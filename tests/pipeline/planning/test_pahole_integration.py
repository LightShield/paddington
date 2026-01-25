"""Integration test for pahole extractor and planning stage working together."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from implementation.pipeline.extraction.pahole import PaholeExtractor
from implementation.pipeline.planning.stage import PlanningStage
from implementation.struct_data.optimization_plan import OptimizationPlan
from implementation.struct_data.struct_info import StructInfo
from implementation.struct_data.member_info import MemberInfo


class TestPaholeToPlanning:
    """Test integration between pahole extractor and planning stage."""
    
    @pytest.mark.integration
    def test_pahole_provides_compilation_data_to_planning(self):
        """Test that pahole extractor provides compilation data to planning stage."""
        # Mock pahole output with source locations
        mock_pahole_output = """
/* Used at: /project/src/user_impl.cpp */
/* Used at: /project/src/user_factory.cpp */
/* <0> /project/src/user.h:10 */
struct UserData {
    int id; /* 0 4 */
    char name; /* 4 1 */
    double score; /* 8 8 */
}; /* size: 24 */
"""
        
        # Create pahole extractor
        extractor = PaholeExtractor()
        
        # Mock the pahole command execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_pahole_output
            
            # Extract structs (this should also collect compilation data)
            structs = extractor.extract([Path("/fake/object.o")])
            
            # Verify struct was extracted
            assert len(structs) == 1
            assert structs[0].name == "UserData"
            assert structs[0].file_path == "/project/src/user.h"
            
            # Verify compilation data was collected
            compilation_data = extractor.get_compilation_data()
            assert "UserData" in compilation_data
            assert "/project/src/user_impl.cpp" in compilation_data["UserData"]
            assert "/project/src/user_factory.cpp" in compilation_data["UserData"]
    
    @pytest.mark.integration
    def test_end_to_end_pahole_to_planning_workflow(self):
        """Test complete workflow from pahole extraction to planning stage."""
        # Create temporary files to simulate real scenario
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create source files
            header = tmpdir / "user.h"
            impl1 = tmpdir / "user_impl.cpp"
            impl2 = tmpdir / "user_factory.cpp"
            
            header.write_text("""
            struct UserData {
                int id;
                char name;
                double score;
            };
            """)
            
            impl1.write_text("""
            #include "user.h"
            UserData::UserData(int i) : id(i), name(0), score(0.0) {}
            """)
            
            impl2.write_text("""
            #include "user.h"
            UserData::UserData(int i, char n) : id(i), name(n), score(0.0) {}
            """)
            
            # Mock pahole output
            mock_pahole_output = f"""
/* Used at: {impl1} */
/* Used at: {impl2} */
/* <0> {header}:2 */
struct UserData {{
    int id; /* 0 4 */
    char name; /* 4 1 */
    double score; /* 8 8 */
}}; /* size: 24 */
"""
            
            # Step 1: Extract with pahole
            extractor = PaholeExtractor()
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = mock_pahole_output
                
                structs = extractor.extract([Path("/fake/object.o")])
                compilation_data = extractor.get_compilation_data()
            
            # Step 2: Create optimization plan
            struct = structs[0]
            plan = OptimizationPlan(
                struct=struct,
                original_order=struct.members,
                optimal_order=tuple(reversed(struct.members)),  # Reverse for optimization
                padding_saved=8,
                skip_reason=None
            )
            
            # Step 3: Use planning stage with compilation data
            planning_stage = PlanningStage()
            planning_stage.set_compilation_data(compilation_data)
            
            # Generate modifications
            modifications = planning_stage.process([plan])
            
            # Verify results
            assert len(modifications) >= 3  # At least 1 header + 2 cpp files (may have duplicates)
            
            # Check header modification
            header_mods = [m for m in modifications if m.file_path == str(header)]
            assert len(header_mods) == 1
            
            # Check cpp modifications
            cpp_mods = [m for m in modifications if m.file_path.endswith('.cpp')]
            assert len(cpp_mods) == 2
            
            cpp_files = [m.file_path for m in cpp_mods]
            assert str(impl1) in cpp_files
            assert str(impl2) in cpp_files
    
    @pytest.mark.unit
    def test_compilation_data_format(self):
        """Test that compilation data has the expected format."""
        extractor = PaholeExtractor()
        
        # Test the parsing method directly
        pahole_output = """
/* Used at: /project/src/data_impl.cpp */
/* Used at: /project/src/data_utils.cpp */
/* Used at: /project/test/data_test.cpp */
/* <0> /project/include/data.h:15 */
struct Data {
    int x; /* 0 4 */
    char y; /* 4 1 */
}; /* size: 8 */
"""
        
        extractor._collect_source_file_mappings(pahole_output)
        compilation_data = extractor.get_compilation_data()
        
        # Should only include .cpp files, not test files or headers
        assert "Data" in compilation_data
        cpp_files = compilation_data["Data"]
        
        # Should include implementation files
        assert "/project/src/data_impl.cpp" in cpp_files
        assert "/project/src/data_utils.cpp" in cpp_files
        assert "/project/test/data_test.cpp" in cpp_files  # Test files are also .cpp
        
        # Should not include headers in the cpp files list
        assert "/project/include/data.h" not in cpp_files