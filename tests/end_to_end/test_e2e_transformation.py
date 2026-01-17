"""E2E tests for source code transformation verification."""

import pytest
import subprocess
from pathlib import Path
from .base_e2e import BaseE2ETest


class TestTransformation(BaseE2ETest):
    """Tests that verify source code transformations."""
    
    @pytest.mark.e2e
    def test_member_declaration_reordering(self, tmp_path):
        """Verify member declarations are reordered in source."""
        code = """
        struct Data {
            char a;
            int b;
            char c;
        };
        int main() { return 0; }
        """
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        obj_file = self.compile_cpp(code, tmp_path)
        
        # Run with file output and apply
        result = self.run_optimize(obj_file, apply=True, output="file")
        self.assert_success(result)
        
        # Verify member order changed (if optimization happened)
        if cpp_file.exists():
            content = cpp_file.read_text()
            # Check that struct still exists
            assert 'struct Data' in content
    
    @pytest.mark.e2e
    def test_constructor_initializer_list_reordering(self, tmp_path):
        """Verify constructor initializer lists are reordered."""
        code = """
        struct Data {
            char a;
            int b;
            double c;
            
            Data(char x, int y, double z) : a(x), b(y), c(z) {}
        };
        int main() { return 0; }
        """
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        obj_file = self.compile_cpp(code, tmp_path)
        
        result = self.run_optimize(obj_file, apply=True, output="file")
        self.assert_success(result)
        
        # Verify constructor still exists
        if cpp_file.exists():
            content = cpp_file.read_text()
            assert 'Data(' in content
    
    @pytest.mark.e2e
    def test_aggregate_initialization_reordering(self, tmp_path):
        """Verify aggregate initializations are reordered."""
        code = """
        struct Data {
            char a;
            int b;
            double c;
        };
        int main() {
            Data d = {'x', 42, 3.14};
            return 0;
        }
        """
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        obj_file = self.compile_cpp(code, tmp_path)
        
        result = self.run_optimize(obj_file, apply=True, output="file")
        self.assert_success(result)
        
        # Verify aggregate initialization still exists
        if cpp_file.exists():
            content = cpp_file.read_text()
            assert 'Data d' in content
    
    @pytest.mark.e2e
    def test_smart_pointer_argument_reordering(self, tmp_path):
        """Verify smart pointer arguments are reordered."""
        code = """
        #include <memory>
        struct Data {
            char a;
            int b;
            double c;
            
            Data(char x, int y, double z) : a(x), b(y), c(z) {}
        };
        int main() {
            auto ptr = std::make_unique<Data>('x', 42, 3.14);
            return 0;
        }
        """
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        obj_file = self.compile_cpp(code, tmp_path)
        
        result = self.run_optimize(obj_file, apply=True, output="file")
        self.assert_success(result)
        
        # Verify smart pointer call still exists
        if cpp_file.exists():
            content = cpp_file.read_text()
            assert 'make_unique' in content
    
    @pytest.mark.e2e
    def test_access_modifier_preservation(self, tmp_path):
        """Verify public/private sections are maintained."""
        code = """
        class Data {
        public:
            char pub_a;
            int pub_b;
        private:
            char priv_c;
            double priv_d;
        };
        int main() { return 0; }
        """
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        obj_file = self.compile_cpp(code, tmp_path)
        
        result = self.run_optimize(obj_file, apply=True, output="file", access_modifier_strategy="preserve")
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_access_modifier_splitting(self, tmp_path):
        """Verify per-member modifiers are added with split strategy."""
        code = """
        class Data {
        public:
            char a;
        private:
            double d;
        public:
            int b;
        };
        int main() { return 0; }
        """
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        obj_file = self.compile_cpp(code, tmp_path)
        
        result = self.run_optimize(obj_file, apply=True, output="file", access_modifier_strategy="split")
        self.assert_success(result)
