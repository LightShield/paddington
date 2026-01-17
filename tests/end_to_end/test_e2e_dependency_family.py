import pytest
from .base_e2e import BaseE2ETest


class TestE2EDependencyFamily(BaseE2ETest):
    """Verifies: FR-1.1.4"""
    
    @pytest.mark.e2e
    def test_dependency_three_levels(self):
        """Verifies: FR-1.1.4 - Test three-level dependency chain A → B → C."""
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
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_dependency_four_levels(self):
        """Verifies: FR-1.1.4 - Test four-level dependency chain A → B → C → D."""
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
    int middle;
};

struct D {
    C c;
    int final;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_dependency_diamond(self):
        """Verifies: FR-1.1.4 - Test diamond dependency pattern Base → Left/Right → Top."""
        cpp_content = """
struct Base {
    int value;
};

struct Left {
    Base base;
    int left_data;
};

struct Right {
    Base base;
    int right_data;
};

struct Top {
    Left left;
    Right right;
    int top_data;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_dependency_size_propagation(self):
        """Verifies: FR-1.1.4 - Test size propagation through dependency chain."""
        cpp_content = """
struct Small {
    char c;
};

struct Medium {
    Small small1;
    Small small2;
    int value;
};

struct Large {
    Medium medium1;
    Medium medium2;
    long data;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_dependency_circular_pointers(self):
        """Verifies: FR-1.1.4 - Test circular dependency with pointers A ↔ B."""
        cpp_content = """
struct B;

struct A {
    B* b_ptr;
    int value;
};

struct B {
    A* a_ptr;
    int data;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_dependency_self_reference(self):
        """Verifies: FR-1.1.4 - Test self-referencing struct with pointer."""
        cpp_content = """
struct Node {
    Node* next;
    int data;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_dependency_mutual_recursion(self):
        """Verifies: FR-1.1.4 - Test mutual recursion A → B → C → A."""
        cpp_content = """
struct B;
struct C;

struct A {
    B* b_ptr;
    int value;
};

struct B {
    C* c_ptr;
    int data;
};

struct C {
    A* a_ptr;
    int info;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        assert result.returncode == 0

    @pytest.mark.e2e
    def test_dependency_optimization_order(self):
        """Verifies: FR-1.1.4 - Test optimization order with mixed dependencies."""
        cpp_content = """
struct Leaf {
    int value;
};

struct Branch1 {
    Leaf leaf;
    int extra1;
};

struct Branch2 {
    Leaf leaf;
    int extra2;
};

struct Root {
    Branch1 branch1;
    Branch2 branch2;
    int root_data;
};
"""
        obj_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(obj_file)
        assert result.returncode == 0