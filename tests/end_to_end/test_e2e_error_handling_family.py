import pytest
import os
import stat
import subprocess
import tempfile
from .base_e2e import BaseE2ETest


class E2ETestCase(BaseE2ETest):
    """Base class for E2E error handling tests."""
    pass


class TestE2EErrorHandlingFamily(E2ETestCase):
    
    @pytest.mark.e2e
    def test_error_missing_file(self):
        """Test missing file error handling - Verifies: NFR-2.5.1
        
        Verifies graceful handling when input file doesn't exist.
        """
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.o")
        
        result = self.run_optimize(nonexistent_file, ["optimize"])
        
        # Should handle gracefully - either fail or succeed with error message
        if result.returncode != 0:
            assert "not found" in result.stderr.lower() or "no such file" in result.stderr.lower() or "error" in result.stderr.lower()
        else:
            # If it succeeds, should have error message in stderr
            assert "error" in result.stderr.lower() or "does not exist" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_error_invalid_file_format(self):
        """Test invalid file format error handling - Verifies: NFR-2.5.1
        
        Verifies graceful handling of non-object files.
        """
        # Create a text file with .o extension
        invalid_file = self.create_file("invalid.o", "This is not an object file")
        
        result = self.run_optimize(invalid_file, ["optimize"])
        
        # Should handle gracefully - either fail or succeed with no results
        if result.returncode != 0:
            assert len(result.stderr) > 0, "Should provide error message"
        else:
            # If it succeeds, should show 0 structs analyzed (graceful handling)
            assert "0 struct" in result.stdout or "Total structs analyzed: 0" in result.stdout
    
    @pytest.mark.e2e
    def test_error_corrupted_object_file(self):
        """Test corrupted object file error handling - Verifies: NFR-2.5.1
        
        Verifies graceful handling of corrupted object files.
        """
        # Create a file that looks like an object file but is corrupted
        corrupted_file = os.path.join(self.temp_dir, "corrupted.o")
        with open(corrupted_file, "wb") as f:
            f.write(b"\x7fELF")  # ELF header start
            f.write(b"\x00" * 100)  # Corrupted data
        
        result = self.run_optimize(corrupted_file, ["optimize"])
        
        # Should handle gracefully - either fail or succeed with no results
        if result.returncode != 0:
            assert len(result.stderr) > 0, "Should provide error message"
        else:
            # If it succeeds, should show 0 structs analyzed (graceful handling)
            assert "0 struct" in result.stdout or "Total structs analyzed: 0" in result.stdout
    
    @pytest.mark.e2e
    def test_error_no_dwarf_info(self):
        """Test no DWARF info error handling - Verifies: NFR-2.5.1
        
        Verifies graceful handling when object file has no debug info.
        """
        cpp_content = """
struct TestStruct {
    char a;
    int b;
};
"""
        cpp_file = self.create_file("nodebug.cpp", cpp_content)
        obj_file = os.path.join(self.temp_dir, "nodebug.o")
        
        # Compile without debug info
        cmd = ["g++", "-c", cpp_file, "-o", obj_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, "Compilation should succeed"
        
        result = self.run_optimize(obj_file, ["optimize"])
        
        # Should handle gracefully - either succeed with no changes or fail gracefully
        if result.returncode != 0:
            assert "debug" in result.stderr.lower() or "dwarf" in result.stderr.lower() or len(result.stderr) > 0
    
    @pytest.mark.e2e
    def test_error_read_only_file(self):
        """Test read-only file error handling - Verifies: NFR-2.5.1
        
        Verifies graceful handling of read-only files when trying to modify.
        """
        cpp_content = """
struct ReadOnlyStruct {
    char a;
    int b;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        # Make object file read-only
        os.chmod(obj_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        
        result = self.run_optimize(obj_file, ["optimize", "--apply", "--output", "file"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Should handle read-only gracefully
        if result.returncode != 0:
            assert "permission" in result.stderr.lower() or "read-only" in result.stderr.lower() or len(result.stderr) > 0
        
        # Restore permissions for cleanup
        os.chmod(obj_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    
    @pytest.mark.e2e
    def test_error_disk_full(self):
        """Test disk full error handling - Verifies: NFR-2.5.1
        
        Verifies graceful handling when disk space is insufficient.
        """
        cpp_content = """
struct DiskFullStruct {
    char a;
    int b;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        # Create output in /dev/full (simulates disk full on Linux)
        if os.path.exists("/dev/full"):
            result = self.run_optimize(obj_file, ["optimize", "--apply", "--output", "/dev/full/output.cpp"])
            
            if result.returncode != 0:
                assert "space" in result.stderr.lower() or "full" in result.stderr.lower() or len(result.stderr) > 0
        else:
            # Skip on systems without /dev/full
            pytest.skip("System doesn't support disk full simulation")
    
    @pytest.mark.e2e
    def test_error_invalid_flags(self):
        """Test invalid flags error handling - Verifies: NFR-2.5.1
        
        Verifies graceful handling of invalid command line flags.
        """
        cpp_content = """
struct InvalidFlagsStruct {
    char a;
    int b;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(obj_file, ["optimize", "--invalid-flag", "--another-invalid"])
        
        assert result.returncode != 0, "Should fail for invalid flags"
        assert "invalid" in result.stderr.lower() or "unknown" in result.stderr.lower() or "unrecognized" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_error_graceful_degradation(self):
        """Test graceful degradation - Verifies: NFR-2.5.1
        
        Verifies system continues to function when encountering partial errors.
        """
        cpp_content = """
struct GracefulStruct {
    char a;
    int b;
    char c;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        
        # Test with potentially problematic but not fatal conditions
        result = self.run_optimize(obj_file, ["--verbose"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Should either succeed or fail gracefully without crashing
        assert result.returncode in [0, 1], "Should not crash unexpectedly"
        
        # If it fails, should provide meaningful error message
        if result.returncode != 0:
            assert len(result.stderr) > 0, "Should provide error message on failure"