"""E2E tests for template optimization - FR-1.7."""

import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestTemplatesProper(BaseE2ETest):
    """Test template instantiation optimization."""

    @pytest.mark.e2e
    def test_template_instantiation_optimized(self, tmp_path):
        """Verifies FR-1.7: Template instantiations are optimized."""
        test_case = E2ETestCase(
            name="template_instantiation_optimized",
            cpp_code="""
template<typename T>
struct Container {
    char a;
    T value;
    int b;
};

Container<int> c;
            """,
            flags={},
            expected_structs=[
                StructExpectation(
                    name="Container<int>",
                    size_before=12,
                    size_after=8,
                    member_order_before=["a", "value", "b"],
                    member_order_after=["value", "b", "a"],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["Changes applied"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_template_definition_skipped(self, tmp_path):
        """Verifies FR-1.7: Template definitions are skipped (T has unknown size)."""
        test_case = E2ETestCase(
            name="template_definition_skipped",
            cpp_code="""
template<typename T>
struct Container {
    char a;
    T value;
    int b;
};
            """,
            flags={},
            expected_structs=[],
            should_succeed=True,
            expected_output_contains=["Changes applied: 0"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_multiple_instantiations_independent(self, tmp_path):
        """Verifies FR-1.7: Multiple instantiations optimized independently."""
        test_case = E2ETestCase(
            name="multiple_instantiations_independent",
            cpp_code="""
template<typename T>
struct Container {
    char a;
    T value;
    int b;
};

Container<char> c1;
Container<int> c2;
Container<double> c3;
            """,
            flags={},
            expected_structs=[
                StructExpectation(
                    name="Container<char>",
                    size_before=8,
                    size_after=6,
                    member_order_before=["a", "value", "b"],
                    member_order_after=["b", "a", "value"],
                    padding_saved=2,
                    should_optimize=True
                ),
                StructExpectation(
                    name="Container<int>",
                    size_before=12,
                    size_after=8,
                    member_order_before=["a", "value", "b"],
                    member_order_after=["value", "b", "a"],
                    padding_saved=4,
                    should_optimize=True
                ),
                StructExpectation(
                    name="Container<double>",
                    size_before=16,
                    size_after=16,
                    member_order_before=["a", "value", "b"],
                    member_order_after=["value", "b", "a"],
                    padding_saved=0,
                    should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["Changes applied"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_template_with_different_sizes(self, tmp_path):
        """Verifies FR-1.7: Different instantiations have different optimal orders."""
        test_case = E2ETestCase(
            name="template_with_different_sizes",
            cpp_code="""
template<typename T>
struct Container {
    char a;
    T value;
    int b;
};

Container<char> small;
Container<double> large;
            """,
            flags={},
            expected_structs=[
                StructExpectation(
                    name="Container<char>",
                    size_before=8,
                    size_after=6,
                    member_order_before=["a", "value", "b"],
                    member_order_after=["b", "a", "value"],
                    padding_saved=2,
                    should_optimize=True
                ),
                StructExpectation(
                    name="Container<double>",
                    size_before=16,
                    size_after=16,
                    member_order_before=["a", "value", "b"],
                    member_order_after=["value", "b", "a"],
                    padding_saved=0,
                    should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["Changes applied"]
        )
        self.run_test_case(test_case, tmp_path)