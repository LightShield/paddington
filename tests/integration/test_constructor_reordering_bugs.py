"""Test for constructor initializer list reordering bugs."""

import pytest
import tempfile
from pathlib import Path
import subprocess


@pytest.mark.integration
def test_constructor_initializer_list_preserves_commas():
    """Test that reordering constructor initializer lists preserves commas."""
    tmp = Path(tempfile.mkdtemp())
    
    header = tmp / "test.h"
    header.write_text("""
struct Test {
    char small;
    int exp_len;
    int len;
    int queue_id;
    
    Test();  // Constructor in .cpp
};
""")
    
    cpp = tmp / "test.cpp"
    cpp.write_text("""#include "test.h"
Test::Test() : exp_len(0), len(0), queue_id(-1) {}
Test t;
""")
    
    obj = tmp / "test.o"
    result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj), f'-I{tmp}'], 
                           capture_output=True)
    assert result.returncode == 0, f"Initial compilation failed: {result.stderr.decode()}"
    
    # Run paddington
    result = subprocess.run(
        ['python3', '__main__.py', str(obj), '--extractor', 'pahole',
         '--source-root', str(tmp), '--apply', '--output', 'file'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0, f"Paddington failed: {result.stderr}"
    
    # Read modified cpp
    modified_cpp = cpp.read_text()
    
    # Check constructor syntax is valid
    assert 'Test::Test()' in modified_cpp, "Constructor declaration missing"
    
    # Try to compile
    result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', tmp / 'test2.o', f'-I{tmp}'], 
                           capture_output=True)
    
    assert result.returncode == 0, \
        f"Modified file doesn't compile! Constructor initializer list broken.\n" \
        f"Error: {result.stderr.decode()}\n" \
        f"Modified .cpp:\n{modified_cpp}\n" \
        f"Modified .h:\n{header.read_text()}"


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])



@pytest.mark.integration
def test_typedef_stays_before_members_using_it():
    """Test that typedef stays before members that use it."""
    tmp = Path(tempfile.mkdtemp())
    
    header = tmp / "test.h"
    header.write_text("""
struct Test {
    using MyType = int;
    char small;
    MyType value;
    int other;
};
""")
    
    cpp = tmp / "test.cpp"
    cpp.write_text('#include "test.h"\nTest t;')
    
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
    
    # Read modified file
    modified = header.read_text()
    
    # Verify typedef comes before value
    typedef_pos = modified.find('using MyType')
    value_pos = modified.find('MyType value')
    
    assert typedef_pos > 0 and value_pos > 0, "typedef or value not found"
    assert typedef_pos < value_pos, \
        f"typedef (pos {typedef_pos}) must come before MyType value (pos {value_pos})"
    
    # Try to compile
    result = subprocess.run(['g++', '-g', '-c', str(cpp), '-o', tmp / 'test2.o', f'-I{tmp}'], 
                           capture_output=True)
    
    assert result.returncode == 0, \
        f"Modified file doesn't compile! Typedef dependency broken.\n" \
        f"Error: {result.stderr.decode()}\n" \
        f"Modified content:\n{modified}"



@pytest.mark.integration
def test_constructor_initializer_order_matches_member_order():
    """Test that constructor initializer list order matches reordered member order."""
    tmp = Path(tempfile.mkdtemp())
    
    header = tmp / "test.h"
    header.write_text("""
struct Test {
    bool flag;           // Will be moved
    int* ptr;            // Large member
    
    Test();
};
""")
    
    cpp = tmp / "test.cpp"
    cpp.write_text("""#include "test.h"
Test::Test() : flag(false), ptr(nullptr) {}
Test t;
""")
    
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
    
    # Read modified files
    modified_h = header.read_text()
    modified_cpp = cpp.read_text()
    
    # Try to compile with -Werror=reorder (treat reorder warning as error)
    result = subprocess.run(['g++', '-g', '-Werror=reorder', '-c', str(cpp), '-o', tmp / 'test2.o', f'-I{tmp}'], 
                           capture_output=True)
    
    assert result.returncode == 0, \
        f"Modified file has constructor reorder warning!\n" \
        f"Members were reordered but constructor initializer list wasn't updated.\n" \
        f"Error: {result.stderr.decode()}\n" \
        f"Modified .h:\n{modified_h}\n" \
        f"Modified .cpp:\n{modified_cpp}"
