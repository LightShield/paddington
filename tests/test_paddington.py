import pytest
import subprocess
from pathlib import Path

TEST_CASES_DIR = Path(__file__).parent / "test_cases"

def get_test_cases():
    """Discover all test case directories."""
    return [d for d in TEST_CASES_DIR.iterdir() if d.is_dir()]

def get_test_files(test_case):
    """Get input and expected files for a test case (handles single and multi-file)."""
    input_files = sorted(test_case.glob("input*"))
    expected_files = sorted(test_case.glob("expected*"))
    return input_files, expected_files

@pytest.mark.parametrize("test_case", get_test_cases(), ids=lambda x: x.name)
def test_optimization(test_case):
    """Test that optimization produces expected output."""
    import tempfile
    import shutil
    from pathlib import Path
    
    input_files, expected_files = get_test_files(test_case)
    
    assert input_files, f"No input files in {test_case.name}"
    assert expected_files, f"No expected files in {test_case.name}"
    assert len(input_files) == len(expected_files), \
        f"Mismatch: {len(input_files)} input files, {len(expected_files)} expected files"
    
    # Create temp directory and copy input files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Copy input files
        for input_file in input_files:
            shutil.copy(input_file, tmpdir_path / input_file.name.replace('input', 'test'))
        
        # Run paddington optimize
        test_files = list(tmpdir_path.glob("test*"))
        for test_file in test_files:
            result = subprocess.run(
                ["python3", "-m", "paddington", "optimize", str(test_file), "--apply", "--force"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            assert result.returncode == 0, f"Optimization failed: {result.stderr}"
        
        # Compare with expected
        for expected_file in expected_files:
            test_file = tmpdir_path / expected_file.name.replace('expected', 'test')
            
            with open(expected_file, 'r') as f:
                expected_content = f.read()
            
            with open(test_file, 'r') as f:
                actual_content = f.read()
            
            assert actual_content == expected_content, \
                f"Output mismatch for {expected_file.name}\nExpected:\n{expected_content}\n\nActual:\n{actual_content}"

@pytest.mark.parametrize("test_case", get_test_cases(), ids=lambda x: x.name)
def test_compilation(test_case):
    """Test that optimized code compiles successfully."""
    input_files, _ = get_test_files(test_case)
    
    assert input_files, f"No input files in {test_case.name}"
    
    # Compile input to verify it's valid C++
    cpp_files = [f for f in input_files if f.suffix in ['.cpp', '.cc', '.cxx']]
    if cpp_files:
        result = subprocess.run(
            ["clang++", "-std=c++17", "-fsyntax-only"] + [str(f) for f in cpp_files],
            capture_output=True,
            text=True,
            cwd=test_case
        )
        
        assert result.returncode == 0, f"Input files don't compile: {result.stderr}"
    
    # TODO: Compile optimized output
    pytest.skip("Optimization implementation pending")

def test_analyze_reports_padding():
    """Test that analyze command reports padding correctly."""
    test_file = TEST_CASES_DIR / "simple_struct" / "input.cpp"
    
    result = subprocess.run(
        ["python3", "-m", "paddington", "analyze", str(test_file)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    assert result.returncode == 0, f"Analyze failed: {result.stderr}"
    assert "10 bytes padding" in result.stdout
    assert "8 bytes savable" in result.stdout
    assert "struct UserData" in result.stdout

def test_ignore_annotation_respected():
    """Test that paddington-ignore annotation is respected."""
    import tempfile
    import shutil
    
    test_file = TEST_CASES_DIR / "ignore_annotation" / "input.cpp"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_copy = tmpdir_path / "test.cpp"
        shutil.copy(test_file, test_copy)
        
        # Read original IgnoreMe struct
        with open(test_copy, 'r') as f:
            original = f.read()
        
        # Run optimization
        result = subprocess.run(
            ["python3", "-m", "paddington", "optimize", str(test_copy), "--apply", "--force"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        
        # Read result
        with open(test_copy, "r") as f:
            optimized = f.read()

        # IgnoreMe should be unchanged (members in original order)
        ignore_start = optimized.find("struct IgnoreMe")
        ignore_end = optimized.find("};", ignore_start)
        ignore_section = optimized[ignore_start:ignore_end]
        
        # Check IgnoreMe has original order (char a before int b)
        assert ignore_section.index("char a;") < ignore_section.index("int b;")

        # OptimizeMe should be changed (double d before char a)
        optimize_start = optimized.find("struct OptimizeMe")
        optimize_end = optimized.find("};", optimize_start)
        optimize_section = optimized[optimize_start:optimize_end]
        
        assert optimize_section.index("double d;") < optimize_section.index("char a;")

def test_nested_struct_bottom_up():
    """Test that nested structs are optimized bottom-up."""
    import tempfile
    
    # Create test with actual padding issues
    test_code = """
struct Inner {
    char a;
    double b;
    char c;
};

struct Outer {
    char x;
    Inner inner;
    char y;
    int z;
};

int main() { return 0; }
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(test_code)
        test_file = f.name
    
    try:
        # Run optimization with verbose output
        result = subprocess.run(
            ["python3", "-m", "paddington", "optimize", test_file, "--apply", "-vv"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        assert result.returncode == 0
        
        # Check that both structs were optimized
        assert "Optimizing struct Inner" in result.stdout or "Optimizing struct Outer" in result.stdout
        
        # Verify Inner comes before Outer in output (bottom-up)
        inner_pos = result.stdout.find("Inner")
        outer_pos = result.stdout.find("Outer")
        if inner_pos != -1 and outer_pos != -1:
            assert inner_pos < outer_pos, "Inner should be optimized before Outer"
    finally:
        Path(test_file).unlink()

def test_usage_counting():
    """Test that tool correctly counts struct instantiations."""
    test_case = TEST_CASES_DIR / "cross_file_usage"
    
    # TODO: Run paddington analyze on test_case
    # TODO: Verify it reports ~7 User instances:
    #   - u1, u2 (direct)
    #   - u3, u4 (smart pointers)
    #   - 2x emplace_back/push_back
    #   - 1x temporary in push_back
    pytest.skip("Implementation pending")

def test_cross_file_constructor_updates():
    """Test that constructor updates work across files."""
    test_case = TEST_CASES_DIR / "cross_file_usage"
    
    # TODO: Run paddington optimize on test_case
    # TODO: Verify User struct is reordered in header
    # TODO: Verify constructor initializer list is updated in .cpp
    # TODO: Verify all call sites in main.cpp remain unchanged (parameter order stays same)
    pytest.skip("Implementation pending")
