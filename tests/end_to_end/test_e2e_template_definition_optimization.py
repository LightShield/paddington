"""Tests for template definition optimization.

When we extract Foo<int> from .o files, we should:
1. Detect it's a template instantiation
2. Find the template definition: template<typename T> struct Foo
3. Optimize the template definition
4. All instantiations benefit
"""

import pytest
from tests.end_to_end.base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestTemplateDefinitionOptimization(BaseE2ETest):
    
    @pytest.mark.e2e
    def test_optimize_template_definition_not_instantiation(self, tmp_path):
        """Test that we optimize template<T> struct Foo, not Foo<int>."""
        test_case = E2ETestCase(
            name="template_definition",
            cpp_code="""
template<typename T>
struct Foo {
    char a;      // 1 byte + 3 padding
    int b;       // 4 bytes
    T* ptr;      // 8 bytes
    // Total: 16 bytes with 3 bytes padding
    // Optimal: ptr, b, a (12 bytes)
};

int main() {
    Foo<int> f1;
    Foo<double> f2;
    return 0;
}
""",
            flags={'extractor': 'pahole', 'source_root': str(tmp_path), 'verbose': True},
            expected_structs=[
                StructExpectation(
                    name="Foo<int>",  # Extracted from .o
                    size_before=16,
                    size_after=12,
                    member_order_before=["a", "b", "ptr"],
                    member_order_after=["ptr", "b", "a"],
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["Template instantiation detected"]  # Should detect template
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_optimize_nested_template_types(self, tmp_path):
        """Test optimizing Bar inside Foo<Bar<int>>."""
        test_case = E2ETestCase(
            name="nested_templates",
            cpp_code="""
template<typename T>
struct Bar {
    char a;      // 1 byte + 3 padding
    int b;       // 4 bytes
    T value;     // varies
};

template<typename T>
struct Foo {
    char x;      // 1 byte + 7 padding
    T data;      // varies
};

int main() {
    Foo<Bar<int>> nested;
    return 0;
}
""",
            flags={'extractor': 'pahole', 'source_root': str(tmp_path), 'verbose': True},
            expected_structs=[
                StructExpectation(
                    name="Bar<int>",
                    size_before=12,  # char(1) + padding(3) + int(4) + int(4) = 12
                    size_after=12,   # int(4) + int(4) + char(1) + padding(3) = 12 (no savings)
                    member_order_before=["a", "b", "value"],
                    member_order_after=["b", "value", "a"],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_extract_types_from_complex_template(self, tmp_path):
        """Test extracting Bar from vector<Foo<tuple<Bar, int>>>."""
        test_case = E2ETestCase(
            name="complex_nested",
            cpp_code="""
#include <vector>
#include <tuple>

struct Bar {
    char a;      // 1 byte + 3 padding
    int b;       // 4 bytes
    // Total: 8 bytes with 3 bytes padding
    // Optimal: b, a (5 bytes rounded to 8)
};

template<typename T>
struct Foo {
    T data;
};

int main() {
    std::vector<Foo<std::tuple<Bar, int>>> complex;
    return 0;
}
""",
            flags={'extractor': 'pahole', 'source_root': str(tmp_path), 'verbose': True},
            expected_structs=[
                StructExpectation(
                    name="Bar",
                    size_before=8,
                    size_after=8,
                    member_order_before=["a", "b"],
                    member_order_after=["b", "a"],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_template_definition_with_multiple_instantiations(self, tmp_path):
        """Test that optimizing template definition benefits all instantiations."""
        test_case = E2ETestCase(
            name="multiple_instantiations",
            cpp_code="""
template<typename T>
struct Container {
    char flag;   // 1 byte + 7 padding
    T* data;     // 8 bytes
};

int main() {
    Container<int> c1;
    Container<double> c2;
    Container<char> c3;
    return 0;
}
""",
            flags={'extractor': 'pahole', 'source_root': str(tmp_path), 'verbose': True},
            expected_structs=[
                StructExpectation(
                    name="Container<int>",
                    size_before=16,
                    size_after=16,  # After optimizing template
                    member_order_before=["flag", "data"],
                    member_order_after=["data", "flag"],
                    padding_saved=0,  # Per instantiation
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_patches_count=1  # Only 1 patch for template definition
        )
        self.run_test_case(test_case, tmp_path)
