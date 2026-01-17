"""E2E tests for complex C++ scenarios."""

import pytest
from .base_e2e import BaseE2ETest


class TestComplexScenarios(BaseE2ETest):
    """Complex C++ scenario e2e tests."""
    
    @pytest.mark.e2e
    def test_inheritance_single(self, tmp_path):
        """Test single inheritance."""
        code = """
        struct Base {
            char a;
            int b;
        };
        struct Derived : Base {
            char c;
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_inheritance_multiple(self, tmp_path):
        """Test multiple inheritance."""
        code = """
        struct Base1 {
            char a;
        };
        struct Base2 {
            int b;
        };
        struct Derived : Base1, Base2 {
            char c;
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_virtual_functions_vtable(self, tmp_path):
        """Test struct with virtual functions (has vtable)."""
        code = """
        struct Base {
            char a;
            virtual void foo() {}
            int b;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # Should handle vtable pointer
    
    @pytest.mark.e2e
    def test_bitfields(self, tmp_path):
        """Test struct with bitfields (should skip)."""
        code = """
        struct Flags {
            unsigned int a : 1;
            unsigned int b : 3;
            unsigned int c : 4;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # Should skip bitfields
    
    @pytest.mark.e2e
    def test_union_members(self, tmp_path):
        """Test union (should skip)."""
        code = """
        union Data {
            char c;
            int i;
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # Should skip unions
    
    @pytest.mark.e2e
    def test_anonymous_struct_in_union(self, tmp_path):
        """Test anonymous struct in union."""
        code = """
        union Data {
            struct {
                char a;
                int b;
            };
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_large_struct_many_members(self, tmp_path):
        """Test struct with many members."""
        code = """
        struct Large {
            char a1, a2, a3, a4;
            int b1, b2, b3, b4;
            double c1, c2, c3, c4;
            short d1, d2, d3, d4;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_multiple_structs_same_file(self, tmp_path):
        """Test multiple structs in same file."""
        code = """
        struct A {
            char a;
            int b;
        };
        struct B {
            char x;
            double y;
        };
        struct C {
            int i;
            char c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
