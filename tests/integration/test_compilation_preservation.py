"""Test that verifies paddington doesn't break compilation with static const dependencies."""

import pytest
import tempfile
from pathlib import Path
import subprocess


@pytest.mark.integration
def test_static_const_dependency_preserves_compilation():
    """Test that reordering preserves static const dependencies and file still compiles."""
    tmp = Path(tempfile.mkdtemp())
    
    header = tmp / "test.h"
    header.write_text("""
template<typename T>
class Test {
public:
    static const int NUM = 32;
    T* ptr1;
    T* ptr2;
    char small;  // Optimizer wants to move this to end
    char array[NUM];  // Uses NUM - must stay after NUM definition
};
""")
    
    cpp = tmp / "test.cpp"
    cpp.write_text('#include "test.h"\nTest<int> t;')
    
    obj = tmp / "test.o"
    result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj), f'-I{tmp}'], 
                           capture_output=True)
    assert result.returncode == 0, "Initial compilation failed"
    
    # Run paddington with --apply to actually modify files
    result = subprocess.run(
        ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
         '--source-root', str(tmp), '--apply', '--output', 'file'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0, f"Paddington failed: {result.stderr}"
    
    # Try to compile the modified file
    result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', tmp / 'test2.o', f'-I{tmp}'], 
                           capture_output=True)
    
    # This is the critical assertion - modified file MUST still compile
    assert result.returncode == 0, \
        f"Modified file doesn't compile! Paddington broke static const dependency.\n" \
        f"Error: {result.stderr.decode()}\n" \
        f"Modified content:\n{header.read_text()}"


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])



@pytest.mark.integration
def test_template_with_static_const_preserves_compilation():
    """Test that template classes with static const don't break compilation."""
    tmp = Path(tempfile.mkdtemp())
    
    header = tmp / "test.h"
    header.write_text("""
template<typename T>
class Test {
public:
    static const int NUM = 32;
    T* ptr1;
    T* ptr2;
    char small;
    char array[NUM];
};
""")
    
    cpp = tmp / "test.cpp"
    cpp.write_text('#include "test.h"\nTest<int> t;')
    
    obj = tmp / "test.o"
    result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj), f'-I{tmp}'], 
                           capture_output=True)
    assert result.returncode == 0, "Initial compilation failed"
    
    # Run paddington
    result = subprocess.run(
        ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
         '--source-root', str(tmp), '--apply', '--output', 'file'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0, f"Paddington failed: {result.stderr}"
    
    # Verify NUM is still in the file
    modified = header.read_text()
    assert 'NUM = 32' in modified, "Static const NUM was removed from template!"
    
    # Verify NUM comes before array
    num_pos = modified.find('NUM = 32')
    array_pos = modified.find('array[NUM]')
    if num_pos > 0 and array_pos > 0:
        assert num_pos < array_pos, \
            f"NUM must come before array[NUM]! NUM at {num_pos}, array at {array_pos}"
    
    # Try to compile the modified file
    result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', tmp / 'test2.o', f'-I{tmp}'], 
                           capture_output=True)
    
    assert result.returncode == 0, \
        f"Modified template doesn't compile!\n" \
        f"Error: {result.stderr.decode()}\n" \
        f"Modified content:\n{modified}"
