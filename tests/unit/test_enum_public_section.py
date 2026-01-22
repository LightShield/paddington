"""Test for enum in public section being incorrectly moved."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestEnumInPublicSection:
    """Test that enums in public section are not moved to protected."""
    
    def test_public_enum_stays_public(self):
        """Test that enum in public section stays public, not moved to protected.
        
        Bug from Register.h: enum cause_t is in public section, but gets
        removed/moved when reordering protected members.
        
        Structure:
        class Test {
        public:
            enum MyEnum { A, B };  // Public enum
            Test(MyEnum e);        // Constructor uses it
        protected:
            int member;
        };
        
        When reordering protected members, the public enum should not be touched.
        """
        test_code = """class RegisterBadAccess {
public:
    enum cause_t {
        NO_READ,
        NO_WRITE
    };
    
    RegisterBadAccess(std::string name, cause_t cause);
    
protected:
    std::string m_name;
    cause_t m_cause;
};
"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(test_code)
            
            # Reorder protected members
            mod = SourceModification(
                file_path=str(test_file),
                struct_name="RegisterBadAccess",
                modifications=(
                    Modification(
                        type='reorder',
                        location=Location(file=str(test_file), line=1, column=0),
                        old_content="members: m_name, m_cause",
                        new_content="members: m_cause, m_name",
                        access_strategy='preserve'
                    ),
                ),
                access_strategy='preserve'
            )
            
            transformer = SrcMLTransformer()
            transformed = transformer.transform([mod])
            
            assert len(transformed) > 0, "Transformation should succeed"
            
            new_content = transformed[0].new_content
            
            # Verify enum is still in public section
            assert 'enum cause_t' in new_content, "enum should still exist"
            
            public_pos = new_content.find('public:')
            protected_pos = new_content.find('protected:')
            enum_pos = new_content.find('enum cause_t')
            
            # Enum should be in public section (between public: and protected:)
            assert public_pos < enum_pos < protected_pos, \
                f"BUG: enum at {enum_pos} should be between public ({public_pos}) and protected ({protected_pos})"
            
            # Constructor should still be in public and use the enum
            constructor_pos = new_content.find('RegisterBadAccess(')
            assert public_pos < constructor_pos < protected_pos, \
                "Constructor should be in public section"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
