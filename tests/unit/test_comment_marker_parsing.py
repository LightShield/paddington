"""Test for comment markers being parsed as member names."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.extraction.pahole import PaholeExtractor


@pytest.mark.unit
class TestCommentMarkerParsing:
    """Test that comment markers are not parsed as member names."""
    
    def test_pahole_comment_parsing(self):
        """Test that pahole parser doesn't extract */ as a member name.
        
        Bug: When pahole output contains comment-like patterns in member lines,
        the */ might be extracted as a member name.
        
        This tests the actual pahole parser with realistic output.
        """
        # Simulated pahole output that might cause the bug
        pahole_output = """/* <6e11c> /test/Callback.h:63 */
class RegisterWriteCallbackInstance {
public:

\t/* class RegisterWriteCallback <ancestor>; */ /*     0     8 */
\tclass RegisterFile *       m_classInst;          /*     8     8 */
\tfunction                   m_functionPtr;        /*    16    16 */
\tcntx_function              m_cntx_functionPtr;   /*    32    16 */
\tbool                       user_cntx_valid;      /*    48     1 */
\tunsigned int               m_cntx;               /*    52     4 */
\tbool                       m_is_attr_cb;         /*    56     1 */

\t/* size: 64, cachelines: 1, members: 7 */
};
"""
        
        extractor = PaholeExtractor()
        structs = extractor._parse_pahole_output(pahole_output)
        
        assert len(structs) == 1, f"Expected 1 struct, got {len(structs)}"
        
        struct = structs[0]
        member_names = [m.name for m in struct.members]
        
        # BUG: member_names should NOT contain */ or other comment markers
        assert '*/' not in member_names, \
            f"BUG: Comment marker '*/' found in member list: {member_names}"
        assert '/*' not in member_names, \
            f"BUG: Comment marker '/*' found in member list: {member_names}"
        
        # Should only have actual member names
        expected_members = ['m_classInst', 'm_functionPtr', 'm_cntx_functionPtr', 
                          'user_cntx_valid', 'm_cntx', 'm_is_attr_cb']
        assert member_names == expected_members, \
            f"Expected {expected_members}, got {member_names}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
