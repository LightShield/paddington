"""E2E tests for access modifier strategies."""

import pytest
from .base_e2e import BaseE2ETest


class TestAccessModifiers(BaseE2ETest):
    """Access modifier strategy e2e tests."""
    
    @pytest.mark.e2e
    def test_preserve_strategy_public_private(self, tmp_path):
        """Test preserve strategy with public/private sections."""
        code = """
        class Data {
        public:
            char a;
            int b;
        private:
            char c;
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file, access_modifier_strategy="preserve")
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_preserve_strategy_multiple_sections(self, tmp_path):
        """Test preserve with multiple public/private sections."""
        code = """
        class Data {
        public:
            char a;
        private:
            int b;
        public:
            char c;
        private:
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file, access_modifier_strategy="preserve")
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_split_strategy_optimal_ordering(self, tmp_path):
        """Test split strategy for optimal ordering."""
        code = """
        class Data {
        public:
            char a;
            int b;
        private:
            char c;
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file, access_modifier_strategy="split")
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_split_strategy_per_member_modifiers(self, tmp_path):
        """Test split strategy adds per-member modifiers."""
        code = """
        class Mixed {
        public:
            char small;
        private:
            double large;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file, access_modifier_strategy="split")
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_ignore_strategy_breaks_encapsulation(self, tmp_path):
        """Test ignore strategy reorders across sections."""
        code = """
        class Data {
        public:
            char a;
        private:
            double d;
        public:
            int b;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file, access_modifier_strategy="ignore")
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_struct_only_no_class_modifiers(self, tmp_path):
        """Test struct optimization (no access modifiers)."""
        code = """
        struct Data {
            char a;
            int b;
            char c;
            double d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
