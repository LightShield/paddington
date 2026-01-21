"""Test for combining .h and .cpp patches for same struct."""

import pytest
import tempfile
from pathlib import Path
from implementation.pipeline.output import GitPatchGenerator
from implementation.struct_data import TransformedSource


@pytest.mark.integration
class TestCombinedPatches:
    """Test that .h and .cpp changes for same struct are in one patch."""
    
    def test_single_patch_for_h_and_cpp(self):
        """Test that changes to .h and .cpp for same struct generate ONE patch.
        
        Current behavior: Generates 2 separate patches
        - struct_000_MyStruct.patch (for .h file)
        - struct_001_MyStruct.patch (for .cpp file)
        
        Expected behavior: Generate 1 combined patch
        - struct_000_MyStruct.patch (contains both .h and .cpp changes)
        
        This makes patches easier to apply and keeps related changes together.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create two transformed sources for same struct
            h_file = TransformedSource(
                file_path="common/caml/test/MyStruct.h",
                original_content="class MyStruct { int a; double b; };",
                new_content="class MyStruct { double b; int a; };",
                modifications=()
            )
            
            cpp_file = TransformedSource(
                file_path="common/caml/test/MyStruct.cpp",
                original_content="MyStruct::MyStruct() : a(1), b(2.0) {}",
                new_content="MyStruct::MyStruct() : b(2.0), a(1) {}",
                modifications=()
            )
            
            # Generate patches
            patch_dir = tmpdir / "patches"
            patch_dir.mkdir()
            generator = GitPatchGenerator(output_dir=patch_dir)
            changes = generator.apply([h_file, cpp_file])
            
            # Current behavior: 2 patches
            # Expected behavior: 1 patch
            patch_files = list(patch_dir.glob("*.patch"))
            
            # THIS WILL FAIL with current implementation
            assert len(patch_files) == 1, \
                f"Expected 1 combined patch for MyStruct, got {len(patch_files)} separate patches"
            
            # The single patch should contain both files
            if len(patch_files) == 1:
                patch_content = patch_files[0].read_text()
                assert "MyStruct.h" in patch_content, "Patch should include .h changes"
                assert "MyStruct.cpp" in patch_content, "Patch should include .cpp changes"
                assert patch_content.count("diff --git") == 2, "Patch should have 2 diff sections"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
