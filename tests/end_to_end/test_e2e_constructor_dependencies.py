"""
Verifies: FR-1.1.5 - Constructor Dependency Detection Test Family

Tests constructor dependency detection to prevent optimization of members
that are used in constructor initialization lists.

TODO: Constructor dependency detection needs to be implemented in SourceScanner
for whole-codebase scans. Currently only works for single-file analysis.
"""

import pytest
from tests.end_to_end.base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestE2EConstructorDependencies(BaseE2ETest):
    
    @pytest.mark.e2e
    def test_dependency_member_uses_member(self, tmp_path):
        """Test buffer(new char[size]) depends on size."""
        # Create a struct with padding that WOULD be optimized, but has constructor dependencies
        test_case = E2ETestCase(
            name="member_uses_member",
            cpp_code="""
struct Data { 
    char a;       // 1 byte + 3 padding
    int size;     // 4 bytes
    char c;       // 1 byte + 7 padding  
    double* buffer; // 8 bytes
    // Total: 24 bytes with 10 bytes padding
    // Optimal would be: buffer, size, a, c (16 bytes, 8 bytes saved)
    // But constructor has: buffer(new double[size]) - depends on size
    Data(int s) : size(s), buffer(new double[size]), a('x'), c('y') {} 
}; 
int main() { Data d(10); return 0; }
""",
            flags={'extractor': 'pahole', 'source_root': str(tmp_path), 'verbose': True},
            expected_structs=[StructExpectation(
                name="Data",
                size_before=24,
                size_after=24,  # Should stay same due to constructor deps
                member_order_before=["a", "size", "c", "buffer"],
                member_order_after=["a", "size", "c", "buffer"],  # Order preserved
                padding_saved=0,
                should_optimize=False,
                skip_reason="constructor dependencies"
            )],
            should_succeed=True,
            expected_output_contains=["constructor dependencies"]  # Verify skip reason is reported
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_multiple_dependencies(self, tmp_path):
        """Test multiple member dependencies."""
        test_case = E2ETestCase(
            name="multiple_dependencies",
            cpp_code="""struct Multi { int width; int height; int* data; Multi(int w, int h) : width(w), height(h), data(new int[width * height]) {} }; int main() { Multi m(5, 10); return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[StructExpectation(
                name="Multi",
                size_before=24,
                size_after=24,
                member_order_before=["width", "height", "data"],
                member_order_after=["width", "height", "data"],
                padding_saved=0,
                should_optimize=False,
                skip_reason="Constructor dependencies prevent optimization"
            )],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_chain(self, tmp_path):
        """Test A depends on B depends on C."""
        test_case = E2ETestCase(
            name="dependency_chain",
            cpp_code="""struct Chain { int base; int derived; int final; Chain(int b) : base(b), derived(base * 2), final(derived + 1) {} }; int main() { Chain c(5); return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[StructExpectation(
                name="Chain",
                size_before=12,
                size_after=12,
                member_order_before=["base", "derived", "final"],
                member_order_after=["base", "derived", "final"],
                padding_saved=0,
                should_optimize=False,
                skip_reason="Dependency chain prevents optimization"
            )],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_circular(self, tmp_path):
        """Test A depends on B, B depends on A (should skip)."""
        test_case = E2ETestCase(
            name="circular_dependency",
            cpp_code="""struct Circular { int a; int b; Circular(int x) : a(b + 1), b(a + 1) {} }; int main() { Circular c(0); return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[StructExpectation(
                name="Circular",
                size_before=8,
                size_after=8,
                member_order_before=["a", "b"],
                member_order_after=["a", "b"],
                padding_saved=0,
                should_optimize=False,
                skip_reason="Circular dependency detected"
            )],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_no_dependencies(self, tmp_path):
        """Test no dependencies, can optimize freely."""
        test_case = E2ETestCase(
            name="no_dependencies",
            cpp_code="""struct Free { char a; int b; char c; Free(int x, char y, char z) : a(y), b(x), c(z) {} }; int main() { Free f(42, 'x', 'y'); return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[StructExpectation(
                name="Free",
                size_before=12,
                size_after=8,
                member_order_before=["a", "b", "c"],
                member_order_after=["b", "a", "c"],
                padding_saved=4,
                should_optimize=True
            )],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_prevents_optimization(self, tmp_path):
        """Test dependencies make optimization impossible."""
        test_case = E2ETestCase(
            name="prevents_optimization",
            cpp_code="""struct Locked { char flag; int size; char* buffer; Locked(int s) : flag(1), size(s), buffer(size > 0 ? new char[size] : nullptr) {} }; int main() { Locked l(100); return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[StructExpectation(
                name="Locked",
                size_before=24,
                size_after=24,
                member_order_before=["flag", "size", "buffer"],
                member_order_after=["flag", "size", "buffer"],
                padding_saved=0,
                should_optimize=False,
                skip_reason="Constructor dependency prevents optimization"
            )],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_partial_optimization(self, tmp_path):
        """Test some members can move, others locked."""
        test_case = E2ETestCase(
            name="partial_optimization",
            cpp_code="""struct Partial { char free1; int size; char* buffer; char free2; Partial(int s) : size(s), buffer(new char[size]), free1('a'), free2('b') {} }; int main() { Partial p(50); return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[StructExpectation(
                name="Partial",
                size_before=24,  # char + pad(3) + int + char* + char + pad(7)
                size_after=24,   # No optimization due to dependencies
                member_order_before=["free1", "size", "buffer", "free2"],
                member_order_after=["free1", "size", "buffer", "free2"],  # Can't reorder due to buffer depending on size
                padding_saved=0,
                should_optimize=False,
                skip_reason="constructor dependencies"
            )],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_detection_in_expression(self, tmp_path):
        """Test detect member use in complex expressions."""
        test_case = E2ETestCase(
            name="complex_expression",
            cpp_code="""struct Complex { int width; int height; int area; int* data; Complex(int w, int h) : width(w), height(h), area(width * height), data(new int[area]) {} }; int main() { Complex c(10, 20); return 0; }""",
            flags={'extractor': 'dwarf'},
            expected_structs=[StructExpectation(
                name="Complex",
                size_before=32,
                size_after=32,
                member_order_before=["width", "height", "area", "data"],
                member_order_after=["width", "height", "area", "data"],
                padding_saved=0,
                should_optimize=False,
                skip_reason="Complex constructor dependencies prevent optimization"
            )],
            should_succeed=True
        )
        self.run_test_case(test_case, tmp_path)