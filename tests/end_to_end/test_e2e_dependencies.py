"""E2E tests for struct dependencies and size propagation."""

import pytest
from .base_e2e import BaseE2ETest


class TestDependencies(BaseE2ETest):
    """Dependency handling e2e tests."""
    
    @pytest.mark.e2e
    def test_nested_struct_two_levels(self, tmp_path):
        """Test Inner → Outer dependency."""
        code = """
        struct Inner {
            char a;
            int b;
        };
        struct Outer {
            int x;
            Inner inner;
            double y;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_nested_struct_three_levels(self, tmp_path):
        """Test A → B → C dependency chain."""
        code = """
        struct A {
            char a;
            int b;
        };
        struct B {
            char x;
            A a_member;
            int y;
        };
        struct C {
            double d;
            B b_member;
            char c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_shared_dependency_multiple_parents(self, tmp_path):
        """Test leaf struct used by multiple parents."""
        code = """
        struct Leaf {
            char a;
            int b;
        };
        struct Parent1 {
            Leaf l;
            int x;
        };
        struct Parent2 {
            Leaf l;
            double y;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_circular_dependency_pointers(self, tmp_path):
        """Test circular dependency with pointers."""
        code = """
        struct A;
        struct B {
            int x;
            A* a_ptr;
        };
        struct A {
            char c;
            B* b_ptr;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_size_propagation_through_chain(self, tmp_path):
        """Test size propagation through dependency chain."""
        code = """
        struct Small {
            char a;
            int b;
            char c;
        };
        struct Medium {
            Small s;
            int x;
        };
        struct Large {
            Medium m;
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
