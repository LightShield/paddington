"""E2E tests for basic functionality."""

import pytest
from pathlib import Path
from .base_e2e import BaseE2ETest


class TestBasicFunctionality(BaseE2ETest):
    """Basic functionality e2e tests."""
    
    @pytest.mark.e2e
    def test_simple_struct_dry_run(self, tmp_path):
        """Test simple struct in dry-run mode (default)."""
        code = """
        struct Simple {
            char a;
            int b;
            char c;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file, verbose=True)
        self.assert_success(result)
        self.assert_output_contains(result, "DRY-RUN")
        # TODO: Verify structs were extracted and analyzed
        # self.assert_output_contains(result, "Total structs:")
    
    @pytest.mark.e2e
    def test_simple_struct_with_patch(self, tmp_path):
        """Test patch generation."""
        code = """
        struct Data {
            char flag;
            int id;
            double score;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        patch_dir = tmp_path / "patches"
        result = self.run_optimize(obj_file, output="patch", patch_dir=str(patch_dir))
        self.assert_success(result)
        # TODO: Verify patches were actually generated
        # if patch_dir.exists():
        #     patches = list(patch_dir.glob("*.patch"))
        #     assert len(patches) > 0, "No patches generated"
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        patch_dir = tmp_path / "patches"
        result = self.run_optimize(obj_file, output="patch", patch_dir=str(patch_dir))
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_simple_struct_with_file_output(self, tmp_path):
        """Test direct file modification."""
        code = """
        struct Data {
            char a;
            int b;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file, apply=True, output="file")
        self.assert_success(result)
    
    @pytest.mark.e2e
    def test_min_savings_threshold(self, tmp_path):
        """Test minimum savings threshold."""
        code = """
        struct Small {
            char a;
            short b;
        };
        int main() { return 0; }
        """
        obj_file = self.compile_cpp(code, tmp_path)
        result = self.run_optimize(obj_file, min_savings=100)  # High threshold
        self.assert_success(result)
        # Should skip due to threshold
    
    @pytest.mark.e2e
    def test_help_documentation(self):
        """Test help documentation."""
        import subprocess
        result = subprocess.run(
            ['python', '__main__.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        assert result.returncode == 0
        assert "--apply" in result.stdout
        assert "--min-savings" in result.stdout
