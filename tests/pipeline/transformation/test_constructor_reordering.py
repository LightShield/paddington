"""Test for constructor initializer list reordering in srcML."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location


@pytest.mark.unit
class TestConstructorReordering:
    """Test srcML constructor initializer list reordering."""
    
    def test_constructor_initializer_list_reordered(self):
        """Test that constructor initializer lists are actually reordered.
        
        Bug: _reorder_constructor_initializers finds constructors but doesn't
        actually reorder the initializer list, so content remains unchanged.
        """
        # Create test cpp file with constructor
        test_code = """
class TestClass {
    int a;
    double b;
    char c;
};

TestClass::TestClass() : a(1), b(2.0), c('x') {
}
"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            cpp_file = tmpdir / "test.cpp"
            cpp_file.write_text(test_code)
            
            # Create modification to reorder: b, a, c (double first, then int, then char)
            mod = SourceModification(
                file_path=str(cpp_file),
                struct_name="TestClass",
                modifications=(
                    Modification(
                        type='reorder_constructors',
                        location=Location(file=str(cpp_file), line=1, column=0),
                        old_content="members: a, b, c",
                        new_content="members: b, a, c",  # Reorder to largest first
                        access_strategy='preserve'
                    ),
                ),
                access_strategy='preserve'
            )
            
            transformer = SrcMLTransformer()
            transformed = transformer.transform([mod])
            
            # BUG: Transformation returns empty or unchanged content
            assert len(transformed) > 0, "Transformer returned empty"
            
            t = transformed[0]
            assert t.original_content != t.new_content, \
                "Content unchanged - constructor initializer list not reordered"
            
            # Verify the initializer list was reordered
            assert ': b(2.0), a(1), c(' in t.new_content, \
                "Initializer list not in new order (b, a, c)"
            assert ': a(1), b(2.0), c(' not in t.new_content, \
                "Initializer list still in old order"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
