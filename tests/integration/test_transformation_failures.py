"""Tests for transformation failure cases.

Goal: Identify and fix the 864 transformation failures (16% failure rate).
"""

import pytest
import tempfile
from pathlib import Path
import subprocess


class TestTransformationFailures:
    
    @pytest.mark.integration
    def test_template_instantiation_finds_definition(self):
        """Test that Foo<int> finds template<typename T> struct Foo."""
        tmp = Path(tempfile.mkdtemp())
        
        cpp = tmp / "test.cpp"
        cpp.write_text("""
template<typename T>
struct Foo {
    char a;
    int b;
};

int main() {
    Foo<int> f;
    return 0;
}
""")
        
        obj = tmp / "test.o"
        subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj)], check=True)
        
        result = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
             '--source-root', str(tmp), '--output', 'patch', '--patch-dir', str(tmp / 'patches'), '-v'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Should create a patch
        patches = list((tmp / 'patches').glob('*.patch')) if (tmp / 'patches').exists() else []
        assert len(patches) > 0, "Template instantiation should find and optimize template definition"
    
    @pytest.mark.integration
    def test_namespace_qualified_struct(self):
        """Test that namespace::Struct is handled correctly."""
        tmp = Path(tempfile.mkdtemp())
        
        cpp = tmp / "test.cpp"
        cpp.write_text("""
namespace MyNamespace {
    struct Foo {
        char a;
        int b;
        Foo() : a(0), b(0) {}  // Constructor forces inclusion
    };
}

int main() {
    MyNamespace::Foo f;
    return f.b;  // Use it
}
""")
        
        obj = tmp / "test.o"
        subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj)], check=True)
        
        result = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
             '--source-root', str(tmp), '--output', 'patch', '--patch-dir', str(tmp / 'patches'), '-v'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Should handle namespace-qualified names
        patches = list((tmp / 'patches').glob('*.patch')) if (tmp / 'patches').exists() else []
        assert len(patches) > 0, "Namespace-qualified struct should be optimized"
    
    @pytest.mark.integration
    def test_struct_in_anonymous_namespace(self):
        """Test structs in anonymous namespaces."""
        tmp = Path(tempfile.mkdtemp())
        
        cpp = tmp / "test.cpp"
        cpp.write_text("""
namespace {
    struct Foo {
        char a;
        int b;
    };
}

int main() {
    Foo f;
    return 0;
}
""")
        
        obj = tmp / "test.o"
        subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj)], check=True)
        
        result = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
             '--source-root', str(tmp), '-v'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Anonymous namespace structs might have mangled names
        # This test documents the behavior
        assert result.returncode == 0
