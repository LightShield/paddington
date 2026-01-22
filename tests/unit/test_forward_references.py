"""Test for forward reference errors in member reordering."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestForwardReferences:
    """Test that reordering doesn't create forward reference errors."""
    
    def test_typedef_before_usage(self):
        """Test that typedef stays before members that use it.
        
        Bug from RBA.h: lockport_info_t typedef is defined at line 70,
        but lockport2regs (which uses it) was moved to line 51,
        causing 'lockport_info_t was not declared' error.
        
        Solution: Move nested types to top of their section, then reorder members.
        """
        test_code = """class Test {
protected:
    int small_member;
    
    typedef struct {
        int value;
    } MyType;
    
    std::map<string, MyType> large_member;  // Uses MyType
};
"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(test_code)
            
            # Reorder to put large_member first (it's larger)
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
            
            # With nested types, transformation should succeed with types moved to top
            assert len(transformed) > 0, \
                "Transformation should succeed with nested types moved to top"
            
            new_content = transformed[0].new_content
            
            # Verify that typedef comes before the member that uses it
            typedef_pos = new_content.find('typedef')
            large_member_pos = new_content.find('large_member')
            
            assert typedef_pos < large_member_pos, \
                "typedef should come before member that uses it"
    
    def test_nested_struct_before_usage(self):
        """Test that nested struct definition stays before members that use it."""
        test_code = """class Test {
protected:
    int a;
    
    struct NestedType {
        int value;
    };
    
    NestedType nested_member;
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
                        old_content="members: a, nested_member",
                        new_content="members: nested_member, a",
                        access_strategy='preserve'
                    ),
                ),
                access_strategy='preserve'
            )
            
            transformer = SrcMLTransformer()
            transformed = transformer.transform([mod])
            
            # With nested types, transformation should succeed with types moved to top
            assert len(transformed) > 0, \
                "Transformation should succeed with nested types moved to top"
            
            new_content = transformed[0].new_content
            
            # Verify that struct definition comes before the member that uses it
            struct_pos = new_content.find('struct NestedType')
            nested_member_pos = new_content.find('NestedType nested_member')
            
            assert struct_pos < nested_member_pos, \
                "struct definition should come before member that uses it"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
