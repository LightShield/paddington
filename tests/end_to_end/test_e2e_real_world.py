"""E2E tests for real-world scenarios."""

import pytest
from .base_e2e import BaseE2ETest


class TestRealWorld(BaseE2ETest):
    """Real-world scenario e2e tests."""
    
    @pytest.mark.e2e
    def test_extern_c_structs(self, tmp_path):
        """Test extern C structs."""
        code = """
        extern "C" {
            struct CStruct {
                char a;
                int b;
                char c;
            };
        }
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_packed_structs(self, tmp_path):
        """Test __attribute__((packed)) structs."""
        code = """
        struct __attribute__((packed)) Packed {
            char a;
            int b;
            char c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # Should skip packed structs
    
    @pytest.mark.e2e
    def test_custom_allocators(self, tmp_path):
        """Test struct with custom allocator."""
        code = """
        template<typename T>
        struct CustomAlloc {};
        
        struct Data {
            char a;
            int b;
            double c;
        };
        int main() {
            Data d;
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_placement_new(self, tmp_path):
        """Test struct used with placement new."""
        code = """
        #include <new>
        struct Data {
            char a;
            int b;
            double c;
        };
        int main() {
            alignas(Data) char buffer[sizeof(Data)];
            Data* d = new (buffer) Data();
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_const_and_volatile_members(self, tmp_path):
        """Test struct with const and volatile members."""
        code = """
        struct Special {
            const char a;
            volatile int b;
            double c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
