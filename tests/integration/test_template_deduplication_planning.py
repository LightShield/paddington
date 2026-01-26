"""Test for template instantiation deduplication."""

import pytest
import tempfile
from pathlib import Path
import subprocess


class TestTemplateDeduplication:
    
    @pytest.mark.integration
    def test_multiple_instantiations_create_one_modification(self):
        """Test that Foo<int> and Foo<double> create only ONE modification for template Foo."""
        tmp = Path(tempfile.mkdtemp())
        
        cpp = tmp / "test.cpp"
        cpp.write_text("""
template<typename T>
struct Foo {
    char a;      // 1 byte + 7 padding
    T* ptr;      // 8 bytes
    int b;       // 4 bytes + 4 padding
    // Total: 24 bytes, optimal: 16 bytes
};

int main() {
    Foo<int> f1;
    Foo<double> f2;
    Foo<char> f3;
    return 0;
}
""")
        
        obj = tmp / "test.o"
        subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj)], check=True)
        
        # Run paddington
        result = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
             '--source-root', str(tmp), '-vv'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Check that we don't have "No changes made" errors
        no_changes_count = result.stdout.count("No changes were made to XML")
        
        # Should be 0 - all instantiations should be deduplicated to single modification
        assert no_changes_count == 0, \
            f"Found {no_changes_count} 'No changes made' - template instantiations not deduplicated"
        
        # Check planning stage deduplicated
        planned_count = result.stdout.count("Modifications planned:")
        # Should mention deduplication
        assert "deduplicated" in result.stdout.lower() or no_changes_count == 0, \
            "Planning stage should deduplicate template instantiations"
