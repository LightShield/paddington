import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestE2EDependencyFamily(BaseE2ETest):
    """Verifies: FR-1.1.4"""
    
    @pytest.mark.e2e
    def test_dependency_three_levels(self, tmp_path):
        """Verifies: FR-1.1.4 - Test three-level dependency chain A → B → C."""
        test_case = E2ETestCase(
            name="dependency_three_levels",
            cpp_code="""
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
""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="A", size_before=4, size_after=4,
                    member_order_before=["value"], member_order_after=["value"],
                    padding_saved=0, should_optimize=False
                ),
                StructExpectation(
                    name="B", size_before=8, size_after=8,
                    member_order_before=["a", "extra"], member_order_after=["a", "extra"],
                    padding_saved=0, should_optimize=False
                ),
                StructExpectation(
                    name="C", size_before=12, size_after=12,
                    member_order_before=["b", "final"], member_order_after=["b", "final"],
                    padding_saved=0, should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_four_levels(self, tmp_path):
        """Verifies: FR-1.1.4 - Test four-level dependency chain A → B → C → D."""
        test_case = E2ETestCase(
            name="dependency_four_levels",
            cpp_code="""
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
""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="D", size_before=16, size_after=16,
                    member_order_before=["c", "final"], member_order_after=["c", "final"],
                    padding_saved=0, should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_diamond(self, tmp_path):
        """Verifies: FR-1.1.4 - Test diamond dependency pattern Base → Left/Right → Top."""
        test_case = E2ETestCase(
            name="dependency_diamond",
            cpp_code="""
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
""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Top", size_before=20, size_after=20,
                    member_order_before=["left", "right", "top_data"], member_order_after=["left", "right", "top_data"],
                    padding_saved=0, should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_size_propagation(self, tmp_path):
        """Verifies: FR-1.1.4 - Test size propagation through dependency chain."""
        test_case = E2ETestCase(
            name="dependency_size_propagation",
            cpp_code="""
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
""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Large", size_before=24, size_after=24,
                    member_order_before=["medium1", "medium2", "data"], member_order_after=["medium1", "medium2", "data"],
                    padding_saved=0, should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_circular_pointers(self, tmp_path):
        """Verifies: FR-1.1.4 - Test circular dependency with pointers A ↔ B."""
        test_case = E2ETestCase(
            name="dependency_circular_pointers",
            cpp_code="""
struct B;

struct A {
    B* b_ptr;
    int value;
};

struct B {
    A* a_ptr;
    int data;
};
""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="A", size_before=16, size_after=16,
                    member_order_before=["b_ptr", "value"], member_order_after=["b_ptr", "value"],
                    padding_saved=0, should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_self_reference(self, tmp_path):
        """Verifies: FR-1.1.4 - Test self-referencing struct with pointer."""
        test_case = E2ETestCase(
            name="dependency_self_reference",
            cpp_code="""
struct Node {
    Node* next;
    int data;
};
""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Node", size_before=16, size_after=16,
                    member_order_before=["next", "data"], member_order_after=["next", "data"],
                    padding_saved=0, should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_mutual_recursion(self, tmp_path):
        """Verifies: FR-1.1.4 - Test mutual recursion A → B → C → A."""
        test_case = E2ETestCase(
            name="dependency_mutual_recursion",
            cpp_code="""
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
""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="A", size_before=16, size_after=16,
                    member_order_before=["b_ptr", "value"], member_order_after=["b_ptr", "value"],
                    padding_saved=0, should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)

    @pytest.mark.e2e
    def test_dependency_optimization_order(self, tmp_path):
        """Verifies: FR-1.1.4 - Test optimization order with mixed dependencies."""
        test_case = E2ETestCase(
            name="dependency_optimization_order",
            cpp_code="""
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
""",
            flags={'extractor': 'dwarf'},
            expected_structs=[
                StructExpectation(
                    name="Root", size_before=20, size_after=20,
                    member_order_before=["branch1", "branch2", "root_data"], member_order_after=["branch1", "branch2", "root_data"],
                    padding_saved=0, should_optimize=False
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"]
        )
        self.run_test_case(test_case, tmp_path)