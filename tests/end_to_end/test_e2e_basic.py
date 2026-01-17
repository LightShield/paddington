"""E2E tests for basic functionality with proper verification."""

import pytest
from pathlib import Path
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestBasicFunctionality(BaseE2ETest):
    """Basic functionality e2e tests with proper verification."""
    
    @pytest.mark.e2e
    def test_simple_struct_dry_run(self, tmp_path):
        """Test simple struct in dry-run mode (default)."""
        test_case = E2ETestCase(
            name="simple_struct_dry_run",
            cpp_code="""
            struct Simple {
                char a;
                int b;
                char c;
            };
            int main() {
                Simple s;  // Must use struct for DWARF
                return 0;
            }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Simple",
                    size_before=12,
                    size_after=8,
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"],
            expected_patches_count=None
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_simple_struct_with_patch(self, tmp_path):
        """Test patch generation with actual padding savings."""
        test_case = E2ETestCase(
            name="simple_struct_patch",
            cpp_code="""
            struct Data {
                char flag;     // 1 byte
                int id;        // 4 bytes (3 bytes padding before)
                char status;   // 1 byte
                double score;  // 8 bytes (7 bytes padding before)
            };
            int main() { Data d; return 0; }
            """,
            flags={
                'output': 'patch',
                'patch_dir': str(tmp_path / "patches"),
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Data",
                    size_before=24,  # char + pad(3) + int + char + pad(7) + double
                    size_after=16,   # double + int + char + char + pad(2)
                    member_order_before=['flag', 'id', 'status', 'score'],
                    member_order_after=['score', 'id', 'flag', 'status'],
                    padding_saved=8,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"],
            expected_patches_count=1
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_simple_struct_with_file_output(self, tmp_path):
        """Test direct file modification with padding savings."""
        test_case = E2ETestCase(
            name="simple_struct_file",
            cpp_code="""
            struct Data {
                char a;        // 1 byte
                int b;         // 4 bytes (3 bytes padding before)
                char c;        // 1 byte
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
                    size_before=12,  # char + pad(3) + int + char + pad(3)
                    size_after=8,    # int + char + char + pad(2)
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"],
            expected_patches_count=None
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_min_savings_threshold(self, tmp_path):
        """Test minimum savings threshold."""
        test_case = E2ETestCase(
            name="min_savings_threshold",
            cpp_code="""
            struct Small {
                char a;
                short b;
            };
            int main() { Small s; return 0; }
            """,
            flags={
                'min_savings': 100,
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Small",
                    size_before=4,
                    size_after=4,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="below threshold"
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"],
            expected_patches_count=0
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_help_documentation(self):
        """Test help documentation."""
        import subprocess
        result = subprocess.run(
            ['python', '__main__.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        assert result.returncode == 0
        assert "--apply" in result.stdout
        assert "--min-savings" in result.stdout
