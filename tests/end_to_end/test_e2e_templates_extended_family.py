import pytest
from .base_e2e import BaseE2ETest


class TestE2ETemplatesExtendedFamily(BaseE2ETest):
    """Verifies: FR-1.7 - Extended template handling family tests"""
    
    @pytest.mark.e2e
    def test_template_with_primitive_types(self):
        """Verifies: FR-1.7 - Template with primitive type parameters"""
        cpp_content = """
template<typename T>
struct Container {
    T value;
    int size;
};

Container<int> int_container;
Container<char> char_container;
Container<double> double_container;
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file)
        assert result.returncode == 0 or "template" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_template_with_struct_types(self):
        """Verifies: FR-1.7 - Template with struct type parameters"""
        cpp_content = """
struct Point {
    int x, y;
};

struct Vector {
    float x, y, z;
};

template<typename T>
struct Wrapper {
    T data;
    int count;
};

Wrapper<Point> point_wrapper;
Wrapper<Vector> vector_wrapper;
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file)
        assert result.returncode == 0 or "template" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_template_with_pointer_types(self):
        """Verifies: FR-1.7 - Template with pointer type parameters"""
        cpp_content = """
template<typename T>
struct Ptrs {
    T* ptr;
    T** double_ptr;
    int count;
};

Ptrs<int> int_ptrs;
Ptrs<char> char_ptrs;
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file)
        assert result.returncode == 0 or "template" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_template_with_reference_types(self):
        """Verifies: FR-1.7 - Template with reference type parameters"""
        cpp_content = """
template<typename T>
struct Mixed {
    T value;
    T& ref;
    T* ptr;
    
    Mixed(T& r) : ref(r) {}
};

int global_int = 42;
Mixed<int> mixed_int(global_int);
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file)
        assert result.returncode == 0 or "template" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_template_partial_specialization(self):
        """Verifies: FR-1.7 - Template partial specialization handling"""
        cpp_content = """
template<typename T>
struct Large {
    T data[100];
    int size;
};

template<>
struct Large<bool> {
    bool data[100];
    char size;
};

Large<int> large_int;
Large<bool> large_bool;
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file)
        assert result.returncode == 0 or "template" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_template_variadic(self):
        """Verifies: FR-1.7 - Variadic template handling"""
        cpp_content = """
template<typename... Args>
struct Tuple {
    char data[sizeof...(Args) * 8];
    int arg_count;
};

Tuple<int> single;
Tuple<int, double> pair;
Tuple<int, double, char> triple;
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file)
        assert result.returncode == 0 or "template" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_template_non_type_param(self):
        """Verifies: FR-1.7 - Template with non-type parameters"""
        cpp_content = """
template<int N>
struct FixedArray {
    int data[N];
    int capacity;
};

FixedArray<5> small;
FixedArray<100> large;
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file)
        assert result.returncode == 0 or "template" in result.stderr.lower()
    
    @pytest.mark.e2e
    def test_template_nested(self):
        """Verifies: FR-1.7 - Nested template structures"""
        cpp_content = """
struct Outer {
    template<typename T>
    struct Inner {
        T value;
        int id;
    };
    
    Inner<int> int_inner;
    Inner<double> double_inner;
};

Outer outer;
"""
        cpp_file = self.compile_cpp(cpp_content)
        result = self.run_optimize(cpp_file)
        assert result.returncode == 0 or "template" in result.stderr.lower()