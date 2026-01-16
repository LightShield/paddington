"""Tests for GitPatchGenerator."""

import pytest
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from implementation.pipeline.output import GitPatchGenerator
from implementation.pipeline.output.patch_generator import AppliedChange
from implementation.struct_data import TransformedSource, SourceModification, Modification, Location


@pytest.mark.unit
class TestGitPatchGeneratorUnit:
    """Unit tests for GitPatchGenerator."""
    
    def test_init(self):
        """Test GitPatchGenerator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            assert generator.output_dir == Path(temp_dir)
            assert generator.output_dir.exists()
    
    def test_supports_dry_run(self):
        """Test that GitPatchGenerator supports dry run."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            assert generator.supports_dry_run() is True
    
    def test_apply_empty_list(self):
        """Test applying empty transformation list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            result = generator.apply([])
            assert result == []
    
    def test_build_dependency_order(self):
        """Test dependency order building."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            
            transformed = [
                TransformedSource(
                    file_path="test.cpp",
                    original_content="old",
                    new_content="new",
                    modifications=(
                        SourceModification(
                            file_path="test.cpp",
                            struct_name="Outer",
                            modifications=()
                        ),
                        SourceModification(
                            file_path="test.cpp", 
                            struct_name="Inner",
                            modifications=()
                        )
                    )
                )
            ]
            
            order = generator._build_dependency_order(transformed)
            assert order == ["Inner", "Outer"]  # Alphabetical order
    
    def test_generate_commit_message(self):
        """Test commit message generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            
            source = TransformedSource(
                file_path="test.cpp",
                original_content="line1\nline2\nline3\n",
                new_content="line1\nline2\n",
                modifications=()
            )
            
            message = generator._generate_commit_message(source, "TestStruct")
            
            assert "refactor: Optimize padding for TestStruct" in message
            assert "Reorder members from largest to smallest" in message
            assert "Saves 4 bytes per instance" in message
            assert "Before: 16 bytes" in message
            assert "After: 12 bytes" in message
    
    def test_patch_naming_convention(self):
        """Test patch file naming follows struct_NNN_StructName.patch format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            
            # Mock subprocess to avoid actual git calls
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(stdout="diff content", returncode=0)
                
                patch_path, message_path = generator._generate_patch(
                    TransformedSource(
                        file_path="test.cpp",
                        original_content="old",
                        new_content="new", 
                        modifications=()
                    ),
                    "TestStruct",
                    0
                )
                
                assert patch_path.name == "struct_000_TestStruct.patch"
                assert message_path.name == "struct_000_TestStruct.msg"
    
    def test_create_apply_order(self):
        """Test APPLY_ORDER.txt creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            
            changes = [
                AppliedChange(
                    file_path="test.cpp",
                    timestamp=datetime.now(),
                    patch_path=str(Path(temp_dir) / "struct_000_Inner.patch"),
                    message_path=str(Path(temp_dir) / "struct_000_Inner.msg")
                ),
                AppliedChange(
                    file_path="test.cpp", 
                    timestamp=datetime.now(),
                    patch_path=str(Path(temp_dir) / "struct_001_Outer.patch"),
                    message_path=str(Path(temp_dir) / "struct_001_Outer.msg")
                )
            ]
            
            generator._create_apply_order(changes)
            
            order_file = Path(temp_dir) / "APPLY_ORDER.txt"
            assert order_file.exists()
            
            content = order_file.read_text()
            assert "1. struct_000_Inner.patch" in content
            assert "2. struct_001_Outer.patch" in content


@pytest.mark.integration
class TestGitPatchGeneratorIntegration:
    """Integration tests for GitPatchGenerator."""
    
    def test_generate_real_patch(self):
        """Test generating actual git patches."""
        # Check if git is available
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Git not available")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            
            original_content = """struct TestStruct {
    char a;
    int b;
    char c;
};"""
            
            new_content = """struct TestStruct {
    int b;
    char a;
    char c;
};"""
            
            transformed = [
                TransformedSource(
                    file_path="test.cpp",
                    original_content=original_content,
                    new_content=new_content,
                    modifications=(
                        SourceModification(
                            file_path="test.cpp",
                            struct_name="TestStruct",
                            modifications=(
                                Modification(
                                    type="reorder",
                                    location=Location("test.cpp", 1, 0),
                                    old_content="char a;\n    int b;\n    char c;",
                                    new_content="int b;\n    char a;\n    char c;"
                                ),
                            )
                        ),
                    )
                )
            ]
            
            result = generator.apply(transformed)
            
            assert len(result) == 1
            assert result[0].file_path == "test.cpp"
            assert isinstance(result[0].timestamp, datetime)
            
            # Check patch file exists and has content
            patch_path = Path(result[0].patch_path)
            assert patch_path.exists()
            assert patch_path.stat().st_size > 0
            
            # Check message file exists and has content
            message_path = Path(result[0].message_path)
            assert message_path.exists()
            assert message_path.stat().st_size > 0
            
            # Check APPLY_ORDER.txt exists
            order_file = Path(temp_dir) / "APPLY_ORDER.txt"
            assert order_file.exists()
    
    def test_multiple_structs_dependency_order(self):
        """Test patch generation with multiple structs in dependency order."""
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Git not available")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            
            transformed = [
                TransformedSource(
                    file_path="test.cpp",
                    original_content="struct Inner { char a; int b; };\nstruct Outer { Inner inner; char c; };",
                    new_content="struct Inner { int b; char a; };\nstruct Outer { char c; Inner inner; };",
                    modifications=(
                        SourceModification(
                            file_path="test.cpp",
                            struct_name="Inner",
                            modifications=()
                        ),
                        SourceModification(
                            file_path="test.cpp",
                            struct_name="Outer", 
                            modifications=()
                        )
                    )
                )
            ]
            
            result = generator.apply(transformed)
            
            assert len(result) == 2
            
            # Check patch files follow naming convention
            patch_names = [Path(change.patch_path).name for change in result]
            assert "struct_000_Inner.patch" in patch_names
            assert "struct_001_Outer.patch" in patch_names
            
            # Check APPLY_ORDER.txt has correct order
            order_file = Path(temp_dir) / "APPLY_ORDER.txt"
            content = order_file.read_text()
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            assert lines[0] == "1. struct_000_Inner.patch"
            assert lines[1] == "2. struct_001_Outer.patch"


@pytest.mark.unit
class TestGitPatchGeneratorErrorHandling:
    """Test error handling in GitPatchGenerator."""
    
    def test_git_not_available(self):
        """Test behavior when git is not available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = FileNotFoundError("git not found")
                
                with pytest.raises(FileNotFoundError):
                    generator._generate_patch(
                        TransformedSource(
                            file_path="test.cpp",
                            original_content="old",
                            new_content="new",
                            modifications=()
                        ),
                        "TestStruct",
                        0
                    )
    
    def test_invalid_output_directory(self):
        """Test handling of invalid output directory."""
        # Test with non-existent parent directory
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_path = Path(temp_dir) / "non_existent" / "subdir"
            generator = GitPatchGenerator(non_existent_path)
            assert generator.output_dir == non_existent_path
            assert generator.output_dir.exists()
    
    def test_git_diff_failure(self):
        """Test handling of git diff command failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = GitPatchGenerator(Path(temp_dir))
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="git error", stdout="")
                
                # Should not raise exception, but create empty patch
                patch_path, message_path = generator._generate_patch(
                    TransformedSource(
                        file_path="test.cpp",
                        original_content="old",
                        new_content="new",
                        modifications=()
                    ),
                    "TestStruct",
                    0
                )
                
                assert patch_path.exists()
                assert message_path.exists()
                # Patch should be empty due to git failure
                assert patch_path.read_text() == ""