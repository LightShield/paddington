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
        
        # Should return empty list because template with constructor should be skipped
        assert len(results) == 0, "Template with constructor should be skipped even if declared after 1000 chars"
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
        
        # Should return empty list because template with constructor should be skipped
        assert len(results) == 0, "Template with constructor should be skipped"
    finally:
        Path(temp_path).unlink()
