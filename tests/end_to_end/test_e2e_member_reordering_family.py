import pytest
from pathlib import Path
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation

class TestMemberReordering(BaseE2ETest):
    @pytest.mark.e2e
    def test_basic_char_int_reordering(self, tmp_path):
        """Basic char-int reordering optimization.
        
        Verifies: FR-1.1.2 (Member Reordering - Basic Case)
        """
        test_case = E2ETestCase(
            name="test_basic_char_int_reordering",
            cpp_code="""struct S { char a; int b; }; int main() { S s; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="S",
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

    @pytest.mark.e2e
    def test_multiple_char_int_gaps(self, tmp_path):
        """Multiple char-int gaps creating padding holes.
        
        Verifies: FR-1.1.2 (Member Reordering - Multiple Gaps)
        """
        test_case = E2ETestCase(
            name="test_multiple_char_int_gaps",
            cpp_code="""struct Data { char a; int b; char c; int d; }; int main() { Data d; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Data",
                    size_before=16,
                    size_after=12,
                    member_order_before=['a', 'b', 'c', 'd'],
                    member_order_after=['b', 'd', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_mixed_type_sizes(self, tmp_path):
        """Mixed type sizes requiring optimal reordering.
        
        Verifies: FR-1.1.2 (Member Reordering - Mixed Types)
        """
        test_case = E2ETestCase(
            name="test_mixed_type_sizes",
            cpp_code="""struct Mixed { char a; double b; short c; int d; }; int main() { Mixed m; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Mixed",
                    size_before=24,
                    size_after=16,
                    member_order_before=['a', 'b', 'c', 'd'],
                    member_order_after=['b', 'd', 'c', 'a'],
                    padding_saved=8,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_already_optimal_struct(self, tmp_path):
        """Already optimally ordered struct should not change.
        
        Verifies: FR-1.1.2 (Member Reordering - No Change Needed)
        """
        test_case = E2ETestCase(
            name="test_already_optimal_struct",
            cpp_code="""struct Optimal { int a; int b; char c; char d; }; int main() { Optimal o; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Optimal",
                    size_before=12,
                    size_after=12,
                    member_order_before=['a', 'b', 'c', 'd'],
                    member_order_after=['a', 'b', 'c', 'd'],
                    padding_saved=0,
                    should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_large_padding_savings(self, tmp_path):
        """Large struct with significant padding savings.
        
        Verifies: FR-1.1.2 (Member Reordering - Large Savings)
        """
        test_case = E2ETestCase(
            name="test_large_padding_savings",
            cpp_code="""struct Large { char a; long b; char c; long d; char e; long f; }; int main() { Large l; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Large",
                    size_before=48,
                    size_after=32,
                    member_order_before=['a', 'b', 'c', 'd', 'e', 'f'],
                    member_order_after=['b', 'd', 'f', 'a', 'c', 'e'],
                    padding_saved=16,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_pointer_alignment_reordering(self, tmp_path):
        """Pointer alignment requiring reordering.
        
        Verifies: FR-1.1.2 (Member Reordering - Pointer Alignment)
        """
        test_case = E2ETestCase(
            name="test_pointer_alignment_reordering",
            cpp_code="""struct Ptrs { char a; void* b; char c; void* d; }; int main() { Ptrs p; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Ptrs",
                    size_before=32,
                    size_after=24,
                    member_order_before=['a', 'b', 'c', 'd'],
                    member_order_after=['b', 'd', 'a', 'c'],
                    padding_saved=8,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_array_member_reordering(self, tmp_path):
        """Array members requiring reordering.
        
        Verifies: FR-1.1.2 (Member Reordering - Array Members)
        """
        test_case = E2ETestCase(
            name="test_array_member_reordering",
            cpp_code="""struct Arrays { char a; int b[2]; char c; int d[2]; }; int main() { Arrays arr; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Arrays",
                    size_before=24,  # char + pad(3) + int[2](8) + char + pad(3) + int[2](8)
                    size_after=20,   # int[2](8) + int[2](8) + char + char + pad(2)
                    member_order_before=['a', 'b', 'c', 'd'],
                    member_order_after=['b', 'd', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_nested_struct_reordering(self, tmp_path):
        """Nested struct with reordering opportunities.
        
        Verifies: FR-1.1.2 (Member Reordering - Nested Structs)
        """
        test_case = E2ETestCase(
            name="test_nested_struct_reordering",
            cpp_code="""struct Inner { char x; int y; }; struct Outer { char a; Inner b; char c; }; int main() { Outer o; return 0; }""",
            flags={'extractor': 'dwarf'},
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
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_bitfield_member_reordering(self, tmp_path):
        """Bitfield members with reordering needs.
        
        Verifies: FR-1.1.2 (Member Reordering - Bitfields)
        """
        test_case = E2ETestCase(
            name="test_bitfield_member_reordering",
            cpp_code="""struct Bits { char a; int b : 4; int c : 4; char d; }; int main() { Bits b; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Bits",
                    size_before=4,   # Bitfields pack tightly
                    size_after=4,    # No optimization possible
                    member_order_before=['a', 'b', 'c', 'd'],
                    member_order_after=['a', 'b', 'c', 'd'],
                    padding_saved=0,
                    should_optimize=False,  # Bitfields shouldn't be reordered
                    skip_reason="bitfields"
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_union_member_reordering(self, tmp_path):
        """Union with struct members requiring reordering.
        
        Verifies: FR-1.1.2 (Member Reordering - Union Context)
        """
        test_case = E2ETestCase(
            name="test_union_member_reordering",
            cpp_code="""struct S { char a; int b; }; union U { S s; long l; }; int main() { U u; return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="S",
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