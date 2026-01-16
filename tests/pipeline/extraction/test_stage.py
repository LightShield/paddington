"""Tests for ExtractionStage."""

import pytest
from pathlib import Path
from unittest.mock import Mock
from implementation.pipeline.extraction.stage import ExtractionStage
from implementation.pipeline.extraction.mock import MockExtractor
from implementation.struct_data.struct_info import StructInfo
from implementation.struct_data.member_info import MemberInfo


@pytest.mark.unit
class TestExtractionStage:
    """Test cases for ExtractionStage."""
    
    def test_init(self):
        """Test stage initialization."""
        extractor = MockExtractor()
        stage = ExtractionStage(extractor)
        assert stage.extractor is extractor
    
    def test_process_calls_extractor(self):
        """Test that process calls extractor.extract."""
        struct_info = StructInfo("TestStruct", 16, [])
        extractor = MockExtractor([struct_info])
        stage = ExtractionStage(extractor)
        
        objfiles = [Path("test.o")]
        result = stage.process(objfiles)
        
        assert result == [struct_info]
    
    def test_process_empty_list(self):
        """Test processing empty object file list."""
        extractor = MockExtractor()
        stage = ExtractionStage(extractor)
        
        result = stage.process([])
        assert result == []
    
    def test_validate_input_valid_files(self, tmp_path):
        """Test validation with valid .o files."""
        extractor = MockExtractor()
        stage = ExtractionStage(extractor)
        
        # Create test .o files
        obj1 = tmp_path / "test1.o"
        obj2 = tmp_path / "test2.o"
        obj1.touch()
        obj2.touch()
        
        assert stage.validate_input([obj1, obj2]) is True
    
    def test_validate_input_nonexistent_file(self):
        """Test validation with nonexistent file."""
        extractor = MockExtractor()
        stage = ExtractionStage(extractor)
        
        nonexistent = Path("nonexistent.o")
        assert stage.validate_input([nonexistent]) is False
    
    def test_validate_input_wrong_extension(self, tmp_path):
        """Test validation with wrong file extension."""
        extractor = MockExtractor()
        stage = ExtractionStage(extractor)
        
        # Create test file with wrong extension
        wrong_ext = tmp_path / "test.cpp"
        wrong_ext.touch()
        
        assert stage.validate_input([wrong_ext]) is False
    
    def test_validate_input_mixed_valid_invalid(self, tmp_path):
        """Test validation with mix of valid and invalid files."""
        extractor = MockExtractor()
        stage = ExtractionStage(extractor)
        
        # Create one valid .o file
        valid_obj = tmp_path / "valid.o"
        valid_obj.touch()
        
        # One nonexistent file
        invalid_obj = Path("nonexistent.o")
        
        assert stage.validate_input([valid_obj, invalid_obj]) is False
    
    def test_validate_input_empty_list(self):
        """Test validation with empty file list."""
        extractor = MockExtractor()
        stage = ExtractionStage(extractor)
        
        assert stage.validate_input([]) is True
    
    def test_extractor_error_propagation(self):
        """Test that extractor errors are propagated."""
        # Create mock extractor that raises exception
        extractor = Mock()
        extractor.extract.side_effect = RuntimeError("Extraction failed")
        
        stage = ExtractionStage(extractor)
        objfiles = [Path("test.o")]
        
        with pytest.raises(RuntimeError, match="Extraction failed"):
            stage.process(objfiles)
    
    def test_get_name(self):
        """Test stage name."""
        extractor = MockExtractor()
        stage = ExtractionStage(extractor)
        assert stage.get_name() == "ExtractionStage"