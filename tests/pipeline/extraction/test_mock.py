"""Unit tests for MockExtractor."""

import pytest
from pathlib import Path
from implementation.pipeline.extraction.base import IStructExtractor
from implementation.pipeline.extraction.mock import MockExtractor
from implementation.struct_data import StructInfo, MemberInfo


@pytest.mark.unit
class TestMockExtractor:
    """Test cases for MockExtractor."""
    
    def test_implements_interface(self):
        """Test that MockExtractor implements IStructExtractor interface."""
        extractor = MockExtractor()
        assert isinstance(extractor, IStructExtractor)
    
    def test_default_behavior(self):
        """Test mock with default behavior returns empty list."""
        extractor = MockExtractor()
        objfiles = [Path("test.o")]
        
        result = extractor.extract(objfiles)
        
        assert result == []
        assert isinstance(result, list)
    
    def test_custom_return_values(self):
        """Test mock with custom return values."""
        struct1 = StructInfo(
            name="TestStruct1",
            size=16,
            members=(MemberInfo(name="field1", type="int", size=8, offset=0, access_modifier="public"),)
        )
        struct2 = StructInfo(
            name="TestStruct2", 
            size=32,
            members=(MemberInfo(name="field2", type="long", size=16, offset=0, access_modifier="public"),)
        )
        
        extractor = MockExtractor(return_structs=[struct1, struct2])
        objfiles = [Path("test1.o"), Path("test2.o")]
        
        result = extractor.extract(objfiles)
        
        assert len(result) == 2
        assert result[0] == struct1
        assert result[1] == struct2
    
    def test_empty_return_values(self):
        """Test mock with explicitly empty return values."""
        extractor = MockExtractor(return_structs=[])
        objfiles = [Path("test.o")]
        
        result = extractor.extract(objfiles)
        
        assert result == []
    
    def test_supports_caching(self):
        """Test that mock supports caching."""
        extractor = MockExtractor()
        
        assert extractor.supports_caching() is True
    
    def test_extract_returns_copy(self):
        """Test that extract returns a copy of the configured structs."""
        struct1 = StructInfo(
            name="TestStruct",
            size=8,
            members=(MemberInfo(name="field", type="int", size=4, offset=0, access_modifier="public"),)
        )
        
        extractor = MockExtractor(return_structs=[struct1])
        objfiles = [Path("test.o")]
        
        result1 = extractor.extract(objfiles)
        result2 = extractor.extract(objfiles)
        
        # Results should be equal but not the same object
        assert result1 == result2
        assert result1 is not result2
        
        # Modifying one result shouldn't affect the other
        result1.append(StructInfo(name="Modified", size=4, members=()))
        assert len(result2) == 1
    
    def test_extract_ignores_objfiles(self):
        """Test that extract ignores the objfiles parameter."""
        struct1 = StructInfo(name="Test", size=4, members=())
        extractor = MockExtractor(return_structs=[struct1])
        
        # Should return same result regardless of objfiles
        result1 = extractor.extract([])
        result2 = extractor.extract([Path("file1.o")])
        result3 = extractor.extract([Path("file1.o"), Path("file2.o")])
        
        assert result1 == result2 == result3 == [struct1]