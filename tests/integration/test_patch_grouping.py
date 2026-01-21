"""Test for grouping patches by file, not by struct."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.output import GitPatchGenerator
from implementation.struct_data import TransformedSource


@pytest.mark.integration
class TestPatchGroupingByFile:
    """Test that patches are grouped by file, not by struct."""
    
    def test_multiple_structs_same_file_one_patch(self):
        """Test that multiple structs in same file generate ONE patch.
        
        Scenario: File has 3 structs, all optimized
        Current bug: Generates 3 identical patches
        Expected: Generate 1 patch with all changes
        """
        # Same file, 3 different structs
        sources = [
            TransformedSource(
                file_path="common/test.h",
                original_content="struct A { int a; }; struct B { int b; }; struct C { int c; };",
                new_content="struct A { int a; }; struct B { int b; }; struct C { int c; };",  # Same for simplicity
                modifications=()
            ),
            TransformedSource(
                file_path="common/test.h",
                original_content="struct A { int a; }; struct B { int b; }; struct C { int c; };",
                new_content="struct A { int a; }; struct B { int b; }; struct C { int c; };",
                modifications=()
            ),
            TransformedSource(
                file_path="common/test.h",
                original_content="struct A { int a; }; struct B { int b; }; struct C { int c; };",
                new_content="struct A { int a; }; struct B { int b; }; struct C { int c; };",
                modifications=()
            ),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_dir = Path(tmpdir) / "patches"
            patch_dir.mkdir()
            generator = GitPatchGenerator(output_dir=patch_dir)
            changes = generator.apply(sources)
            
            patch_files = list(patch_dir.glob("*.patch"))
            
            # Should generate 1 patch, not 3
            assert len(patch_files) == 1, \
                f"Expected 1 patch for common/test.h, got {len(patch_files)}"
    
    def test_h_and_cpp_combined_one_patch(self):
        """Test that .h and .cpp for same struct are in ONE patch."""
        sources = [
            TransformedSource(
                file_path="common/test.h",
                original_content="class Test { int a; };",
                new_content="class Test { int a; };",
                modifications=()
            ),
            TransformedSource(
                file_path="common/test.cpp",
                original_content="Test::Test() : a(1) {}",
                new_content="Test::Test() : a(1) {}",
                modifications=()
            ),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_dir = Path(tmpdir) / "patches"
            patch_dir.mkdir()
            generator = GitPatchGenerator(output_dir=patch_dir)
            changes = generator.apply(sources)
            
            patch_files = list(patch_dir.glob("*.patch"))
            
            # Should generate 1 combined patch
            assert len(patch_files) == 1, \
                f"Expected 1 combined patch, got {len(patch_files)}"
            
            # Patch should contain both files
            patch_content = patch_files[0].read_text()
            assert "test.h" in patch_content
            assert "test.cpp" in patch_content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
