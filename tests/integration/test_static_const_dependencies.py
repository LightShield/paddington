"""Test for static const member dependencies."""

import pytest
import tempfile
from pathlib import Path
import subprocess


class TestStaticConstDependencies:
    
    @pytest.mark.integration
    def test_static_const_used_in_member_type(self):
        """Test that static const can't be moved after members that use it in their type."""
        tmp = Path(tempfile.mkdtemp())
        
        header = tmp / "test.h"
        header.write_text("""
struct Test {
    static const int SIZE = 32;
    char small;      // 1 byte - would be moved to end for optimization
    int other;       // 4 bytes
    char array[SIZE];  // Uses SIZE in type - must come after SIZE
    // Optimal would be: SIZE, other, array, small
    // But we can't move array before SIZE!
};
""")
        
        cpp = tmp / "test.cpp"
        cpp.write_text('#include "test.h"\nTest t;')
        
        obj = tmp / "test.o"
        result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj), f'-I{tmp}'], 
                               capture_output=True)
        
        if result.returncode != 0:
            pytest.skip("Compilation failed")
        
        # Run paddington with --apply to actually modify the file
        result = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
             '--source-root', str(tmp), '--apply', '--output', 'file'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Paddington failed: {result.stderr}"
        
        # Read modified file
        modified_content = header.read_text()
        
        # Verify SIZE is still before array
        size_pos = modified_content.find('SIZE = 32')
        array_pos = modified_content.find('array[SIZE]')
        
        assert size_pos > 0 and array_pos > 0, "SIZE or array not found in modified file"
        assert size_pos < array_pos, \
            f"SIZE (pos {size_pos}) must come before array[SIZE] (pos {array_pos}) - static const dependency violated!"
        
        # Try to compile the modified file
        result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', tmp / 'test2.o', f'-I{tmp}'], 
                               capture_output=True)
        
        assert result.returncode == 0, \
            f"Modified file doesn't compile! Error: {result.stderr.decode()}"
    
    @pytest.mark.integration
    def test_static_const_in_template_parameter(self):
        """Test that static const can't be moved after members using it in template params."""
        tmp = Path(tempfile.mkdtemp())
        
        header = tmp / "test.h"
        header.write_text("""
template<int N>
struct Array {
    char data[N];
};

struct Test {
    static const int NUM = 32;
    Array<NUM> buffer;  // Uses NUM in template parameter
    int other;
};
""")
        
        cpp = tmp / "test.cpp"
        cpp.write_text('#include "test.h"\nTest t;')
        
        obj = tmp / "test.o"
        result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj), f'-I{tmp}'], 
                               capture_output=True)
        
        if result.returncode != 0:
            pytest.skip("Compilation failed")
        
        # Run paddington
        result = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
             '--source-root', str(tmp), '--apply', '--output', 'file'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Read modified file
        modified_content = header.read_text()
        
        # Verify NUM is still before buffer
        num_pos = modified_content.find('NUM = 32')
        buffer_pos = modified_content.find('Array<NUM>')
        
        assert num_pos < buffer_pos, \
            "NUM must come before Array<NUM> - template parameter dependency violated!"
