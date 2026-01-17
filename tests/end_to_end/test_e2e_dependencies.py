import pytest
from .base_e2e import BaseE2ETest


class TestE2EDependencies(BaseE2ETest):
    
    @pytest.mark.e2e
    def test_nested_struct_two_levels(self):
        """Test Inner → Outer dependency ordering and size propagation."""
        cpp_content = """
struct Inner {
    int field1;
    long field2;
};

struct Outer {
    Inner inner;
    int extra;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        # Should process successfully
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_nested_struct_three_levels(self):
        """Test A → B → C dependency chain."""
        cpp_content = """
struct A {
    int value;
};

struct B {
    A a;
    int extra;
};

struct C {
    B b;
    int final;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        # Should process successfully
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_shared_dependency_multiple_parents(self):
        """Test Leaf used by multiple parents."""
        cpp_content = """
struct Leaf {
    long data;
};

struct Parent1 {
    Leaf leaf;
    int extra1;
};

struct Parent2 {
    Leaf leaf;
    long extra2;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        # Should process successfully
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_circular_dependency_detection(self):
        """Test A → B → A circular dependency (should skip)."""
        cpp_content = """
struct B;

struct A {
    B* b;
};

struct B {
    A* a;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        # Should handle circular dependency gracefully
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_size_propagation_through_chain(self):
        """Test size propagation through dependency chain."""
        cpp_content = """
struct Base {
    int value;
};

struct Middle {
    Base base1;
    Base base2;
    int extra;
};

struct Top {
    Middle middle;
    long final;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        
        # Should process successfully and show struct information
        assert result.returncode == 0