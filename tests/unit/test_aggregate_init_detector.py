"""Test for detecting aggregate initialization usage."""

import pytest
import tempfile
from pathlib import Path

from implementation.padding_analysis.aggregate_init_detector import has_aggregate_initialization


@pytest.mark.unit
class TestAggregateInitDetector:
    """Test detection of aggregate initialization."""
    
    def test_detect_brace_initialization(self):
        """Test detection of brace initialization."""
        code = """
struct Data {
    int a;
    int b;
};

void func() {
    Data d{1, 2};  // Aggregate initialization
}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file = Path(tmpdir) / "test.cpp"
            file.write_text(code)
            
            assert has_aggregate_initialization(str(file), "Data")
    
    def test_no_aggregate_init(self):
        """Test struct without aggregate initialization."""
        code = """
struct Data {
    int a;
    int b;
    Data(int x, int y) : a(x), b(y) {}
};

void func() {
    Data d(1, 2);  // Constructor call, not aggregate
}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file = Path(tmpdir) / "test.cpp"
            file.write_text(code)
            
            assert not has_aggregate_initialization(str(file), "Data")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
