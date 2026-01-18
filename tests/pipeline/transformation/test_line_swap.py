"""Tests for LineSwapTransformer."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from implementation.pipeline.transformation.line_swap import LineSwapTransformer
from implementation.struct_data import SourceModification, Modification, Location


class TestLineSwapTransformer:
    """Unit tests for LineSwapTransformer."""
    
    def test_can_handle_file(self):
        """Test file type detection."""
        transformer = LineSwapTransformer()
        
        assert transformer.can_handle_file("test.cpp")
        assert transformer.can_handle_file("test.h")
        assert transformer.can_handle_file("test.hpp")
        assert transformer.can_handle_file("test.cc")
        assert transformer.can_handle_file("test.cxx")
        assert not transformer.can_handle_file("test.py")
        assert not transformer.can_handle_file("test.txt")
    
    def test_find_struct_bounds(self):
        """Test struct boundary detection."""
        transformer = LineSwapTransformer()
        lines = [
            "// comment\n",
            "struct TestStruct {\n",
            "    int a;\n",
            "    double b;\n",
            "};\n"
        ]
        
        start, end = transformer._find_struct_bounds(lines, "TestStruct")
        assert start == 1  # Opening brace line
        assert end == 4    # Closing brace line
    
    def test_find_member_lines(self):
        """Test member line detection."""
        transformer = LineSwapTransformer()
        lines = [
            "struct Test {\n",
            "    int a;\n",
            "    double b;\n",
            "    void method();\n",  # Should be skipped
            "    char c;\n",
            "};\n"
        ]
        
        member_lines = transformer._find_member_lines(lines, 0, 5)
        expected = {"a": 1, "b": 2, "c": 4}
        assert member_lines == expected
    
    def test_find_member_lines_with_access_modifiers(self):
        """Test member detection with access modifiers."""
        transformer = LineSwapTransformer()
        lines = [
            "class Test {\n",
            "public:\n",
            "    int a;\n",
            "private:\n",
            "    double b;\n",
            "};\n"
        ]
        
        member_lines = transformer._find_member_lines(lines, 0, 5)
        expected = {"a": 2, "b": 4}
        assert member_lines == expected
    
    def test_apply_swaps(self):
        """Test line swapping logic."""
        transformer = LineSwapTransformer()
        lines = [
            "struct Test {\n",
            "    int a;\n",
            "    double b;\n",
            "    char c;\n",
            "};\n"
        ]
        
        member_lines = {"a": 1, "b": 2, "c": 3}
        new_order = ["b", "c", "a"]  # Swap order
        
        result = transformer._apply_swaps_with_access_modifiers(
            lines, member_lines, {}, new_order, "preserve", 0, len(lines)-1
        )
        
        # Check that lines were swapped correctly
        assert result[1] == "    double b;\n"  # b moved to first position
        assert result[2] == "    char c;\n"    # c moved to second position  
        assert result[3] == "    int a;\n"     # a moved to third position


class TestLineSwapTransformerIntegration:
    """Integration tests with real files."""
    
    def test_transform_simple_struct(self):
        """Test transformation of a simple struct."""
        source_content = """struct TestStruct {
    int a;
    double b;
    char c;
};"""
        
        with NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(source_content)
            f.flush()
            
            try:
                transformer = LineSwapTransformer()
                
                # Create a mock modification (simplified)
                mod = SourceModification(
                    file_path=f.name,
                    struct_name="TestStruct",
                    modifications=(
                        Modification(
                            type="reorder",
                            location=Location(f.name, 1, 0),
                            old_content="int a;\ndouble b;\nchar c;",
                            new_content="double b;\nchar c;\nint a;"
                        ),
                    )
                )
                
                results = transformer.transform([mod])
                
                # Should return one result
                assert len(results) == 1
                result = results[0]
                
                # Check that transformation occurred
                assert result.file_path == f.name
                assert result.original_content == source_content
                assert "double b;" in result.new_content
                
            finally:
                Path(f.name).unlink()
    
    def test_transform_with_methods(self):
        """Test transformation preserves methods."""
        source_content = """class TestClass {
public:
    int a;
    void method();
    double b;
    char getValue() const;
    char c;
};"""
        
        with NamedTemporaryFile(mode='w', suffix='.h', delete=False) as f:
            f.write(source_content)
            f.flush()
            
            try:
                transformer = LineSwapTransformer()
                
                # Should handle the file type
                assert transformer.can_handle_file(f.name)
                
                # Create mock modification
                mod = SourceModification(
                    file_path=f.name,
                    struct_name="TestClass", 
                    modifications=(
                        Modification(
                            type="reorder",
                            location=Location(f.name, 1, 0),
                            old_content="int a;\ndouble b;\nchar c;",
                            new_content="double b;\nchar c;\nint a;"
                        ),
                    )
                )
                
                results = transformer.transform([mod])
                
                # Should successfully transform
                assert len(results) == 1
                result = results[0]
                
                # Methods should still be present
                assert "void method();" in result.new_content
                assert "char getValue() const;" in result.new_content
                
            finally:
                Path(f.name).unlink()


if __name__ == "__main__":
    pytest.main([__file__])