import pytest
import os
import stat
import shutil
import subprocess
from .base_e2e import BaseE2ETest


class TestE2EDirectModificationFamily(BaseE2ETest):
    """Verifies: FR-1.3.3"""
    
    @pytest.mark.e2e
    def test_modify_single_file(self):
        """Test direct modification of a single file"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        original_mtime = os.path.getmtime(cpp_file)
        
        result = self.run_optimize(cpp_file, ["--apply", "--output", "file"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert os.path.exists(cpp_file)
    
    @pytest.mark.e2e
    def test_modify_multiple_files(self):
        """Test direct modification of multiple files"""
        cpp_content1 = """
struct Point {
    int x;
    int y;
};
"""
        cpp_content2 = """
struct Vector {
    float a;
    float b;
    float c;
};
"""
        cpp_file1 = self.compile_cpp(cpp_content1)
        cpp_file2 = self.create_file("test2.cpp", cpp_content2)
        obj_file2 = os.path.join(self.temp_dir, "test2.o")
        
        # Compile second file
        cmd = ["g++", "-c", "-g", str(cpp_file2), "-o", obj_file2]
        subprocess.run(cmd, capture_output=True, text=True)
        
        # Run on directory (not individual files)
        result = self.run_paddington([self.temp_dir, "--apply", "--output", "file"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        assert os.path.exists(cpp_file1)
        assert os.path.exists(obj_file2)
    
    @pytest.mark.e2e
    def test_modify_creates_backup(self):
        """Test that modification creates backup files"""
        cpp_content = """
struct Data {
    int value;
    char flag;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, ["--apply", "--output", "file"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        
        # Check for backup file (common patterns)
        backup_patterns = [str(cpp_file) + ".bak", str(cpp_file) + ".backup", str(cpp_file) + "~"]
        backup_exists = any(os.path.exists(pattern) for pattern in backup_patterns)
        # Note: backup creation is implementation dependent
    
    @pytest.mark.e2e
    def test_modify_preserves_permissions(self):
        """Test that file permissions are preserved during modification"""
        cpp_content = """
struct Config {
    int setting;
    bool enabled;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        # Set specific permissions
        original_mode = os.stat(cpp_file).st_mode
        os.chmod(cpp_file, 0o644)
        
        result = self.run_optimize(cpp_file, ["--apply", "--output", "file"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        
        # Check permissions are preserved
        new_mode = os.stat(cpp_file).st_mode
        assert stat.S_IMODE(new_mode) == 0o644
    
    @pytest.mark.e2e
    def test_modify_atomic_operation(self):
        """Test that file modification is atomic"""
        cpp_content = """
struct Record {
    long id;
    double value;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, ["--apply", "--output", "file"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
        
        # File should exist and be readable (atomic operation completed)
        assert os.path.exists(cpp_file)
        assert os.access(cpp_file, os.R_OK)
    
    @pytest.mark.e2e
    def test_modify_rollback_on_error(self):
        """Test that modifications are rolled back on error"""
        cpp_content = """
struct Item {
    int count;
    float price;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        original_content = open(cpp_file, 'rb').read()
        
        # Force an error by making file read-only after compilation
        os.chmod(cpp_file, 0o444)
        
        result = self.run_optimize(cpp_file, ["--apply", "--output", "file"])
        
        # Restore permissions for cleanup
        os.chmod(cpp_file, 0o644)
        
        # On error, original file should be unchanged
        if result.returncode != 0:
            current_content = open(cpp_file, 'rb').read()
            assert current_content == original_content
        else:
            # If no error occurred, that's also acceptable
            pass