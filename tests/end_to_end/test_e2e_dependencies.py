"""E2E tests for dependencies with proper verification."""

import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestDependencies(BaseE2ETest):
    """Dependency handling tests with proper verification."""
    
    @pytest.mark.e2e
    def test_nested_struct_two_levels(self, tmp_path):
        """Test Inner → Outer with size propagation."""
        test_case = E2ETestCase(
            name="nested_two_levels",
            cpp_code="""
            struct Inner {
                char a;
                int b;
            };
            struct Outer {
                int x;
                Inner inner;
                double y;
            };
            int main() { return 0; }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Inner",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['b', 'a'],
                    padding_saved=0,
                    should_optimize=True
                ),
                StructExpectation(
                    name="Outer",
                    size_before=24,
                    size_after=24,
                    member_order_before=['x', 'inner', 'y'],
                    member_order_after=['y', 'inner', 'x'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_shared_dependency(self, tmp_path):
        """Test leaf struct used by multiple parents."""
        test_case = E2ETestCase(
            name="shared_dependency",
            cpp_code="""
            struct Leaf {
                char a;
                int b;
            };
            struct Parent1 {
                Leaf l;
                int x;
            };
            struct Parent2 {
                Leaf l;
                double y;
            };
            int main() { return 0; }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Leaf",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['b', 'a'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
