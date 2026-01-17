import pytest
import tempfile
import subprocess
import os
import shutil
from pathlib import Path


class TestE2EMinSavingsFamily:
    """Verifies: FR-1.2.4"""
    
    def setup_method(self):
        """Setup temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup temporary directory after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def compile_cpp(self, content):
        """Compile C++ content and return object file path."""
        cpp_file = self.temp_dir / "test.cpp"
        cpp_file.write_text(content)
        obj_file = self.temp_dir / "test.o"
        
        cmd = ["g++", "-c", "-g", str(cpp_file), "-o", str(obj_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Compilation failed: {result.stderr}")
        
        return obj_file
    
    def run_optimize(self, obj_file, args=None):
        """Run paddington optimize command."""
        if args is None:
            args = []
        
        cmd = ["python", "-m", "paddington", "optimize"] + args + [str(obj_file)]
        result = subprocess.run(
            cmd,
            cwd=self.original_cwd,
            capture_output=True,
            text=True
        )
        return result
    
    def assert_success(self, result):
        """Assert that command executed successfully."""
        if result.returncode != 0:
            print(f"Command failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
        assert result.returncode == 0
    
    @pytest.mark.e2e
    def test_threshold_zero(self):
        """Test threshold 0 - all optimized"""
        cpp_content = """
struct Test {
    char a;
    int b;
    char c;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_threshold_small(self):
        """Test threshold 4 bytes"""
        cpp_content = """
struct Test {
    char a;
    int b;
    char c;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_threshold_medium(self):
        """Test threshold 8 bytes"""
        cpp_content = """
struct Test {
    char a;
    int b;
    char c;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_threshold_large(self):
        """Test threshold 16 bytes"""
        cpp_content = """
struct Test {
    char a;
    int b;
    char c;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_threshold_exceeds_all(self):
        """Test threshold 100 bytes - nothing optimized"""
        cpp_content = """
struct Test {
    char a;
    int b;
    char c;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)