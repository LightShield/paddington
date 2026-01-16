"""End-to-end tests for optimize workflow."""

import pytest
import subprocess
import tempfile
from pathlib import Path


@pytest.mark.e2e
def test_optimize_dry_run():
    """Test optimize command in dry-run mode."""
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
        
        cpp_file = tmpdir / "test.cpp"
        cpp_file.write_text(cpp_code)
        
        obj_file = tmpdir / "test.o"
        result = subprocess.run(
            ['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0
        
        # Run optimize (dry-run by default)
        result = subprocess.run(
            ['python', '__main__.py', 'optimize', str(obj_file), 
             '--extractor', 'dwarf',
             '--transformer', 'line-swap',
             '--output', 'patch',
             '-vv'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Optimize failed: {result.stderr}"
        assert "Found 1 object files" in result.stdout or "Found" in result.stdout


@pytest.mark.e2e
def test_optimize_with_patch_output():
    """Test optimize command generating patches."""
    cpp_code = """
    struct Data {
        char flag;
        int id;
        double score;
    };
    
    int main() { return 0; }
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        cpp_file = tmpdir / "test.cpp"
        cpp_file.write_text(cpp_code)
        
        obj_file = tmpdir / "test.o"
        subprocess.run(['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)])
        
        patch_dir = tmpdir / "patches"
        
        result = subprocess.run(
            ['python', '__main__.py', 'optimize', str(obj_file),
             '--extractor', 'dwarf',
             '--transformer', 'line-swap',
             '--output', 'patch',
             '--patch-dir', str(patch_dir)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0


@pytest.mark.e2e
def test_optimize_access_modifier_strategies():
    """Test optimize with different access modifier strategies."""
    cpp_code = """
    class Data {
    public:
        char a;
        int b;
    private:
        char c;
        double d;
    };
    
    int main() { return 0; }
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        cpp_file = tmpdir / "test.cpp"
        cpp_file.write_text(cpp_code)
        
        obj_file = tmpdir / "test.o"
        subprocess.run(['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)])
        
        # Test each strategy
        for strategy in ['preserve', 'split', 'ignore']:
            result = subprocess.run(
                ['python', '__main__.py', 'optimize', str(obj_file),
                 '--access-modifier-strategy', strategy,
                 '--extractor', 'dwarf'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            assert result.returncode == 0, f"Strategy {strategy} failed: {result.stderr}"


@pytest.mark.e2e
def test_optimize_help():
    """Test optimize command help."""
    result = subprocess.run(
        ['python', '__main__.py', 'optimize', '--help'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    assert result.returncode == 0
    assert "optimize" in result.stdout
    assert "--access-modifier-strategy" in result.stdout
    assert "preserve" in result.stdout
    assert "split" in result.stdout
    assert "ignore" in result.stdout
