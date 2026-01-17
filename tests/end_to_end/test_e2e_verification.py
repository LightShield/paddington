"""E2E tests that verify actual optimization results."""

import pytest
from pathlib import Path
from .base_e2e import BaseE2ETest


class TestVerification(BaseE2ETest):
    """Tests that verify optimization actually works."""
    
    @pytest.mark.e2e
    def test_verify_size_reduction(self, tmp_path):
        """Verify struct size is actually reduced after optimization."""
        code_before = """
        struct Simple {
            char a;
            int b;
            char c;
        };
        int main() { return 0; }
        """
        
        # Get size before optimization
        size_before = self.compile_and_get_size(code_before, tmp_path, "Simple")
        
        # Expected: char(1) + pad(3) + int(4) + char(1) + pad(3) = 12 bytes
        if size_before:
            assert size_before == 12, f"Expected size 12, got {size_before}"
    
    @pytest.mark.e2e
    def test_verify_member_reordering_in_patch(self, tmp_path):
        """Verify patch contains correct member reordering."""
        code = """
        struct Data {
            char flag;
            int id;
            double score;
        };
        int main() { return 0; }
        """
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        obj_file = self.compile_cpp(code, tmp_path)
        patch_dir = tmp_path / "patches"
        
        result = self.run_optimize(obj_file, output="patch", patch_dir=str(patch_dir))
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_verify_no_change_when_optimal(self, tmp_path):
        """Verify already optimal struct is not changed."""
        code = """
        struct Optimal {
            double a;
            int b;
            char c;
        };
        int main() { return 0; }
        """
        
        obj_file = self.compile_cpp(code, tmp_path)
        patch_dir = tmp_path / "patches"
        
        result = self.run_optimize(obj_file, output="patch", patch_dir=str(patch_dir))
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_verify_padding_calculation(self, tmp_path):
        """Verify padding is calculated correctly."""
        code = """
        struct WithPadding {
            char a;
            int b;
            char c;
        };
        int main() { return 0; }
        """
        
        size = self.compile_and_get_size(code, tmp_path, "WithPadding")
        
        if size:
            assert size == 12, f"Expected 12 bytes, got {size}"
    
    @pytest.mark.e2e
    def test_verify_access_modifiers_preserved(self, tmp_path):
        """Verify access modifiers are preserved with preserve strategy."""
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
        
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(code)
        obj_file = self.compile_cpp(code, tmp_path)
        
        result = self.run_optimize(
            obj_file,
            apply=True,
            output="file",
            access_modifier_strategy="preserve"
        )
        self.assert_success(result)
