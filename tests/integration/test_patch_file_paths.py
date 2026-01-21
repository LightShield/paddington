"""Test that generated patches have correct file paths."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.output import GitPatchGenerator
from implementation.struct_data import TransformedSource


@pytest.mark.integration
class TestPatchFilePaths:
    """Test that patches contain actual source file paths, not temp paths."""
    
    def test_patch_contains_actual_file_paths(self):
        """Test that generated patch uses actual source file paths.
        
        BUG: GitPatchGenerator uses temp files for git diff, resulting in
        patches with paths like 'tmp/tmpXXX.cpp' instead of actual source paths.
        
        This makes patches unapplicable to the source repository.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a transformed source
            source_file = "common/caml/logging/al_report.h"
            transformed = TransformedSource(
                file_path=source_file,
                original_content="class Test { int a; double b; };",
                new_content="class Test { double b; int a; };",
                modifications=()
            )
            
            # Generate patch
            patch_dir = tmpdir / "patches"
            patch_dir.mkdir()
            generator = GitPatchGenerator(output_dir=patch_dir)
            changes = generator.apply([transformed])
            
            assert len(changes) > 0, "No patches generated"
            
            # Read the patch file
            patch_files = list(patch_dir.glob("*.patch"))
            assert len(patch_files) > 0, "No .patch files created"
            
            patch_content = patch_files[0].read_text()
            
            # BUG: Patch contains temp paths like 'tmp/tmpXXX.cpp'
            assert 'tmp/tmp' not in patch_content, \
                "Patch contains temp file paths - should use actual source paths"
            
            # Should contain actual source path
            assert source_file in patch_content or 'al_report.h' in patch_content, \
                f"Patch should contain actual source path '{source_file}'"
            
            # Check diff header format
            assert f'a/{source_file}' in patch_content or 'a/al_report.h' in patch_content, \
                "Patch should have proper git diff format with source path"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
