"""Unit and integration tests for DirectFileWriter."""

import os
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open
from implementation.pipeline.output import DirectFileWriter, DirectFileWriterAppliedChange
from implementation.struct_data import TransformedSource


@pytest.mark.unit
class TestDirectFileWriterUnit:
    """Unit tests for DirectFileWriter."""
    
    def test_init_default(self):
        """Test default initialization."""
        writer = DirectFileWriter()
        assert writer.supports_dry_run() is True
    
    def test_init_dry_run(self):
        """Test dry run initialization."""
        writer = DirectFileWriter(dry_run=True)
        assert writer.supports_dry_run() is True
    
    def test_supports_dry_run(self):
        """Test dry run support."""
        writer = DirectFileWriter()
        assert writer.supports_dry_run() is True
    
    def test_apply_dry_run_mode(self):
        """Test apply in dry run mode."""
        writer = DirectFileWriter(dry_run=True)
        transformed = [
            TransformedSource(
                file_path="test.cpp",
                original_content="old content",
                new_content="new content",
                modifications=()
            )
        ]
        
        result = writer.apply(transformed)
        
        assert len(result) == 1
        assert result[0].file_path == "test.cpp"
        assert result[0].backup_path == "test.cpp.backup"
        assert isinstance(result[0].timestamp, datetime)
        assert isinstance(result[0], DirectFileWriterAppliedChange)
    
    def test_apply_empty_list(self):
        """Test applying empty transformation list."""
        writer = DirectFileWriter(dry_run=True)
        result = writer.apply([])
        assert result == []
    
    def test_backup_path_generation(self):
        """Test backup path generation logic."""
        writer = DirectFileWriter()
        file_path = Path("test.cpp")
        
        # Test non-existent file
        backup_path = writer._create_backup(file_path)
        assert backup_path == "test.cpp.backup"
    
    @patch('os.access')
    def test_validate_writable_existing_file_writable(self, mock_access):
        """Test validation of writable existing file."""
        mock_access.return_value = True
        writer = DirectFileWriter()
        
        with patch.object(Path, 'exists', return_value=True):
            writer._validate_writable(Path("test.cpp"))  # Should not raise
    
    @patch('os.access')
    def test_validate_writable_existing_file_not_writable(self, mock_access):
        """Test validation of non-writable existing file."""
        mock_access.return_value = False
        writer = DirectFileWriter()
        
        with patch.object(Path, 'exists', return_value=True):
            with pytest.raises(PermissionError, match="File not writable"):
                writer._validate_writable(Path("test.cpp"))
    
    @patch('os.access')
    def test_validate_writable_new_file_writable_dir(self, mock_access):
        """Test validation of new file in writable directory."""
        mock_access.return_value = True
        writer = DirectFileWriter()
        
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'mkdir'):
                writer._validate_writable(Path("test.cpp"))  # Should not raise
    
    @patch('os.access')
    def test_validate_writable_new_file_not_writable_dir(self, mock_access):
        """Test validation of new file in non-writable directory."""
        mock_access.return_value = False
        writer = DirectFileWriter()
        
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'mkdir'):
                with pytest.raises(PermissionError, match="Directory not writable"):
                    writer._validate_writable(Path("test.cpp"))


@pytest.mark.integration
class TestDirectFileWriterIntegration:
    """Integration tests for DirectFileWriter."""
    
    def test_write_new_file(self):
        """Test writing a new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DirectFileWriter()
            file_path = Path(temp_dir) / "test.cpp"
            content = "int main() { return 0; }"
            
            transformed = [
                TransformedSource(
                    file_path=str(file_path),
                    original_content="",
                    new_content=content,
                    modifications=()
                )
            ]
            
            result = writer.apply(transformed)
            
            assert len(result) == 1
            assert result[0].file_path == str(file_path)
            assert result[0].backup_path == str(file_path) + ".backup"
            assert file_path.exists()
            assert file_path.read_text() == content
    
    def test_overwrite_existing_file_with_backup(self):
        """Test overwriting existing file creates backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DirectFileWriter()
            file_path = Path(temp_dir) / "test.cpp"
            original_content = "original content"
            new_content = "new content"
            
            # Create original file
            file_path.write_text(original_content)
            
            transformed = [
                TransformedSource(
                    file_path=str(file_path),
                    original_content=original_content,
                    new_content=new_content,
                    modifications=()
                )
            ]
            
            result = writer.apply(transformed)
            
            assert len(result) == 1
            backup_path = Path(result[0].backup_path)
            
            # Check original file is updated
            assert file_path.read_text() == new_content
            
            # Check backup exists with original content
            assert backup_path.exists()
            assert backup_path.read_text() == original_content
    
    def test_write_multiple_files(self):
        """Test writing multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DirectFileWriter()
            
            files = [
                (Path(temp_dir) / "test1.cpp", "content1"),
                (Path(temp_dir) / "test2.cpp", "content2"),
            ]
            
            transformed = [
                TransformedSource(
                    file_path=str(file_path),
                    original_content="",
                    new_content=content,
                    modifications=()
                )
                for file_path, content in files
            ]
            
            result = writer.apply(transformed)
            
            assert len(result) == 2
            for i, (file_path, content) in enumerate(files):
                assert result[i].file_path == str(file_path)
                assert file_path.exists()
                assert file_path.read_text() == content
    
    def test_atomic_write_behavior(self):
        """Test atomic write behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DirectFileWriter()
            file_path = Path(temp_dir) / "test.cpp"
            content = "test content"
            
            # Mock tempfile to verify atomic behavior
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_file = mock_open()
                mock_temp.return_value.__enter__.return_value = mock_file.return_value
                mock_temp.return_value.__enter__.return_value.name = str(file_path) + ".tmp"
                
                with patch.object(Path, 'replace') as mock_replace:
                    transformed = [
                        TransformedSource(
                            file_path=str(file_path),
                            original_content="",
                            new_content=content,
                            modifications=()
                        )
                    ]
                    
                    writer.apply(transformed)
                    
                    # Verify temp file was written to
                    mock_file.return_value.write.assert_called_once_with(content)
                    # Verify atomic replace was called
                    mock_replace.assert_called_once()
    
    def test_create_parent_directories(self):
        """Test creating parent directories when they don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DirectFileWriter()
            file_path = Path(temp_dir) / "subdir" / "test.cpp"
            content = "test content"
            
            transformed = [
                TransformedSource(
                    file_path=str(file_path),
                    original_content="",
                    new_content=content,
                    modifications=()
                )
            ]
            
            result = writer.apply(transformed)
            
            assert len(result) == 1
            assert file_path.exists()
            assert file_path.read_text() == content
            assert file_path.parent.exists()


@pytest.mark.integration
class TestDirectFileWriterErrorHandling:
    """Error handling tests for DirectFileWriter."""
    
    def test_permission_error_on_readonly_file(self):
        """Test permission error when file is read-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DirectFileWriter()
            file_path = Path(temp_dir) / "readonly.cpp"
            
            # Create read-only file
            file_path.write_text("original")
            file_path.chmod(0o444)  # Read-only
            
            try:
                transformed = [
                    TransformedSource(
                        file_path=str(file_path),
                        original_content="original",
                        new_content="new content",
                        modifications=()
                    )
                ]
                
                with pytest.raises(PermissionError):
                    writer.apply(transformed)
            finally:
                # Restore write permissions for cleanup
                file_path.chmod(0o644)
    
    def test_permission_error_on_readonly_directory(self):
        """Test permission error when directory is read-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = DirectFileWriter()
            subdir = Path(temp_dir) / "readonly_dir"
            subdir.mkdir()
            file_path = subdir / "test.cpp"
            
            # Make directory read-only
            subdir.chmod(0o555)  # Read-only directory
            
            try:
                transformed = [
                    TransformedSource(
                        file_path=str(file_path),
                        original_content="",
                        new_content="new content",
                        modifications=()
                    )
                ]
                
                with pytest.raises(PermissionError):
                    writer.apply(transformed)
            finally:
                # Restore write permissions for cleanup
                subdir.chmod(0o755)
    
    @patch('tempfile.NamedTemporaryFile')
    def test_disk_full_simulation(self, mock_temp):
        """Test handling of disk full scenario."""
        writer = DirectFileWriter()
        
        # Simulate disk full by raising OSError
        mock_temp.side_effect = OSError("No space left on device")
        
        transformed = [
            TransformedSource(
                file_path="test.cpp",
                original_content="",
                new_content="content",
                modifications=()
            )
        ]
        
        with pytest.raises(OSError, match="No space left on device"):
            writer.apply(transformed)