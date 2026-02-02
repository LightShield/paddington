"""Test that template detection works for templates declared beyond first 1000 chars."""
import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
def test_template_detection_beyond_1000_chars():
    """Template declared after 1000 chars should still be detected and skipped."""
    
    # Create a file with lots of comments/includes before template
    header = "// " + "x" * 50 + "\n"
    padding = header * 25  # ~1300 chars of comments
    
    source = padding + """
template<typename T>
class MyStruct {
public:
    int a;
    int b;
    
    MyStruct() : a(0), b(0) {}
};
"""
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.h', delete=False) as f:
        f.write(source)
        temp_path = f.name
    
    try:
        mod = SourceModification(
            file_path=temp_path,
            struct_name="MyStruct",
            modifications=[
                Modification(
                    type="reorder",
                    old_content="",
                    new_content="members: b, a",
                    location=Location(file=temp_path, line=1, column=0)
                )
            ]
        )
        
        transformer = SrcMLTransformer()
        results = transformer.transform([mod])
        
        # With constructor support enabled, simple constructors are now reordered
        assert len(results) == 1, "Template with simple constructor should be optimized"
        assert "a;" in results[0].new_content
        assert results[0].new_content.index("b;") < results[0].new_content.index("a;")
    finally:
        Path(temp_path).unlink()


@pytest.mark.unit
def test_template_detection_in_first_1000_chars():
    """Template declared in first 1000 chars should be detected."""
    
    source = """
template<typename T>
class MyStruct {
public:
    int a;
    int b;
    
    MyStruct() : a(0), b(0) {}
};
"""
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.h', delete=False) as f:
        f.write(source)
        temp_path = f.name
    
    try:
        mod = SourceModification(
            file_path=temp_path,
            struct_name="MyStruct",
            modifications=[
                Modification(
                    type="reorder",
                    old_content="",
                    new_content="members: b, a",
                    location=Location(file=temp_path, line=1, column=0)
                )
            ]
        )
        
        transformer = SrcMLTransformer()
        results = transformer.transform([mod])
        
        # With constructor support enabled, simple constructors are now reordered
        assert len(results) == 1, "Template with simple constructor should be optimized"
    finally:
        Path(temp_path).unlink()
