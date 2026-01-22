"""Test for comment markers being parsed as member names."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestCommentMarkerParsing:
    """Test that comment markers are not parsed as member names."""
    
    def test_comment_end_not_member(self):
        """Test that */ from comments is not extracted as a member name.
        
        Bug: Comment blocks like /* ... */ have their end marker */
        extracted as a member name.
        
        Example from Callback.h:
        class Test {
            /* Comment about members */
            int m_member;
        };
        
        The */ is being extracted as a member, appearing in new_order.
        """
        test_code = """class Test {
protected:
    /* This is a comment about the members below */
    int m_first;
    double m_second;
};
"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(test_code)
            
            mod = SourceModification(
                file_path=str(test_file),
                struct_name="Test",
                modifications=(
                    Modification(
                        type='reorder',
                        location=Location(file=str(test_file), line=1, column=0),
                        old_content="members: m_first, m_second",
                        new_content="members: m_second, m_first",
                        access_strategy='preserve'
                    ),
                ),
                access_strategy='preserve'
            )
            
            transformer = SrcMLTransformer()
            
            # Extract the new order to check what members were found
            new_order = transformer._extract_new_order(mod)
            
            # BUG: new_order should NOT contain */ or other comment markers
            assert '*/' not in new_order, \
                f"BUG: Comment marker '*/' found in member list: {new_order}"
            assert '/*' not in new_order, \
                f"BUG: Comment marker '/*' found in member list: {new_order}"
            
            # Should only have actual member names
            assert 'm_first' in new_order
            assert 'm_second' in new_order
            assert len(new_order) == 2, \
                f"Expected 2 members, got {len(new_order)}: {new_order}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
