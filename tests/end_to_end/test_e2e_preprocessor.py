"""E2E tests for preprocessor and macro handling."""

import pytest
from .base_e2e import BaseE2ETest


class TestPreprocessor(BaseE2ETest):
    """Preprocessor and macro e2e tests."""
    
    @pytest.mark.e2e
    def test_ifdef_in_struct_definition(self, tmp_path):
        """Test struct with #ifdef (should skip)."""
        code = """
        struct Config {
            char a;
        #ifdef DEBUG
            int debug_flag;
        #endif
            double b;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # Should skip this struct
    
    @pytest.mark.e2e
    def test_macro_defined_members(self, tmp_path):
        """Test struct with macro-defined members."""
        code = """
        #define MEMBER_TYPE int
        struct Data {
            char a;
            MEMBER_TYPE b;
            double c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_conditional_compilation(self, tmp_path):
        """Test conditional compilation."""
        code = """
        struct Platform {
        #if defined(__APPLE__)
            char apple_specific;
        #elif defined(__linux__)
            char linux_specific;
        #endif
            int common;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_pragma_pack(self, tmp_path):
        """Test #pragma pack directive."""
        code = """
        #pragma pack(push, 1)
        struct Packed {
            char a;
            int b;
            char c;
        };
        #pragma pack(pop)
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # Should skip packed structs
    
    @pytest.mark.e2e
    def test_attribute_aligned(self, tmp_path):
        """Test __attribute__((aligned)) directive."""
        code = """
        struct Aligned {
            char a;
            int b __attribute__((aligned(16)));
            char c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_mixed_preprocessor_and_code(self, tmp_path):
        """Test mix of preprocessor and normal code."""
        code = """
        #define SIZE 10
        struct Mixed {
            char array[SIZE];
            int count;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
