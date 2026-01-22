"""Test for inline constructor initializer list reordering functionality."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestInlineConstructorReordering:
    """Test that inline constructor initializer lists are reordered to match member order.
    
    These tests verify that the SrcMLTransformer correctly reorders constructor
    initializer lists when struct/class members are reordered for optimization.
    """
    
    def test_basic_constructor_initializer_reordering(self):
        """Test basic constructor initializer list reordering."""
        original_code = """class Test {
public:
    Test() : m_a(1), m_b(0) {}
private:
    int m_a;
    int m_b;
};"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(original_code)
            
            transformer = SrcMLTransformer()
            
            modification = SourceModification(
                struct_name="Test",
                file_path=str(test_file),
                modifications=(
                    Modification(
                        type="reorder",
                        location=Location(file=str(test_file), line=1, column=1),
                        old_content="",
                        new_content="members: m_b, m_a"
                    ),
                )
            )
            
            results = transformer.transform([modification])
            
            assert results is not None and len(results) > 0
            result_content = results[0].new_content
            
            # Verify initializer is reordered to match new member order
            assert "Test() : m_b(0), m_a(1)" in result_content
    
    def test_multiple_constructors_reordering(self):
        """Test that all constructors get their initializer lists reordered."""
        original_code = """class Test {
public:
    Test() : m_a(1), m_b(0) {}
    Test(int x) : m_a(x), m_b(x+1) {}
    Test(int x, int y) : m_a(x), m_b(y) {}
private:
    int m_a;
    int m_b;
};"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(original_code)
            
            transformer = SrcMLTransformer()
            
            modification = SourceModification(
                struct_name="Test",
                file_path=str(test_file),
                modifications=(
                    Modification(
                        type="reorder",
                        location=Location(file=str(test_file), line=1, column=1),
                        old_content="",
                        new_content="members: m_b, m_a"
                    ),
                )
            )
            
            results = transformer.transform([modification])
            
            assert results is not None and len(results) > 0
            result_content = results[0].new_content
            
            # All constructors should have reordered initializer lists
            assert "Test() : m_b(0), m_a(1)" in result_content
            assert "Test(int x) : m_b(x+1), m_a(x)" in result_content  
            assert "Test(int x, int y) : m_b(y), m_a(x)" in result_content
    
    def test_constructor_with_dependencies_skipped(self):
        """Test that constructors with member dependencies are not reordered."""
        # m_b depends on m_a, so reordering should be skipped
        original_code = """class Test {
public:
    Test() : m_a(1), m_b(m_a + 1) {}
private:
    int m_a;
    int m_b;
};"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(original_code)
            
            transformer = SrcMLTransformer()
            
            modification = SourceModification(
                struct_name="Test",
                file_path=str(test_file),
                modifications=(
                    Modification(
                        type="reorder",
                        location=Location(file=str(test_file), line=1, column=1),
                        old_content="",
                        new_content="members: m_b, m_a"
                    ),
                )
            )
            
            results = transformer.transform([modification])
            
            # Transformation should be skipped due to constructor dependencies
            assert results is None or len(results) == 0
    
    def test_complex_initializers_handled_correctly(self):
        """Test that complex initializers (function calls, expressions) are handled."""
        original_code = """class Test {
public:
    Test() : m_a(getValue()), m_b(0) {}
    Test(int x) : m_a(x), m_b(x * 2) {}
    
    static int getValue() { return 42; }
private:
    int m_a;
    int m_b;
};"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.h"
            test_file.write_text(original_code)
            
            transformer = SrcMLTransformer()
            
            modification = SourceModification(
                struct_name="Test",
                file_path=str(test_file),
                modifications=(
                    Modification(
                        type="reorder",
                        location=Location(file=str(test_file), line=1, column=1),
                        old_content="",
                        new_content="members: m_b, m_a"
                    ),
                )
            )
            
            results = transformer.transform([modification])
            
            assert results is not None and len(results) > 0
            result_content = results[0].new_content
            
            # Complex initializers should be correctly reordered
            assert "Test() : m_b(0), m_a(getValue())" in result_content
            assert "Test(int x) : m_b(x * 2), m_a(x)" in result_content