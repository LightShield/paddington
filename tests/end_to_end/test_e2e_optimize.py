"""End-to-end tests for optimize functionality."""

import pytest
import tempfile
from pathlib import Path
from .base_e2e import BaseE2ETest


class TestOptimizeE2E(BaseE2ETest):
    """E2E tests for optimize functionality."""

    @pytest.mark.e2e
    def test_default_dry_run_behavior(self):
        """Test that default behavior is dry-run."""
        cpp_code = """
        struct Simple {
            char a;
            int b;
            char c;
        };
        
        int main() {
            Simple s;
            return 0;
        }
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            obj_file = self.compile_cpp(cpp_code, tmpdir)
            result = self.run_optimize(obj_file, extractor='dwarf', verbose=True)
            
            self.assert_success(result)
            self.assert_output_contains(result, "Found")

    @pytest.mark.e2e
    def test_optimize_with_apply_flag(self):
        """Test optimize command with --apply flag."""
        cpp_code = """
        struct Data {
            char flag;
            int id;
            double score;
        };
        
        int main() { return 0; }
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            obj_file = self.compile_cpp(cpp_code, tmpdir)
            patch_dir = Path(tmpdir) / "patches"
            
            result = self.run_optimize(
                obj_file,
                apply=True,
                extractor='dwarf',
                transformer='line-swap',
                output='patch',
                patch_dir=patch_dir
            )
            
            self.assert_success(result)

    @pytest.mark.e2e
    def test_optimize_access_modifier_strategies(self):
        """Test optimize with different access modifier strategies."""
        cpp_code = """
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
        
        with tempfile.TemporaryDirectory() as tmpdir:
            obj_file = self.compile_cpp(cpp_code, tmpdir)
            
            # Test each strategy
            for strategy in ['preserve', 'split', 'ignore']:
                result = self.run_optimize(
                    obj_file,
                    access_modifier_strategy=strategy,
                    extractor='dwarf'
                )
                
                self.assert_success(result)

    @pytest.mark.e2e
    def test_optimize_help_output(self):
        """Test optimize command help output."""
        import subprocess
        
        result = subprocess.run(
            ['python', '__main__.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        self.assert_success(result)
        self.assert_output_contains(result, "paddingTON")
        self.assert_output_contains(result, "--apply")
        self.assert_output_contains(result, "--access-modifier-strategy")