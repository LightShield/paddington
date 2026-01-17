import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestE2EDirectivesFamily(BaseE2ETest):
    """Verifies: FR-1.2.1 - Opt-Out Markers Test Family"""
    
    @pytest.mark.e2e
    def test_ignore_single_struct(self, tmp_path):
        """Test ignoring a single struct with paddington-ignore marker"""
        test_case = E2ETestCase(
            name="ignore_single_struct",
            cpp_code="""
            // paddington-ignore
            struct IgnoredStruct {
                char a;
                int b;
            };
            struct ProcessedStruct {
                char a;
                int b;
            };
            int main() {
                IgnoredStruct ignored;
                ProcessedStruct processed;
                return 0;
            }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="IgnoredStruct",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                ),
                StructExpectation(
                    name="ProcessedStruct",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_ignore_multiple_structs(self, tmp_path):
        """Test ignoring multiple structs with paddington-ignore markers"""
        test_case = E2ETestCase(
            name="ignore_multiple_structs",
            cpp_code="""
            // paddington-ignore
            struct FirstIgnored {
                char a;
                int b;
            };
            struct ProcessedStruct {
                char a;
                int b;
            };
            // paddington-ignore
            struct SecondIgnored {
                char a;
                int b;
            };
            int main() {
                FirstIgnored first;
                ProcessedStruct processed;
                SecondIgnored second;
                return 0;
            }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="FirstIgnored",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                ),
                StructExpectation(
                    name="ProcessedStruct",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=True
                ),
                StructExpectation(
                    name="SecondIgnored",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_ignore_comment_styles(self, tmp_path):
        """Test ignoring structs with different comment styles (// vs /* */)"""
        test_case = E2ETestCase(
            name="ignore_comment_styles",
            cpp_code="""
            // paddington-ignore
            struct SingleLineIgnored {
                char a;
                int b;
            };
            /* paddington-ignore */
            struct BlockCommentIgnored {
                char a;
                int b;
            };
            struct ProcessedStruct {
                char a;
                int b;
            };
            int main() {
                SingleLineIgnored single;
                BlockCommentIgnored block;
                ProcessedStruct processed;
                return 0;
            }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="SingleLineIgnored",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                ),
                StructExpectation(
                    name="BlockCommentIgnored",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                ),
                StructExpectation(
                    name="ProcessedStruct",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_ignore_case_variations(self, tmp_path):
        """Test ignoring structs with case variations of paddington-ignore"""
        test_case = E2ETestCase(
            name="ignore_case_variations",
            cpp_code="""
            // PADDINGTON-IGNORE
            struct UpperCaseIgnored {
                char a;
                int b;
            };
            // Paddington-Ignore
            struct MixedCaseIgnored {
                char a;
                int b;
            };
            struct ProcessedStruct {
                char a;
                int b;
            };
            int main() {
                UpperCaseIgnored upper;
                MixedCaseIgnored mixed;
                ProcessedStruct processed;
                return 0;
            }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="UpperCaseIgnored",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                ),
                StructExpectation(
                    name="MixedCaseIgnored",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                ),
                StructExpectation(
                    name="ProcessedStruct",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_ignore_with_whitespace(self, tmp_path):
        """Test ignoring structs with whitespace around paddington-ignore marker"""
        test_case = E2ETestCase(
            name="ignore_with_whitespace",
            cpp_code="""
            //   paddington-ignore   
            struct WhitespaceIgnored {
                char a;
                int b;
            };
            /*  paddington-ignore  */
            struct BlockWhitespaceIgnored {
                char a;
                int b;
            };
            struct ProcessedStruct {
                char a;
                int b;
            };
            int main() {
                WhitespaceIgnored whitespace;
                BlockWhitespaceIgnored blockWhitespace;
                ProcessedStruct processed;
                return 0;
            }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="WhitespaceIgnored",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                ),
                StructExpectation(
                    name="BlockWhitespaceIgnored",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="marked ignore"
                ),
                StructExpectation(
                    name="ProcessedStruct",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)