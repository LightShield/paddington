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
    input_files, expected_files = get_test_files(test_case)
    
    assert input_files, f"No input files in {test_case.name}"
    assert expected_files, f"No expected files in {test_case.name}"
    assert len(input_files) == len(expected_files), \
        f"Mismatch: {len(input_files)} input files, {len(expected_files)} expected files"
    
    # TODO: Run paddington optimize on input_files
    # TODO: Compare output with expected_files
    pytest.skip("Implementation pending")

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
    
    # TODO: Run paddington analyze on test_file
    # TODO: Verify it reports 10 bytes padding for UserData
    pytest.skip("Implementation pending")

def test_ignore_annotation_respected():
    """Test that paddington-ignore annotation is respected."""
    test_file = TEST_CASES_DIR / "ignore_annotation" / "input.cpp"
    
    # TODO: Run paddington optimize on test_file
    # TODO: Verify IgnoreMe struct is unchanged
    # TODO: Verify OptimizeMe struct is optimized
    pytest.skip("Implementation pending")

def test_nested_struct_bottom_up():
    """Test that nested structs are optimized bottom-up."""
    test_file = TEST_CASES_DIR / "nested_struct" / "input.cpp"
    
    # TODO: Run paddington optimize on test_file
    # TODO: Verify Inner is optimized before Outer
    # TODO: Verify both structs are optimized
    pytest.skip("Implementation pending")

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
