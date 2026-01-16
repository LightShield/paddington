"""Unit tests for source change dataclasses."""

import pytest

from implementation.struct_data.source_change import (
    Location, Modification, SourceModification, TransformedSource
)


@pytest.mark.unit
class TestLocation:
    """Test cases for Location dataclass."""
    
    def test_creation(self):
        """Test creating Location."""
        location = Location("file.cpp", 10, 5)
        
        assert location.file == "file.cpp"
        assert location.line == 10
        assert location.column == 5
    
    def test_immutability(self):
        """Test that Location is immutable."""
        location = Location("file.cpp", 10, 5)
        
        with pytest.raises(AttributeError):
            location.line = 20
    
    def test_invalid_line_number(self):
        """Test validation of line number."""
        with pytest.raises(ValueError, match="Line number must be positive"):
            Location("file.cpp", 0, 5)
    
    def test_negative_column(self):
        """Test validation of negative column."""
        with pytest.raises(ValueError, match="Column number cannot be negative"):
            Location("file.cpp", 10, -1)


@pytest.mark.unit
class TestModification:
    """Test cases for Modification dataclass."""
    
    def test_creation(self):
        """Test creating Modification."""
        location = Location("file.cpp", 10, 5)
        mod = Modification("reorder_member", location, "old", "new")
        
        assert mod.type == "reorder_member"
        assert mod.location == location
        assert mod.old_content == "old"
        assert mod.new_content == "new"
    
    def test_immutability(self):
        """Test that Modification is immutable."""
        location = Location("file.cpp", 10, 5)
        mod = Modification("reorder_member", location, "old", "new")
        
        with pytest.raises(AttributeError):
            mod.type = "new_type"


@pytest.mark.unit
class TestSourceModification:
    """Test cases for SourceModification dataclass."""
    
    def test_creation(self):
        """Test creating SourceModification."""
        location = Location("file.cpp", 10, 5)
        mod = Modification("reorder_member", location, "old", "new")
        modifications = (mod,)
        
        source_mod = SourceModification("file.cpp", "TestStruct", modifications)
        
        assert source_mod.file_path == "file.cpp"
        assert source_mod.struct_name == "TestStruct"
        assert source_mod.modifications == modifications
    
    def test_immutability(self):
        """Test that SourceModification is immutable."""
        location = Location("file.cpp", 10, 5)
        mod = Modification("reorder_member", location, "old", "new")
        modifications = (mod,)
        
        source_mod = SourceModification("file.cpp", "TestStruct", modifications)
        
        with pytest.raises(AttributeError):
            source_mod.file_path = "new_file.cpp"
    
    def test_empty_modifications(self):
        """Test creating SourceModification with empty modifications."""
        source_mod = SourceModification("file.cpp", "TestStruct", ())
        
        assert source_mod.modifications == ()


@pytest.mark.unit
class TestTransformedSource:
    """Test cases for TransformedSource dataclass."""
    
    def test_creation(self):
        """Test creating TransformedSource."""
        location = Location("file.cpp", 10, 5)
        mod = Modification("reorder_member", location, "old", "new")
        source_mod = SourceModification("file.cpp", "TestStruct", (mod,))
        modifications = (source_mod,)
        
        transformed = TransformedSource(
            "file.cpp",
            "original content",
            "new content",
            modifications
        )
        
        assert transformed.file_path == "file.cpp"
        assert transformed.original_content == "original content"
        assert transformed.new_content == "new content"
        assert transformed.modifications == modifications
    
    def test_immutability(self):
        """Test that TransformedSource is immutable."""
        transformed = TransformedSource("file.cpp", "old", "new", ())
        
        with pytest.raises(AttributeError):
            transformed.original_content = "different"
    
    def test_empty_modifications(self):
        """Test creating TransformedSource with empty modifications."""
        transformed = TransformedSource("file.cpp", "old", "new", ())
        
        assert transformed.modifications == ()