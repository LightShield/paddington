"""Example of properly verified e2e test."""

import pytest
from pathlib import Path
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestProperVerification(BaseE2ETest):
    """E2E tests with proper verification."""
    
    @pytest.mark.e2e
    def test_simple_struct_optimization(self, tmp_path):
        """Test simple struct optimization with full verification."""
        test_case = E2ETestCase(
            name="simple_struct_optimization",
            cpp_code="""
            struct Simple {
                char a;      // 1 byte
                int b;       // 4 bytes
                char c;      // 1 byte
            };
            int main() { Simple s; return 0; }
            """,
            flags={
                'apply': True,
                'output': 'file',
                'extractor': 'dwarf',
                'transformer': 'line-swap'
            },
            expected_structs=[
                StructExpectation(
                    name="Simple",
                    size_before=12,  # char(1) + pad(3) + int(4) + char(1) + pad(3)
                    size_after=8,    # int(4) + char(1) + char(1) + pad(2)
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],  # int first (largest)
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"],
            expected_patches_count=None  # Using file output, not patches
        )
        
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_already_optimal_struct(self, tmp_path):
        """Test struct that's already optimal (no changes)."""
        test_case = E2ETestCase(
            name="already_optimal",
            cpp_code="""
            struct Optimal {
                double a;    // 8 bytes (largest first)
                int b;       // 4 bytes
                char c;      // 1 byte
            };
            int main() { Optimal o; return 0; }
            """,
            flags={
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Optimal",
                    size_before=16,  # Already optimal
                    size_after=16,   # No change
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['a', 'b', 'c'],  # Same order
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="no padding to save"
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"],
            expected_patches_count=0  # No optimization needed
        )
        
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_nested_struct_with_size_propagation(self, tmp_path):
        """Test nested structs with size propagation verification."""
        test_case = E2ETestCase(
            name="nested_struct_propagation",
            cpp_code="""
            struct Inner {
                char a;      // 1 byte
                int b;       // 4 bytes
                char c;      // 1 byte
            };
            struct Outer {
                char x;      // 1 byte
                Inner inner; // Size depends on Inner optimization
                int y;       // 4 bytes
            };
            int main() { Inner i; Outer o; return 0; }
            """,
            flags={
                'apply': True,
                'output': 'patch',
                'patch_dir': str(tmp_path / "patches"),
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Inner",
                    size_before=12,  # char + pad + int + char + pad
                    size_after=8,    # int + char + char + pad
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                ),
                StructExpectation(
                    name="Outer",
                    size_before=20,  # char + pad + Inner(12) + int
                    size_after=16,   # Inner(8) + int + char + pad (after Inner optimized)
                    member_order_before=['x', 'inner', 'y'],
                    member_order_after=['inner', 'y', 'x'],  # Reordered based on new Inner size
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"],  # apply=True
            expected_patches_count=2  # One patch per struct
        )
        
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_min_savings_threshold(self, tmp_path):
        """Test minimum savings threshold skips small optimizations."""
        test_case = E2ETestCase(
            name="min_savings_threshold",
            cpp_code="""
            struct Small {
                char a;
                short b;  // Only 1 byte padding
            };
            int main() { Small s; return 0; }
            """,
            flags={
                'min_savings': 10,  # Require at least 10 bytes savings
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Small",
                    size_before=4,
                    size_after=4,  # Would save <10 bytes, so skipped
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],  # No change
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

    def compile_cpp(self, cpp_file, output_name="test.o"):
        """Compile C++ file."""
