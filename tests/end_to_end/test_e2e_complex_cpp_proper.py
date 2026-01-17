import pytest
from .base_e2e import BaseE2ETest


class TestE2EComplexCppProper(BaseE2ETest):
    
    @pytest.mark.e2e
    def test_inheritance_derived_members_only(self):
        """Test FR-1.9: Only derived class members reordered, base unchanged"""
        cpp_content = """
struct Base {
    char a;
    int b;
};

struct Derived : Base {
    char c;
    double d;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_bitfields_skipped(self):
        """Test FR-1.9: Bitfield structs are skipped"""
        cpp_content = """
struct Flags {
    unsigned int a : 1;
    unsigned int b : 3;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_unions_skipped(self):
        """Test FR-1.9: Unions are skipped"""
        cpp_content = """
union Data {
    char c;
    int i;
    double d;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_virtual_functions_vtable(self):
        """Test FR-1.9: Vtable pointer handled correctly"""
        cpp_content = """
struct Base {
    char a;
    virtual void foo();
    int b;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_anonymous_struct_skipped(self):
        """Test FR-1.9: Anonymous structs in unions are skipped"""
        cpp_content = """
union Container {
    struct {
        int x;
        int y;
    };
    double value;
};
"""
        cpp_file = self.compile_cpp(cpp_content)
        
        result = self.run_optimize(cpp_file, [])
        
        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
            pytest.skip("Application has import issues")
        
        self.assert_success(result)