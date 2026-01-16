"""Unit tests for mock output writer."""

import pytest
from datetime import datetime
from implementation.pipeline.output import MockOutputWriter, AppliedChange
from implementation.struct_data import TransformedSource, SourceModification


@pytest.mark.unit
class TestMockOutputWriter:
    """Test cases for MockOutputWriter."""
    
    def test_init_default(self):
        """Test default initialization."""
        writer = MockOutputWriter()
        assert writer.supports_dry_run() is True
        assert writer.applied_changes == []
    
    def test_init_with_dry_run_support(self):
        """Test initialization with dry run support."""
        writer = MockOutputWriter(dry_run_support=False)
        assert writer.supports_dry_run() is False
        assert writer.applied_changes == []
    
    def test_apply_empty_list(self):
        """Test applying empty transformation list."""
        writer = MockOutputWriter()
        result = writer.apply([])
        assert result == []
        assert writer.applied_changes == []
    
    def test_apply_single_transformation(self):
        """Test applying single transformation."""
        writer = MockOutputWriter()
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
        assert isinstance(result[0].timestamp, datetime)
        assert writer.applied_changes == result
    
    def test_apply_multiple_transformations(self):
        """Test applying multiple transformations."""
        writer = MockOutputWriter()
        transformed = [
            TransformedSource(
                file_path="test1.cpp",
                original_content="old1",
                new_content="new1",
                modifications=()
            ),
            TransformedSource(
                file_path="test2.cpp", 
                original_content="old2",
                new_content="new2",
                modifications=()
            )
        ]
        
        result = writer.apply(transformed)
        
        assert len(result) == 2
        assert result[0].file_path == "test1.cpp"
        assert result[1].file_path == "test2.cpp"
        assert all(isinstance(change.timestamp, datetime) for change in result)
        assert writer.applied_changes == result
    
    def test_apply_accumulates_changes(self):
        """Test that multiple apply calls accumulate changes."""
        writer = MockOutputWriter()
        
        first_batch = [
            TransformedSource(
                file_path="test1.cpp",
                original_content="old1",
                new_content="new1", 
                modifications=()
            )
        ]
        
        second_batch = [
            TransformedSource(
                file_path="test2.cpp",
                original_content="old2",
                new_content="new2",
                modifications=()
            )
        ]
        
        result1 = writer.apply(first_batch)
        result2 = writer.apply(second_batch)
        
        assert len(writer.applied_changes) == 2
        assert writer.applied_changes[0] == result1[0]
        assert writer.applied_changes[1] == result2[0]
    
    def test_applied_changes_returns_copy(self):
        """Test that applied_changes returns a copy."""
        writer = MockOutputWriter()
        transformed = [
            TransformedSource(
                file_path="test.cpp",
                original_content="old",
                new_content="new",
                modifications=()
            )
        ]
        
        writer.apply(transformed)
        changes1 = writer.applied_changes
        changes2 = writer.applied_changes
        
        assert changes1 == changes2
        assert changes1 is not changes2
        
        # Modifying returned list shouldn't affect internal state
        changes1.clear()
        assert len(writer.applied_changes) == 1