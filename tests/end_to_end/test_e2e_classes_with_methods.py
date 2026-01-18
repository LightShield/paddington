"""E2E tests for classes with methods (critical bug prevention)."""

import pytest
from .base_e2e import BaseE2ETest, E2ETestCase, StructExpectation


class TestClassesWithMethods(BaseE2ETest):
    """Tests to prevent regression of method deletion bug."""
    
    @pytest.mark.e2e
    def test_class_with_methods_preserved(self, tmp_path):
        """Test that methods are preserved during optimization.
        
        Verifies: FR-1.1.3 (Source Transformation - Method Preservation)
        
        CRITICAL: This test prevents the bug where rewriter deleted all methods.
        """
        test_case = E2ETestCase(
            name="class_with_methods",
            cpp_code="""
            class TestClass {
            private:
                char a;
                int b;
            public:
                void method1() { }
                void method2() { }
                int get_b() { return b; }
            };
            
            int main() {
                TestClass t;
                return 0;
            }
            """,
            flags={'apply': True, 'output': 'file', 'extractor': 'dwarf', 'transformer': 'line-swap'},
            expected_structs=[
                StructExpectation(
                    name="TestClass",
                    size_before=8,
                    size_after=8,
                    member_order_before=['a', 'b'],
                    member_order_after=['b', 'a'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"]
        )
        self.run_test_case(test_case, tmp_path)
        
        # CRITICAL: Verify methods are still in the file
        cpp_file = tmp_path / "test.cpp"
        if cpp_file.exists():
            content = cpp_file.read_text()
            assert 'void method1()' in content, "method1 was deleted!"
            assert 'void method2()' in content, "method2 was deleted!"
            assert 'int get_b()' in content, "get_b was deleted!"
    
    @pytest.mark.e2e
    def test_class_with_many_methods(self, tmp_path):
        """Test class with many methods (like al_report with 50+ methods).
        
        Verifies: FR-1.1.3 (Source Transformation - Large Classes)
        """
        test_case = E2ETestCase(
            name="class_with_many_methods",
            cpp_code="""
            class LargeClass {
            private:
                char flag;
                int id;
                double value;
            public:
                void method1() { }
                void method2() { }
                void method3() { }
                void method4() { }
                void method5() { }
                int get_id() { return id; }
                double get_value() { return value; }
                void set_flag(char f) { flag = f; }
            };
            
            int main() {
                LargeClass c;
                return 0;
            }
            """,
            flags={'apply': True, 'output': 'file', 'extractor': 'dwarf', 'transformer': 'line-swap'},
            expected_structs=[
                StructExpectation(
                    name="LargeClass",
                    size_before=16,
                    size_after=16,
                    member_order_before=['flag', 'id', 'value'],
                    member_order_after=['value', 'id', 'flag'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"]
        )
        self.run_test_case(test_case, tmp_path)
        
        # Verify all methods preserved
        cpp_file = tmp_path / "test.cpp"
        if cpp_file.exists():
            content = cpp_file.read_text()
            for i in range(1, 6):
                assert f'void method{i}()' in content, f"method{i} was deleted!"
            assert 'int get_id()' in content
            assert 'double get_value()' in content
            assert 'void set_flag(' in content
    
    @pytest.mark.e2e
    def test_class_with_nested_types(self, tmp_path):
        """Test class with nested types preserved.
        
        Verifies: FR-1.1.3 (Source Transformation - Nested Types)
        """
        test_case = E2ETestCase(
            name="class_with_nested",
            cpp_code="""
            class WithNested {
            public:
                enum Type { A, B, C };
                typedef int ID;
            private:
                char flag;
                int id;
            public:
                Type get_type() { return A; }
            };
            
            int main() {
                WithNested w;
                return 0;
            }
            """,
            flags={'apply': True, 'output': 'file', 'extractor': 'dwarf', 'transformer': 'line-swap'},
            expected_structs=[
                StructExpectation(
                    name="WithNested",
                    size_before=8,
                    size_after=8,
                    member_order_before=['flag', 'id'],
                    member_order_after=['id', 'flag'],
                    padding_saved=0,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"]
        )
        self.run_test_case(test_case, tmp_path)
        
        # Verify nested types preserved
        cpp_file = tmp_path / "test.cpp"
        if cpp_file.exists():
            content = cpp_file.read_text()
            assert 'enum Type' in content, "enum was deleted!"
            assert 'typedef int ID' in content, "typedef was deleted!"
            assert 'Type get_type()' in content, "method was deleted!"
