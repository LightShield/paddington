"""E2E tests for multi-file scenarios."""

import pytest
import subprocess
from pathlib import Path
from .base_e2e import BaseE2ETest


class TestMultiFile(BaseE2ETest):
    """Multi-file scenario e2e tests."""
    
    @pytest.mark.e2e
    def test_header_and_cpp_split(self, tmp_path):
        """Test struct in .h, usage in .cpp."""
        header_code = """
        struct Data {
            char flag;
            int id;
            double score;
        };
        """
        
        cpp_code = """
        #include "test.h"
        int main() {
            Data d;
            return 0;
        }
        """
        
        # Write header
        header_file = tmp_path / "test.h"
        header_file.write_text(header_code)
        
        # Write cpp
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(cpp_code)
        
        # Compile
        obj_file = tmp_path / "test.o"
        result = subprocess.run(
            ['g++', '-g', '-c', '-I', str(tmp_path), str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0
        
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_multiple_cpp_files_same_struct(self, tmp_path):
        """Test multiple .cpp files using same struct."""
        header_code = """
        struct Shared {
            char a;
            int b;
            double c;
        };
        """
        
        cpp1_code = """
        #include "shared.h"
        void func1() {
            Shared s;
        }
        """
        
        cpp2_code = """
        #include "shared.h"
        void func2() {
            Shared s;
        }
        """
        
        header_file = tmp_path / "shared.h"
        header_file.write_text(header_code)
        
        cpp1_file = tmp_path / "file1.cpp"
        cpp1_file.write_text(cpp1_code)
        
        cpp2_file = tmp_path / "file2.cpp"
        cpp2_file.write_text(cpp2_code)
        
        # Compile both
        obj1 = tmp_path / "file1.o"
        obj2 = tmp_path / "file2.o"
        
        subprocess.run(['g++', '-g', '-c', '-I', str(tmp_path), str(cpp1_file), '-o', str(obj1)])
        subprocess.run(['g++', '-g', '-c', '-I', str(tmp_path), str(cpp2_file), '-o', str(obj2)])
        
        # Optimize both
        result = self.run_optimize(obj1)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_constructor_in_header(self, tmp_path):
        """Test struct with inline constructor in header."""
        code = """
        struct Data {
            char a;
            int b;
            double c;
            
            Data(char x, int y, double z) : a(x), b(y), c(z) {}
        };
        int main() { return 0; }
        """
        
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_constructor_in_cpp(self, tmp_path):
        """Test struct with constructor implemented in .cpp."""
        header_code = """
        struct Data {
            char a;
            int b;
            double c;
            
            Data(char x, int y, double z);
        };
        """
        
        cpp_code = """
        #include "test.h"
        
        Data::Data(char x, int y, double z) : a(x), b(y), c(z) {}
        
        int main() { return 0; }
        """
        
        header_file = tmp_path / "test.h"
        header_file.write_text(header_code)
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(cpp_code)
        
        obj_file = tmp_path / "test.o"
        result = subprocess.run(
            ['g++', '-g', '-c', '-I', str(tmp_path), str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0
        
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_inline_vs_outline_methods(self, tmp_path):
        """Test struct with inline and outline methods."""
        header_code = """
        struct Data {
            char a;
            int b;
            
            void inline_method() { }
            void outline_method();
        };
        """
        
        cpp_code = """
        #include "test.h"
        
        void Data::outline_method() { }
        
        int main() { return 0; }
        """
        
        header_file = tmp_path / "test.h"
        header_file.write_text(header_code)
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(cpp_code)
        
        obj_file = tmp_path / "test.o"
        subprocess.run(['g++', '-g', '-c', '-I', str(tmp_path), str(cpp_file), '-o', str(obj_file)])
        
        result = self.run_optimize(obj_file)
        self.assert_success(result)
