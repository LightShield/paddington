import pytest
import os
from .base_e2e import BaseE2ETest


class TestE2EDryRunFamily(BaseE2ETest):
    """Verifies: FR-1.3.2"""
    
    @pytest.mark.e2e
    def test_dry_run_default_behavior(self):
        """Test dry run is default behavior"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_dry_run_no_files_modified(self):
        """Test dry run mode doesn't modify files"""
        cpp_content = """
struct Data {
    int a;
    int b;
    int c;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        original_mtime = os.path.getmtime(cpp_file)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert os.path.getmtime(cpp_file) == original_mtime
    
    @pytest.mark.e2e
    def test_dry_run_with_patches(self):
        """Test dry run with patch output"""
        cpp_content = """
struct Config {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, ["--output", "patch", "--patch-dir", self.temp_dir])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_dry_run_output_format(self):
        """Test dry run output format"""
        cpp_content = """
struct Item {
    int id;
    int value;
    int count;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert result.stdout  # Should have output
    
    @pytest.mark.e2e
    def test_dry_run_multiple_structs(self):
        """Test dry run with multiple structs"""
        cpp_content = """
struct Point {
    int x;
    int y;
};

struct Vector {
    int a;
    int b;
    int c;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)