"""E2E tests for user directives (paddington-ignore, paddington-lock)."""

import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestDirectives(BaseE2ETest):
    """User directive e2e tests."""
    
    @pytest.mark.e2e
    def test_paddington_ignore_marker(self, tmp_path):
        """Test paddington-ignore marker skips struct.
        
        Verifies: FR-1.2.1 (Opt-Out Markers - Struct Level)
        """
        test_case = E2ETestCase(
            name="paddington_ignore",
            cpp_code="""
            // paddington-ignore
            struct DontTouch {
                char a;
                int b;
                char c;
            };
            int main() { DontTouch d; return 0; }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="DontTouch",
                    size_before=12,
                    size_after=12,
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['a', 'b', 'c'],
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
    def test_paddington_lock_marker(self, tmp_path):
        """Test paddington-lock marker keeps member in place.
        
        Verifies: FR-1.2.2 (Opt-Out Markers - Member Level)
        """
        test_case = E2ETestCase(
            name="paddington_lock",
            cpp_code="""
            struct Partial {
                char a;
                // paddington-lock
                int b;
                // paddington-unlock
                char c;
            };
            int main() { Partial p; return 0; }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Partial",
                    size_before=12,
                    size_after=12,
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['a', 'b', 'c'],  # b is locked
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="has locked members"
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_paddington_off_on_markers(self, tmp_path):
        """Test paddington-off/on markers skip region.
        
        Verifies: FR-1.2.3 (Opt-Out Markers - Region Level)
        """
        test_case = E2ETestCase(
            name="paddington_off_on",
            cpp_code="""
            // paddington-off
            struct Skipped {
                char a;
                int b;
            };
            // paddington-on
            struct Processed {
                char x;
                int y;
                char z;
            };
            int main() { Skipped s; Processed p; return 0; }
            """,
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Skipped",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="in disabled region"
                ),
                StructExpectation(
                    name="Processed",
                    size_before=12,
                    size_after=8,
                    member_order_before=['x', 'y', 'z'],
                    member_order_after=['y', 'x', 'z'],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)
