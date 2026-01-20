"""Tests for compilation-based .cpp file detection."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from implementation.pipeline.planning.stage import PlanningStage
from implementation.struct_data.struct_info import StructInfo
from implementation.struct_data.member_info import MemberInfo
from implementation.struct_data.optimization_plan import OptimizationPlan


class TestCppFileDetection:
    """Test proper .cpp file detection using compilation data."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_struct(self):
        """Create sample struct info."""
        return StructInfo(
            name="UserData",
            size=24,
            members=(
                MemberInfo(name="id", type="int", size=4, offset=0, access_modifier="public"),
                MemberInfo(name="name", type="char", size=1, offset=4, access_modifier="public"),
                MemberInfo(name="score", type="double", size=8, offset=8, access_modifier="public"),
            ),
            file_path="/project/src/user.h",
            line=10
        )
    
    @pytest.fixture
    def planning_stage(self):
        """Create planning stage with compilation data."""
        return PlanningStage()
    
    @pytest.mark.unit
    def test_extract_cpp_files_from_compilation_data(self, planning_stage):
        """Test extracting .cpp files from compilation data."""
        # Mock compilation data (like from pahole -I output)
        compilation_data = {
            "UserData": [
                "/project/src/user_impl.cpp",
                "/project/src/user_factory.cpp"
            ],
            "Config": [
                "/project/src/config.cpp"
            ]
        }
        
        planning_stage._set_compilation_data(compilation_data)
        
        cpp_files = planning_stage._get_cpp_files_for_struct("UserData")
        assert cpp_files == ["/project/src/user_impl.cpp", "/project/src/user_factory.cpp"]
        
        cpp_files = planning_stage._get_cpp_files_for_struct("Config")
        assert cpp_files == ["/project/src/config.cpp"]
        
        cpp_files = planning_stage._get_cpp_files_for_struct("NonExistent")
        assert cpp_files == []
    
    @pytest.mark.unit
    def test_no_filename_guessing(self, planning_stage, sample_struct):
        """Test that filename guessing is not used."""
        # Even if user.cpp exists, it should not be detected without compilation data
        with tempfile.TemporaryDirectory() as tmpdir:
            header_file = Path(tmpdir) / "user.h"
            cpp_file = Path(tmpdir) / "user.cpp"
            
            header_file.write_text("struct UserData { int id; };")
            cpp_file.write_text("UserData::UserData() : id(0) {}")
            
            # Update struct to point to temp files
            struct_with_temp_path = StructInfo(
                name="UserData",
                size=24,
                members=sample_struct.members,
                file_path=str(header_file),
                line=1
            )
            
            # Without compilation data, no .cpp files should be found
            cpp_files = planning_stage._get_cpp_files_for_struct("UserData")
            assert cpp_files == []
    
    @pytest.mark.unit
    def test_multiple_cpp_files_per_header(self, planning_stage, temp_dir):
        """Test handling multiple .cpp files for one header."""
        # Create test files
        header_file = temp_dir / "user.h"
        impl_file = temp_dir / "user_impl.cpp"
        factory_file = temp_dir / "user_factory.cpp"
        test_file = temp_dir / "user_test.cpp"
        
        header_file.write_text("""
        struct UserData {
            int id;
            char* name;
            UserData(int i);
            UserData(const char* n);
        };
        """)
        
        impl_file.write_text("""
        #include "user.h"
        UserData::UserData(int i) : id(i), name(nullptr) {}
        """)
        
        factory_file.write_text("""
        #include "user.h"
        UserData::UserData(const char* n) : name(strdup(n)), id(0) {}
        """)
        
        test_file.write_text("""
        #include "user.h"
        // Just includes header, no constructor definitions
        void test_user() { UserData u(42); }
        """)
        
        # Set compilation data showing which files actually contain constructors
        compilation_data = {
            "UserData": [str(impl_file), str(factory_file)]
        }
        planning_stage._set_compilation_data(compilation_data)
        
        cpp_files = planning_stage._get_cpp_files_for_struct("UserData")
        assert set(cpp_files) == {str(impl_file), str(factory_file)}
        assert str(test_file) not in cpp_files
    
    @pytest.mark.unit
    def test_validate_cpp_files_contain_constructors(self, planning_stage, temp_dir):
        """Test validation that detected .cpp files contain relevant constructors."""
        # Create files
        header_file = temp_dir / "data.h"
        valid_cpp = temp_dir / "data.cpp"
        invalid_cpp = temp_dir / "data_utils.cpp"
        
        header_file.write_text("struct Data { int x; Data(int i); };")
        valid_cpp.write_text("Data::Data(int i) : x(i) {}")
        invalid_cpp.write_text("#include \"data.h\"\nvoid helper() {}")
        
        # Test validation
        assert planning_stage._validate_cpp_file_has_constructors(str(valid_cpp), "Data")
        assert not planning_stage._validate_cpp_file_has_constructors(str(invalid_cpp), "Data")
    
    @pytest.mark.integration
    def test_pahole_output_parsing(self, planning_stage):
        """Test parsing pahole -I output to extract source files."""
        pahole_output = """
/* <0> /project/src/user.h:10 */
struct UserData {
    int id; /* 0 4 */
    char name; /* 4 1 */
    double score; /* 8 8 */
}; /* size: 24 */

/* <24> /project/src/user_impl.cpp:5 */
/* <48> /project/src/user_factory.cpp:12 */
"""
        
        source_files = planning_stage._parse_pahole_source_locations(pahole_output)
        expected = {
            "/project/src/user.h": [10],
            "/project/src/user_impl.cpp": [5],
            "/project/src/user_factory.cpp": [12]
        }
        assert source_files == expected
    
    @pytest.mark.integration
    def test_build_struct_to_cpp_mapping(self, planning_stage):
        """Test building mapping from struct names to their .cpp files."""
        # Mock struct extraction data with source locations
        structs_with_sources = [
            {
                "name": "UserData",
                "header": "/project/src/user.h",
                "sources": ["/project/src/user_impl.cpp", "/project/src/user_factory.cpp"]
            },
            {
                "name": "Config", 
                "header": "/project/src/config.h",
                "sources": ["/project/src/config.cpp"]
            }
        ]
        
        mapping = planning_stage._build_struct_to_cpp_mapping(structs_with_sources)
        
        expected = {
            "UserData": ["/project/src/user_impl.cpp", "/project/src/user_factory.cpp"],
            "Config": ["/project/src/config.cpp"]
        }
        assert mapping == expected
    
    @pytest.mark.unit
    def test_error_handling_no_cpp_files_found(self, planning_stage, sample_struct):
        """Test error handling when no .cpp files are found for a struct."""
        # No compilation data set
        cpp_files = planning_stage._get_cpp_files_for_struct("UserData")
        assert cpp_files == []
        
        # Should log warning about no implementation files found
        with patch.object(planning_stage, 'log') as mock_log:
            modifications = planning_stage._create_cpp_modifications(
                OptimizationPlan(
                    struct=sample_struct,
                    original_order=sample_struct.members,
                    optimal_order=sample_struct.members,
                    padding_saved=0,
                    skip_reason=None
                )
            )
            assert modifications == []
            mock_log.warning.assert_called_once()
    
    @pytest.mark.unit
    def test_report_detection_method(self, planning_stage):
        """Test that the detection method is logged."""
        compilation_data = {"UserData": ["/project/src/user.cpp"]}
        planning_stage._set_compilation_data(compilation_data)
        
        with patch.object(planning_stage, 'log') as mock_log:
            cpp_files = planning_stage._get_cpp_files_for_struct("UserData")
            
            # Should log which detection method was used
            mock_log.debug.assert_called()
            log_calls = [call.args[0] for call in mock_log.debug.call_args_list]
            assert any("compilation data" in call.lower() for call in log_calls)
    
    @pytest.mark.integration
    def test_end_to_end_cpp_detection(self, planning_stage, temp_dir):
        """Test end-to-end .cpp file detection from compilation data."""
        # Create realistic file structure
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        
        header = src_dir / "user.h"
        impl1 = src_dir / "user_impl.cpp"
        impl2 = src_dir / "user_factory.cpp"
        
        header.write_text("""
        struct UserData {
            int id;
            char* name;
            UserData(int i);
            static UserData create(const char* n);
        };
        """)
        
        impl1.write_text("""
        #include "user.h"
        UserData::UserData(int i) : id(i), name(nullptr) {}
        """)
        
        impl2.write_text("""
        #include "user.h"
        UserData::UserData(const char* n) : name(strdup(n)), id(0) {}
        UserData UserData::create(const char* n) {
            return UserData(n);
        }
        """)
        
        # Simulate compilation data from pahole
        compilation_data = {
            "UserData": [str(impl1), str(impl2)]
        }
        planning_stage._set_compilation_data(compilation_data)
        
        # Create optimization plan
        struct_info = StructInfo(
            name="UserData",
            size=16,
            members=(
                MemberInfo(name="id", type="int", size=4, offset=0, access_modifier="public"),
                MemberInfo(name="name", type="char*", size=8, offset=8, access_modifier="public"),
            ),
            file_path=str(header),
            line=2
        )
        
        plan = OptimizationPlan(
            struct=struct_info,
            original_order=struct_info.members,
            optimal_order=struct_info.members,
            padding_saved=0,
            skip_reason=None
        )
        
        # Test that both .cpp files are detected and modifications created
        cpp_modifications = planning_stage._create_cpp_modifications(plan)
        
        # Should create modifications for both implementation files
        assert len(cpp_modifications) == 2
        cpp_files = [mod.file_path for mod in cpp_modifications]
        assert str(impl1) in cpp_files
        assert str(impl2) in cpp_files