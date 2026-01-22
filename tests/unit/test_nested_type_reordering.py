"""Test for moving nested types to top of their section."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestNestedTypeReordering:
    """Test that nested types are moved to top of their access section."""
    
    def test_typedef_moved_to_top_of_protected(self):
        """Test that typedef moves to top of protected section, before members.
        
        Solution: Move all nested type definitions to the top of their
        access section, then reorder members below them.
        """
        test_code = """class Test {
protected:
    int small_member;
    
    typedef struct {
        int value;
    } MyType;
    
    std::map<string, MyType> large_member;
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
                        old_content="members: small_member, large_member",
                        new_content="members: large_member, small_member",
                        access_strategy='preserve'
                    ),
                ),
                access_strategy='preserve'
            )
            
            transformer = SrcMLTransformer()
            transformed = transformer.transform([mod])
            
            assert len(transformed) > 0, "Transformation should succeed"
            
            new_content = transformed[0].new_content
            
            # Verify structure: typedef should be at top of protected
            protected_pos = new_content.find('protected:')
            typedef_pos = new_content.find('typedef')
            large_pos = new_content.find('large_member')
            small_pos = new_content.find('small_member')
            
            # Order should be: protected: -> typedef -> large_member -> small_member
            assert protected_pos < typedef_pos, "typedef should be in protected"
            assert typedef_pos < large_pos, "typedef before large_member"
            assert large_pos < small_pos, "large_member before small_member"
            
            # typedef should still be in protected section
            public_pos = new_content.find('public:') if 'public:' in new_content else len(new_content)
            assert typedef_pos < public_pos, "typedef should stay in protected, not leak to public"
    
    def test_multiple_nested_types_stay_in_order(self):
        """Test that multiple nested types maintain their relative order."""
        test_code = """class Test {
protected:
    int a;
    
    typedef int TypeA;
    typedef double TypeB;
    
    TypeB member_b;
    TypeA member_a;
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
                        old_content="members: a, member_b, member_a",
                        new_content="members: member_b, member_a, a",
                        access_strategy='preserve'
                    ),
                ),
                access_strategy='preserve'
            )
            
            transformer = SrcMLTransformer()
            transformed = transformer.transform([mod])
            
            assert len(transformed) > 0, "Transformation should succeed"
            
            new_content = transformed[0].new_content
            
            # Both typedefs should be at top, in their original order
            typea_pos = new_content.find('typedef int TypeA')
            typeb_pos = new_content.find('typedef double TypeB')
            member_b_pos = new_content.find('TypeB member_b')
            member_a_pos = new_content.find('TypeA member_a')
            
            # Typedefs should come first, in original order
            assert typea_pos < typeb_pos, "TypeA before TypeB (original order)"
            assert typeb_pos < member_b_pos, "Typedefs before members"
            assert typeb_pos < member_a_pos, "Typedefs before members"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
