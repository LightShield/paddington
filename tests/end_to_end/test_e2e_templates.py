"""E2E tests for template handling."""

import pytest
from .base_e2e import BaseE2ETest


class TestTemplates(BaseE2ETest):
    """Template handling e2e tests."""
    
    @pytest.mark.e2e
    def test_template_with_primitive_types(self, tmp_path):
        """Test template instantiated with int/double."""
        code = """
        template<typename T>
        struct Container {
            char flag;
            T value;
            int count;
        };
        int main() {
            Container<int> c1;
            Container<double> c2;
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_template_with_struct_types(self, tmp_path):
        """Test template with struct as T."""
        code = """
        struct Data {
            char a;
            int b;
        };
        template<typename T>
        struct Wrapper {
            char flag;
            T value;
        };
        int main() {
            Wrapper<Data> w;
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_template_multiple_instantiations(self, tmp_path):
        """Test same template with different types."""
        code = """
        template<typename T>
        struct Box {
            char label;
            T item;
        };
        int main() {
            Box<char> b1;
            Box<int> b2;
            Box<double> b3;
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_template_partial_specialization(self, tmp_path):
        """Test partially specialized template."""
        code = """
        template<typename T>
        struct Container {
            char a;
            T value;
        };
        template<>
        struct Container<int> {
            int value;
            char a;
        };
        int main() {
            Container<int> c;
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_template_with_non_type_params(self, tmp_path):
        """Test template with non-type parameter."""
        code = """
        template<int N>
        struct Array {
            char flag;
            int data[N];
        };
        int main() {
            Array<10> arr;
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_template_nested_in_struct(self, tmp_path):
        """Test template nested inside struct."""
        code = """
        struct Outer {
            template<typename T>
            struct Inner {
                char a;
                T value;
            };
            char x;
            int y;
        };
        int main() {
            Outer::Inner<int> i;
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_variadic_template(self, tmp_path):
        """Test variadic template."""
        code = """
        template<typename... Args>
        struct Tuple {
            char flag;
            int count;
        };
        int main() {
            Tuple<int, double, char> t;
            return 0;
        }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
