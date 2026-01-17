"""E2E tests for complex C++ features."""

import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestComplexCpp(BaseE2ETest):
    """Complex C++ feature e2e tests."""
    
    @pytest.mark.e2e
    def test_inheritance_derived_members_only(self, tmp_path):
        """Test inheritance - only derived members reordered.
        
        Verifies: FR-1.9 (Complex C++ Features - Inheritance)
        """
        test_case = E2ETestCase(
            name="inheritance",
            cpp_code="""
            struct Base {
                char a;
                int b;
            };
            struct Derived : Base {
                char c;
                double d;
            };
            int main() { Derived d; return 0; }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Derived",
                    size_before=24,
                    size_after=24,
                    member_order_before=['c', 'd'],
                    member_order_after=['d', 'c'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_bitfields_skipped(self, tmp_path):
        """Test bitfields are skipped.
        
        Verifies: FR-1.9 (Complex C++ Features - Bitfields)
        """
        test_case = E2ETestCase(
            name="bitfields",
            cpp_code="""
            struct Flags {
                unsigned int a : 1;
                unsigned int b : 3;
                unsigned int c : 4;
            };
            int main() { Flags f; return 0; }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[],  # May not appear in DWARF or be skipped
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_unions_skipped(self, tmp_path):
        """Test unions are skipped.
        
        Verifies: FR-1.9 (Complex C++ Features - Unions)
        """
        test_case = E2ETestCase(
            name="unions",
            cpp_code="""
            union Data {
                char c;
                int i;
                double d;
            };
            int main() { Data d; return 0; }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[],  # Unions should be skipped
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
