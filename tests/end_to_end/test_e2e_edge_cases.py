"""E2E tests for edge cases."""

import pytest
from .base_e2e import BaseE2ETest


class TestEdgeCases(BaseE2ETest):
    """Edge case e2e tests."""
    
    @pytest.mark.e2e
    def test_empty_struct(self, tmp_path):
        """Test empty struct."""
        code = """
        struct Empty {};
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # Should skip empty structs
    
    @pytest.mark.e2e
    def test_single_member_struct(self, tmp_path):
        """Test struct with single member."""
        code = """
        struct Single {
            int value;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # No reordering possible
    
    @pytest.mark.e2e
    def test_already_optimal_struct(self, tmp_path):
        """Test struct already optimally ordered."""
        code = """
        struct Optimal {
            double a;
            int b;
            char c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # Should skip (no padding to save)
    
    @pytest.mark.e2e
    def test_zero_size_members(self, tmp_path):
        """Test struct with zero-size members (empty base)."""
        code = """
        struct Empty {};
        struct WithEmpty {
            Empty e;
            char a;
            int b;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_padding_only_at_end(self, tmp_path):
        """Test struct with padding only at end."""
        code = """
        struct EndPadding {
            int a;
            int b;
            char c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_no_padding_possible(self, tmp_path):
        """Test struct where no padding reduction is possible."""
        code = """
        struct NoPadding {
            int a;
            int b;
            int c;
            int d;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file)
        self.assert_success(result)
        # All same size, no optimization possible
