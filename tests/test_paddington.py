import pytest
import subprocess
from pathlib import Path

TEST_CASES_DIR = Path(__file__).parent / "test_cases"

def get_test_cases():
    """Discover all test case directories."""
    return [d for d in TEST_CASES_DIR.iterdir() if d.is_dir()]

@pytest.mark.parametrize("test_case", get_test_cases(), ids=lambda x: x.name)
def test_optimization(test_case):
    """Test that optimization produces expected output."""
    input_file = test_case / "input.cpp"
    expected_file = test_case / "expected.cpp"
    
    assert input_file.exists(), f"Missing input.cpp in {test_case.name}"
    assert expected_file.exists(), f"Missing expected.cpp in {test_case.name}"
    
    # TODO: Run paddington optimize on input_file
    # TODO: Compare output with expected_file
    pytest.skip("Implementation pending")

@pytest.mark.parametrize("test_case", get_test_cases(), ids=lambda x: x.name)
def test_compilation(test_case):
    """Test that optimized code compiles successfully."""
    input_file = test_case / "input.cpp"
    
    assert input_file.exists(), f"Missing input.cpp in {test_case.name}"
    
    # Compile input to verify it's valid C++
    result = subprocess.run(
        ["clang++", "-std=c++17", "-fsyntax-only", str(input_file)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Input file doesn't compile: {result.stderr}"
    
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
