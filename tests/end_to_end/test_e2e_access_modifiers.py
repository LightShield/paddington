"""E2E tests for access modifier strategies with proper verification."""

import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestAccessModifiers(BaseE2ETest):
    """Access modifier strategy tests with proper verification."""
    
    @pytest.mark.e2e
    def test_preserve_strategy(self, tmp_path):
        """Test preserve strategy - reorder within sections."""
        test_case = E2ETestCase(
            name="preserve_strategy",
            cpp_code="""
            class Data {
            public:
                char a;
                int b;
            private:
                char c;
                double d;
            };
            int main() { Data d; return 0; }
            """,
            flags={
                'access_modifier_strategy': 'preserve',
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Data",
                    size_before=24,
                    size_after=20,
                    member_order_before=['a', 'b', 'c', 'd'],
                    member_order_after=['b', 'a', 'd', 'c'],  # Reordered within sections
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_split_strategy(self, tmp_path):
        """Test split strategy - optimal with per-member modifiers."""
        test_case = E2ETestCase(
            name="split_strategy",
            cpp_code="""
            class Data {
            public:
                char a;
            private:
                double d;
            public:
                int b;
            };
            int main() { Data d; return 0; }
            """,
            flags={
                'access_modifier_strategy': 'split',
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Data",
                    size_before=24,
                    size_after=16,
                    member_order_before=['a', 'd', 'b'],
                    member_order_after=['d', 'b', 'a'],  # Optimal order
                    padding_saved=8,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_ignore_strategy(self, tmp_path):
        """Test ignore strategy - reorder across all sections."""
        test_case = E2ETestCase(
            name="ignore_strategy",
            cpp_code="""
            class Data {
            public:
                char a;
            private:
                double d;
            public:
                int b;
            };
            int main() { Data d; return 0; }
            """,
            flags={
                'access_modifier_strategy': 'ignore',
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Data",
                    size_before=24,
                    size_after=16,
                    member_order_before=['a', 'd', 'b'],
                    member_order_after=['d', 'b', 'a'],
                    padding_saved=8,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
