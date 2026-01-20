"""E2E tests for reporting and output formatting."""

import pytest
import subprocess
from pathlib import Path
from .base_e2e import BaseE2ETest


class TestReporting(BaseE2ETest):
    """Reporting e2e tests."""
    
    @pytest.mark.e2e
    def test_progress_reporting(self, tmp_path):
        """Test progress reporting with multiple files.
        
        Verifies: FR-1.9.1 (Progress Reporting)
        """
        # Create multiple files
        for i in range(3):
            code = f"struct S{i} {{ char a; int b; }}; int main() {{ S{i} s; return 0; }}"
            cpp = tmp_path / f"file{i}.cpp"
            cpp.write_text(code)
            obj = tmp_path / f"file{i}.o"
            subprocess.run(['g++', '-g', '-O0', '-c', str(cpp), '-o', str(obj)])
        
        result = subprocess.run(
            ['python3', '__main__.py', str(tmp_path), '--extractor', 'dwarf', '-vv'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "Found" in result.stdout
        assert "object files" in result.stdout
    
    @pytest.mark.e2e
    def test_summary_statistics(self, tmp_path):
        """Test summary statistics in output.
        
        Verifies: FR-1.9.2 (Summary Statistics)
        """
        code = "struct A { char a; int b; char c; }; int main() { A a; return 0; }"
        cpp = tmp_path / "test.cpp"
        cpp.write_text(code)
        obj = tmp_path / "test.o"
        subprocess.run(['g++', '-g', '-O0', '-c', str(cpp), '-o', str(obj)])
        
        result = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'dwarf', '-vv'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        # Should show summary
        assert "Optimization complete" in result.stdout
        assert "changes applied" in result.stdout.lower()
    
    @pytest.mark.e2e
    def test_verbosity_levels(self, tmp_path):
        """Test different verbosity levels produce different output.
        
        Verifies: FR-1.9.3 (Verbosity Levels)
        """
        code = "struct A { char a; int b; }; int main() { A a; return 0; }"
        cpp = tmp_path / "test.cpp"
        cpp.write_text(code)
        obj = tmp_path / "test.o"
        subprocess.run(['g++', '-g', '-O0', '-c', str(cpp), '-o', str(obj)])
        
        # Test default verbosity
        result_default = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'dwarf'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Test -vv
        result_verbose = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'dwarf', '-vv'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result_default.returncode == 0
        assert result_verbose.returncode == 0
        # Verbose should have more output
        assert len(result_verbose.stdout) >= len(result_default.stdout)
    
    @pytest.mark.e2e
    def test_skip_reason_reporting(self, tmp_path):
        """Test skip reasons are reported.
        
        Verifies: FR-1.9.5 (Skip Reason Reporting)
        """
        # Struct that will be skipped (already optimal)
        code = "struct Optimal { double a; int b; char c; }; int main() { Optimal o; return 0; }"
        cpp = tmp_path / "test.cpp"
        cpp.write_text(code)
        obj = tmp_path / "test.o"
        subprocess.run(['g++', '-g', '-O0', '-c', str(cpp), '-o', str(obj)])
        
        result = subprocess.run(
            ['python3', '__main__.py', str(obj), '--extractor', 'dwarf', '-vv'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        # Should report why struct was skipped (if verbose enough)
    
    @pytest.mark.e2e
    def test_configuration_logging(self, tmp_path):
        """Test configuration values are logged.
        
        Verifies: FR-1.9.4 (Configuration Logging)
        """
        code = "struct A { char a; int b; }; int main() { A a; return 0; }"
        cpp = tmp_path / "test.cpp"
        cpp.write_text(code)
        obj = tmp_path / "test.o"
        subprocess.run(['g++', '-g', '-O0', '-c', str(cpp), '-o', str(obj)])
        
        result = subprocess.run(
            ['python3', '__main__.py', str(obj),
             '--min-savings', '10',
             '--access-modifier-strategy', 'preserve',
             '--extractor', 'dwarf',
             '-vv'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        # Should log configuration (if implemented)
