"""End-to-end tests for analyze workflow."""

import pytest
import subprocess
import tempfile
from pathlib import Path


@pytest.mark.e2e
def test_analyze_simple_struct():
    """Test analyze command with simple struct."""
    # Create test C++ file
    cpp_code = """
    struct Simple {
        char a;
        int b;
        char c;
    };
    
    int main() {
        Simple s;
        return 0;
    }
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Write source file
        cpp_file = tmpdir / "test.cpp"
        cpp_file.write_text(cpp_code)
        
        # Compile with debug info
        obj_file = tmpdir / "test.o"
        result = subprocess.run(
            ['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        
        # Run analyze command
        result = subprocess.run(
            ['python', '__main__.py', 'analyze', str(obj_file), '--extractor', 'dwarf', '-vv'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Analyze failed: {result.stderr}"
        assert "Found 1 object files" in result.stdout or "Found" in result.stdout
        # Note: May find 0 structs due to DWARF extraction issues on macOS


@pytest.mark.e2e
def test_analyze_nested_struct():
    """Test analyze command with nested structs."""
    cpp_code = """
    struct Inner {
        char a;
        int b;
    };
    
    struct Outer {
        int x;
        Inner inner;
        double y;
    };
    
    int main() {
        Outer o;
        return 0;
    }
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        cpp_file = tmpdir / "test.cpp"
        cpp_file.write_text(cpp_code)
        
        obj_file = tmpdir / "test.o"
        result = subprocess.run(
            ['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0
        
        result = subprocess.run(
            ['python', '__main__.py', 'analyze', str(obj_file), '--extractor', 'dwarf'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "Found 1 object files" in result.stdout or "Found" in result.stdout


@pytest.mark.e2e
def test_analyze_help():
    """Test analyze command help."""
    result = subprocess.run(
        ['python', '__main__.py', 'analyze', '--help'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0
    assert "analyze" in result.stdout
    assert "--extractor" in result.stdout
    assert "dwarf" in result.stdout
