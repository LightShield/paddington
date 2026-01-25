"""Test for base class members being counted as real members."""

import pytest
from implementation.pipeline.extraction.pahole import PaholeExtractor
from implementation.pipeline.analysis.stage import AnalysisStage


@pytest.mark.unit
class TestBaseClassMembers:
    """Test that base class members (0-byte ancestors) are not counted."""
    
    def test_skip_struct_with_only_base_class(self):
        """Test that structs with only base class members are skipped.
        
        Bug: Structs like al_pcap_info_node have 1 real member but show 2
        because the base class (0 bytes) is counted as a member.
        
        Single-member structs should not be optimized.
        """
        # Simulated pahole output with base class
        pahole_output = """/* <1234> /test/test.h:10 */
class DerivedClass : public BaseClass {
public:

\t/* class BaseClass <ancestor>; */ /*     0     8 */
\tint m_only_member;                   /*     8     4 */

\t/* size: 16, cachelines: 1, members: 2 */
};
"""
        
        extractor = PaholeExtractor()
        structs, _ = extractor._parse_pahole_output(pahole_output)
        
        assert len(structs) == 1, f"Expected 1 struct, got {len(structs)}"
        
        struct = structs[0]
        
        # After the fix, base class should not be in members
        assert len(struct.members) == 1, \
            f"Expected 1 member (excluding base class), got {len(struct.members)}: {[m.name for m in struct.members]}"
        
        assert struct.members[0].name == 'm_only_member'
    
    def test_analysis_skips_single_member_structs(self):
        """Test that analysis stage skips structs with only 1 real member."""
        # Simulated pahole output
        pahole_output = """/* <1234> /test/test.h:10 */
class SingleMember {
public:

\tint m_only_member;                   /*     0     4 */

\t/* size: 8, cachelines: 1, members: 1 */
};
"""
        
        extractor = PaholeExtractor()
        structs, _ = extractor._parse_pahole_output(pahole_output)
        
        # Run through analysis
        analyzer = AnalysisStage()
        plans = analyzer.process(structs)
        
        # Should be skipped (no optimization needed for single member)
        optimizable_plans = [p for p in plans if not p.skip_reason]
        assert len(optimizable_plans) == 0, \
            "Single-member struct should be skipped"
    
    def test_zero_byte_members_filtered(self):
        """Test that 0-byte members (base classes) are filtered out.
        
        Some pahole outputs show base classes with 0 bytes.
        These should not be counted as real members.
        """
        pahole_output = """/* <1234> /test/test.h:10 */
class TestClass : public Base1, public Base2 {
public:

\t/* class Base1 <ancestor>; */ /*     0     0 */
\t/* class Base2 <ancestor>; */ /*     0     0 */
\tint m_real_member1;              /*     0     4 */
\tint m_real_member2;              /*     4     4 */

\t/* size: 8, cachelines: 1, members: 4 */
};
"""
        
        extractor = PaholeExtractor()
        structs, _ = extractor._parse_pahole_output(pahole_output)
        
        assert len(structs) == 1
        struct = structs[0]
        
        # Should only have the 2 real members, not the 0-byte base classes
        assert len(struct.members) == 2, \
            f"Expected 2 members (excluding 0-byte bases), got {len(struct.members)}: {[m.name for m in struct.members]}"
        
        member_names = [m.name for m in struct.members]
        assert 'm_real_member1' in member_names
        assert 'm_real_member2' in member_names


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
