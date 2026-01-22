"""Test for access modifier boundary preservation."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestAccessModifierBoundaries:
    """Test that access modifiers are preserved correctly during reordering."""
    
    def test_members_before_public_stay_protected(self):
        """Test that members before public: keyword stay in protected section.
        
        Bug: Members at the end of protected section (right before public:)
        get moved up in protected section, but the public: keyword also moves,
        corrupting the class structure.
        
        Example from RBA.h:
        protected:
            member1;
            member2;  // These are protected
            member3;  // Right before public:
        public:
            method();
        
        After transformation, member3 moves up but public: also moves incorrectly.
        """
        test_code = """
class Test {
protected:
    int a;
    double b;
    char c;  // Last protected member
public:
    void method();
};
"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(test_code)
            
            # Create modification to reorder: b, a, c (double first)
            mod = SourceModification(
                file_path=str(test_file),
                struct_name="Test",
                modifications=(
                    Modification(
                        type='reorder',
                        location=Location(file=str(test_file), line=2, column=0),
                        old_content="members: a, b, c",
                        new_content="members: b, a, c",
                        access_strategy='preserve'
                    ),
                ),
                access_strategy='preserve'
            )
            
            transformer = SrcMLTransformer()
            transformed = transformer.transform([mod])
            
            assert len(transformed) > 0, "Transformation failed"
            
            new_content = transformed[0].new_content
            
            # Verify structure
            assert 'protected:' in new_content, "protected: keyword missing"
            assert 'public:' in new_content, "public: keyword missing"
            
            # Find positions
            protected_pos = new_content.index('protected:')
            public_pos = new_content.index('public:')
            
            # All members should be between protected: and public:
            protected_section = new_content[protected_pos:public_pos]
            
            assert 'double b' in protected_section, "Member b should be in protected"
            assert 'int a' in protected_section, "Member a should be in protected"
            assert 'char c' in protected_section, "Member c should be in protected"
            
            # Method should be after public:
            public_section = new_content[public_pos:]
            assert 'void method()' in public_section, "Method should be in public section"
            
            # Critical: No members should appear after public:
            assert 'double b' not in public_section, "Member b leaked into public section!"
            assert 'int a' not in public_section, "Member a leaked into public section!"
            assert 'char c' not in public_section, "Member c leaked into public section!"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
