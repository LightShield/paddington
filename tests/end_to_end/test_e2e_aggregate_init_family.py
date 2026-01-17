"""E2E tests for FR-1.1.3 Aggregate Initialization functionality."""

import pytest
from pathlib import Path
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestAggregateInitFamily(BaseE2ETest):
    """Aggregate initialization e2e tests. Verifies: FR-1.1.3 (Aggregate Init)"""
    
    @pytest.mark.e2e
    def test_aggregate_simple(self, tmp_path):
        """Verifies: FR-1.1.3 (Aggregate Init) - Data d = {1, 2, 3};"""
        test_case = E2ETestCase(
            name="aggregate_simple",
            cpp_code="""
            struct Data {
                char a;
                int b;
                char c;
            };
            int main() {
                Data d = {1, 2, 3};
                return 0;
            }
            """,
            flags={'apply': True, 'extractor': 'dwarf'},
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
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_aggregate_nested(self, tmp_path):
        """Verifies: FR-1.1.3 (Aggregate Init) - Nested struct initialization"""
        test_case = E2ETestCase(
            name="aggregate_nested",
            cpp_code="""
            struct Inner {
                char x;
                int y;
            };
            struct Outer {
                char a;
                Inner inner;
                char b;
            };
            int main() {
                Outer o = {1, {2, 3}, 4};
                return 0;
            }
            """,
            flags={'apply': True, 'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Inner",
                    size_before=8,
                    size_after=8,
                    member_order_before=['x', 'y'],
                    member_order_after=['y', 'x'],
                    padding_saved=0,
                    should_optimize=True
                ),
                StructExpectation(
                    name="Outer",
                    size_before=16,
                    size_after=12,
                    member_order_before=['a', 'inner', 'b'],
                    member_order_after=['inner', 'a', 'b'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_aggregate_array(self, tmp_path):
        """Verifies: FR-1.1.3 (Aggregate Init) - Array of structs"""
        test_case = E2ETestCase(
            name="aggregate_array",
            cpp_code="""
            struct Data {
                char a;
                int b;
            };
            int main() {
                Data arr[] = {{1, 2}, {3, 4}, {5, 6}};
                return 0;
            }
            """,
            flags={'apply': True, 'extractor': 'dwarf'},
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
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_aggregate_designated(self, tmp_path):
        """Verifies: FR-1.1.3 (Aggregate Init) - C++20 designated initializers"""
        test_case = E2ETestCase(
            name="aggregate_designated",
            cpp_code="""
            struct Data {
                char a;
                int b;
                char c;
            };
            int main() {
                Data d = {.a = 1, .b = 2, .c = 3};
                return 0;
            }
            """,
            flags={'apply': True, 'extractor': 'dwarf'},
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
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_aggregate_partial(self, tmp_path):
        """Verifies: FR-1.1.3 (Aggregate Init) - Partial initialization"""
        test_case = E2ETestCase(
            name="aggregate_partial",
            cpp_code="""
            struct Data {
                char a;
                int b;
                char c;
            };
            int main() {
                Data d = {1, 2};  // c defaults to 0
                return 0;
            }
            """,
            flags={'apply': True, 'extractor': 'dwarf'},
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
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_aggregate_uniform(self, tmp_path):
        """Verifies: FR-1.1.3 (Aggregate Init) - Uniform initialization Data d{1, 2, 3};"""
        test_case = E2ETestCase(
            name="aggregate_uniform",
            cpp_code="""
            struct Data {
                char a;
                int b;
                char c;
            };
            int main() {
                Data d{1, 2, 3};
                return 0;
            }
            """,
            flags={'apply': True, 'extractor': 'dwarf'},
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
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)