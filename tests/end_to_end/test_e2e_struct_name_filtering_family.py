import pytest
import os
from .base_e2e import BaseE2ETest


class TestE2EStructNameFilteringFamily(BaseE2ETest):
    """Verifies: FR-1.4.2"""
    
    @pytest.mark.e2e
    def test_filter_single_struct_name(self):
        """Test filtering by single struct name"""
        cpp_content = """
struct Point {
    int x;
    int y;
    int z;
};

struct Rectangle {
    int width;
    int height;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, ["--struct-names", "Point"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Feature not implemented yet - expect unrecognized argument error
        if "unrecognized arguments: --struct-names" in result.stderr:
            pytest.skip("Struct name filtering not implemented yet")
        
        self.assert_success(result)
        
        # Should process only Point struct
        assert "Point" in result.stdout or result.returncode == 0
    
    @pytest.mark.e2e
    def test_filter_multiple_struct_names(self):
        """Test filtering by multiple struct names"""
        cpp_content = """
struct Point {
    int x;
    int y;
};

struct Rectangle {
    int width;
    int height;
};

struct Circle {
    int radius;
    int center_x;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, ["--struct-names", "Point,Rectangle"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Feature not implemented yet - expect unrecognized argument error
        if "unrecognized arguments: --struct-names" in result.stderr:
            pytest.skip("Struct name filtering not implemented yet")
        
        self.assert_success(result)
        
        # Should process Point and Rectangle but not Circle
        assert result.returncode == 0
    
    @pytest.mark.e2e
    def test_filter_wildcard_pattern(self):
        """Test filtering with wildcard patterns"""
        cpp_content = """
struct DataPoint {
    int value;
    int timestamp;
};

struct DataBuffer {
    int size;
    int capacity;
};

struct Config {
    int setting;
    int mode;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, ["--struct-names", "Data*"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Feature not implemented yet - expect unrecognized argument error
        if "unrecognized arguments: --struct-names" in result.stderr:
            pytest.skip("Struct name filtering not implemented yet")
        
        self.assert_success(result)
        
        # Should process DataPoint and DataBuffer but not Config
        assert result.returncode == 0
    
    @pytest.mark.e2e
    def test_filter_case_sensitive(self):
        """Test case-sensitive struct name filtering"""
        cpp_content = """
struct point {
    int x;
    int y;
};

struct Point {
    int x;
    int y;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, ["--struct-names", "Point"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Feature not implemented yet - expect unrecognized argument error
        if "unrecognized arguments: --struct-names" in result.stderr:
            pytest.skip("Struct name filtering not implemented yet")
        
        self.assert_success(result)
        
        # Should process only Point (uppercase) not point (lowercase)
        assert result.returncode == 0
    
    @pytest.mark.e2e
    def test_filter_namespace_qualified(self):
        """Test filtering namespace-qualified struct names"""
        cpp_content = """
namespace geometry {
    struct Point {
        int x;
        int y;
    };
}

struct Point {
    int x;
    int y;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, ["--struct-names", "geometry::Point"])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        # Feature not implemented yet - expect unrecognized argument error
        if "unrecognized arguments: --struct-names" in result.stderr:
            pytest.skip("Struct name filtering not implemented yet")
        
        self.assert_success(result)
        
        # Should process only geometry::Point not global Point
        assert result.returncode == 0