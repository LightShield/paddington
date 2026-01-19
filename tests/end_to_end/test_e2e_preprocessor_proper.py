"""E2E tests for preprocessor directive handling - FR-1.8."""

import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestPreprocessorDirectives(BaseE2ETest):
    """E2E tests for preprocessor directive handling - verifies FR-1.8."""
    
    @pytest.mark.e2e
    def test_ifdef_struct_skipped(self, tmp_path):
        """Test that struct with #ifdef in member definitions is skipped - FR-1.8."""
        test_case = E2ETestCase(
            name="ifdef_struct_skipped",
            cpp_code="""
            struct ConditionalMembers {
                char a;
            #ifdef DEBUG
                int debug_field;
            #endif
                char b;
            };
            int main() {
                ConditionalMembers s;
                return 0;
            }
            """,
            flags={'extractor': 'auto'},
            expected_structs=[
                StructExpectation(
                    name="ConditionalMembers",
                    size_before=8,  # Will vary based on DEBUG flag
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="has preprocessor directives"
                )
            ],
            should_succeed=True,
            expected_output_contains=["SKIPPED", "preprocessor directives"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_macro_members_handled(self, tmp_path):
        """Test struct with macro-defined member types - FR-1.8."""
        test_case = E2ETestCase(
            name="macro_members_handled",
            cpp_code="""
            #define TYPE int
            struct MacroData {
                char a;
                TYPE b;
                char c;
            };
            int main() {
                MacroData s;
                return 0;
            }
            """,
            flags={'extractor': 'auto'},
            expected_structs=[
                StructExpectation(
                    name="MacroData",
                    size_before=12,
                    size_after=8,
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["Optimized"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_pragma_pack_skipped(self, tmp_path):
        """Test that struct with #pragma pack is skipped - FR-1.8."""
        test_case = E2ETestCase(
            name="pragma_pack_skipped",
            cpp_code="""
            #pragma pack(1)
            struct PackedStruct {
                char a;
                int b;
                char c;
            };
            #pragma pack()
            int main() {
                PackedStruct s;
                return 0;
            }
            """,
            flags={'extractor': 'auto'},
            expected_structs=[
                StructExpectation(
                    name="PackedStruct",
                    size_before=6,  # Packed size
                    size_after=6,
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['a', 'b', 'c'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="has preprocessor directives"
                )
            ],
            should_succeed=True,
            expected_output_contains=["SKIPPED", "preprocessor directives"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_conditional_compilation(self, tmp_path):
        """Test struct with #if/#elif/#endif platform-specific members - FR-1.8."""
        test_case = E2ETestCase(
            name="conditional_compilation",
            cpp_code="""
            struct PlatformStruct {
                char common;
            #if defined(__linux__)
                int linux_field;
            #elif defined(__APPLE__)
                int apple_field;
            #else
                int default_field;
            #endif
                char end;
            };
            int main() {
                PlatformStruct s;
                return 0;
            }
            """,
            flags={'extractor': 'auto'},
            expected_structs=[
                StructExpectation(
                    name="PlatformStruct",
                    size_before=12,
                    size_after=12,
                    member_order_before=['common', 'end'],
                    member_order_after=['common', 'end'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="has preprocessor directives"
                )
            ],
            should_succeed=True,
            expected_output_contains=["SKIPPED", "preprocessor directives"]
        )
        self.run_test_case(test_case, tmp_path)