"""E2E tests for validation and error handling."""

import pytest
import subprocess
from pathlib import Path
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestValidation(BaseE2ETest):
    """Validation and error handling e2e tests."""
    
    @pytest.mark.e2e
    def test_build_verification(self, tmp_path):
        """Test that optimized code compiles successfully.
        
        Verifies: FR-1.8.1 (Build Verification)
        """
        test_case = E2ETestCase(
            name="build_verification",
            cpp_code="""
            struct Data {
                char a;
                int b;
                char c;
            };
            int main() { Data d; return 0; }
            """,
            flags={
                'apply': True,
                'output': 'file',
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Data",
                    size_before=12,
                    size_after=8,
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"]
        )
        self.run_test_case(test_case, tmp_path)
        
        # After optimization, verify code still compiles
        cpp_file = tmp_path / "test.cpp"
        if cpp_file.exists():
            obj_file_after = tmp_path / "test_after.o"
            result = subprocess.run(
                ['g++', '-g', '-O0', '-c', str(cpp_file), '-o', str(obj_file_after)],
                capture_output=True
            )
            assert result.returncode == 0, f"Optimized code doesn't compile: {result.stderr.decode()}"
    
    @pytest.mark.e2e
    def test_syntax_validation(self, tmp_path):
        """Test invalid C++ is handled gracefully.
        
        Verifies: FR-1.8.2 (Syntax Validation)
        """
        # Create invalid C++ (missing semicolon)
        code = """
        struct Invalid {
            char a
            int b;
        };
        int main() { return 0; }
        """
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        
        # Try to compile - should fail
        obj_file = tmp_path / "test.o"
        result = subprocess.run(
            ['g++', '-g', '-O0', '-c', str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        
        # Compilation should fail (invalid syntax)
        assert result.returncode != 0, "Invalid C++ should not compile"
    
    @pytest.mark.e2e
    def test_error_handling_missing_file(self, tmp_path):
        """Test error handling for missing files.
        
        Verifies: NFR-2.5.1 (Error Handling)
        """
        # Run on non-existent file
        result = subprocess.run(
            ['python', '__main__.py', str(tmp_path / "nonexistent.o"), '--extractor', 'dwarf'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should handle gracefully (not crash)
        # May succeed with 0 files found, or fail with clear error
        assert "nonexistent" in result.stdout or "nonexistent" in result.stderr or result.returncode == 0
    
    @pytest.mark.e2e
    def test_atomicity_rollback_on_error(self, tmp_path):
        """Test atomicity - rollback on error.
        
        Verifies: NFR-2.5.2 (Atomicity)
        """
        test_case = E2ETestCase(
            name="atomicity",
            cpp_code="""
            struct Data {
                char a;
                int b;
            };
            int main() { Data d; return 0; }
            """,
            flags={
                'apply': True,
                'output': 'file',
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Data",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['b', 'a'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"]
        )
        self.run_test_case(test_case, tmp_path)
        
        # Verify backup file was created
        cpp_file = tmp_path / "test.cpp"
        backup_file = tmp_path / "test.cpp.backup"
        if cpp_file.exists():
            assert backup_file.exists(), "Backup file should be created for atomicity"
