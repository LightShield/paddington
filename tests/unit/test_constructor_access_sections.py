"""Test constructor reordering across access sections."""

import pytest
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data import SourceModification, Modification, Location


class TestConstructorAccessSections:
    """Test that constructor initializers respect member order across access sections."""
    
    def test_constructor_reorder_across_public_private(self, tmp_path):
        """Test reordering when members span public and private sections."""
        # Create test file with members in public and private sections
        test_file = tmp_path / "test.h"
        test_file.write_text("""
class TestClass {
public:
    int m_a;
    int m_b;
    
    TestClass() : m_a(0), m_c(0), m_d(0), m_b(0) {}
    
private:
    int m_c;
    int m_d;
};
""")
        
        # Create modification to reorder: m_b, m_a, m_d, m_c
        # This should update constructor to: m_b(0), m_a(0), m_d(0), m_c(0)
        modification = SourceModification(
            file_path=str(test_file),
            struct_name="TestClass",
            modifications=(
                Modification(
                    type="reorder",
                    location=Location(file=str(test_file), line=2, column=0),
                    old_content="members: m_a, m_b, m_c, m_d",
                    new_content="members: m_b, m_a, m_d, m_c",
                ),
            ),
        )
        
        transformer = SrcMLTransformer()
        results = transformer.transform([modification])
        
        assert len(results) == 1
        result = results[0]
        
        # Verify constructor initializer list is reordered correctly
        assert "m_b(0), m_a(0), m_d(0), m_c(0)" in result.new_content
        # Verify members are reordered
        assert result.new_content.index("m_b;") < result.new_content.index("m_a;")
        assert result.new_content.index("m_d;") < result.new_content.index("m_c;")
    
    def test_constructor_reorder_partial_optimization(self, tmp_path):
        """Test when only some members are optimized, but constructor references all."""
        # This simulates the real-world case where paddington only optimizes
        # a subset of members, but the constructor initializes all members
        test_file = tmp_path / "test.h"
        test_file.write_text("""
class TestClass {
public:
    int m_a;
    int m_b;
    bool m_flag;
    
    TestClass() : m_a(0), m_b(0), m_c(0), m_d(0), m_flag(false) {}
    
private:
    int m_c;
    int m_d;
};
""")
        
        # Only reorder m_a and m_b (m_flag, m_c, m_d not in new_order)
        # Constructor should still respect full declaration order: m_b, m_a, m_flag, m_c, m_d
        modification = SourceModification(
            file_path=str(test_file),
            struct_name="TestClass",
            modifications=(
                Modification(
                    type="reorder",
                    location=Location(file=str(test_file), line=2, column=0),
                    old_content="members: m_a, m_b",
                    new_content="members: m_b, m_a",
                ),
            ),
        )
        
        transformer = SrcMLTransformer()
        results = transformer.transform([modification])
        
        assert len(results) == 1
        result = results[0]
        
        # Constructor should be: m_b(0), m_a(0), m_flag(false), m_c(0), m_d(0)
        # NOT: m_b(0), m_a(0), m_c(0), m_d(0), m_flag(false)
        content = result.new_content
        
        # Find positions in constructor initializer list
        ctor_start = content.index("TestClass() :")
        ctor_end = content.index("{}", ctor_start)
        ctor_init = content[ctor_start:ctor_end]
        
        # Verify order
        assert ctor_init.index("m_b(0)") < ctor_init.index("m_a(0)")
        assert ctor_init.index("m_a(0)") < ctor_init.index("m_flag(false)")
        assert ctor_init.index("m_flag(false)") < ctor_init.index("m_c(0)")
        assert ctor_init.index("m_c(0)") < ctor_init.index("m_d(0)")
