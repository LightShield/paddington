"""Test for access modifier corruption bug from RBA.h."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestAccessModifierCorruption:
    """Test for the specific bug found in RBA.h transformation."""
    
    def test_rba_structure_preserved(self):
        """Test that RBA.h-like structure is preserved during reordering.
        
        Bug: When members at the end of protected section (right before public:)
        are moved up, the public: keyword gets corrupted or moved.
        
        Structure:
        protected:
            member1;
            member2;
            nested_struct { };
            comment
            member3;  // Last protected member
            member4;  // Also protected
        public:
            method();
        
        After reordering to put member3, member4 first, the public: keyword
        should stay in the same place, not move with the members.
        """
        test_code = """class RegBundle {
protected:
    int bundle_arrays;
    int regs;
    std::string regBundle_name;
    
    typedef struct {
        int value;
    } nested_t;
    
    // Comment about these members
    std::map<string, int> lockport2regs;
    std::map<string, int> tc_array_vec;

public:
    RegBundle();
    void method();
};
"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(test_code)
            
            # Reorder to put maps first (they're larger)
            mod = SourceModification(
                file_path=str(test_file),
                struct_name="RegBundle",
                modifications=(
                    Modification(
                        type='reorder',
                        location=Location(file=str(test_file), line=1, column=0),
                        old_content="members: bundle_arrays, regs, regBundle_name, lockport2regs, tc_array_vec",
                        new_content="members: lockport2regs, tc_array_vec, regBundle_name, bundle_arrays, regs",
                        access_strategy='preserve'
                    ),
                ),
                access_strategy='preserve'
            )
            
            transformer = SrcMLTransformer()
            transformed = transformer.transform([mod])
            
            assert len(transformed) > 0, "Transformation failed"
            
            new_content = transformed[0].new_content
            
            # Verify public: keyword is still present and in correct position
            assert 'public:' in new_content, "public: keyword missing!"
            
            # Find positions
            protected_pos = new_content.index('protected:')
            public_pos = new_content.index('public:')
            
            # All members should be in protected section
            protected_section = new_content[protected_pos:public_pos]
            assert 'lockport2regs' in protected_section
            assert 'tc_array_vec' in protected_section
            assert 'regBundle_name' in protected_section
            
            # Methods should be in public section
            public_section = new_content[public_pos:]
            assert 'RegBundle()' in public_section
            assert 'void method()' in public_section
            
            # CRITICAL: No member variables should leak into public section
            # This is the bug - members appear after public: keyword
            assert 'lockport2regs' not in public_section, \
                "BUG: lockport2regs leaked into public section!"
            assert 'tc_array_vec' not in public_section, \
                "BUG: tc_array_vec leaked into public section!"
            
            # Verify public: is not duplicated or misplaced
            assert new_content.count('public:') == 1, \
                "public: keyword should appear exactly once"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
