import pytest
from implementation.pipeline.stage import Stage

class MockStage(Stage[str, int]):
    """Mock stage for testing."""
    
    def process(self, input_data: str) -> int:
        return len(input_data)
    
    def validate_input(self, input_data: str) -> bool:
        return isinstance(input_data, str) and len(input_data) > 0

class FailingValidationStage(Stage[str, str]):
    """Stage that always fails validation."""
    
    def process(self, input_data: str) -> str:
        return input_data.upper()
    
    def validate_input(self, input_data: str) -> bool:
        return False

@pytest.mark.unit
class TestStage:
    """Test cases for Stage base class."""
    
    def test_stage_is_abstract(self):
        """Test that Stage cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Stage()
    
    def test_mock_stage_process(self):
        """Test mock stage processing."""
        stage = MockStage()
        result = stage.process("hello")
        assert result == 5
    
    def test_mock_stage_validate_input_valid(self):
        """Test mock stage input validation with valid input."""
        stage = MockStage()
        assert stage.validate_input("hello") is True
    
    def test_mock_stage_validate_input_invalid_empty(self):
        """Test mock stage input validation with empty string."""
        stage = MockStage()
        assert stage.validate_input("") is False
    
    def test_mock_stage_validate_input_invalid_type(self):
        """Test mock stage input validation with wrong type."""
        stage = MockStage()
        assert stage.validate_input(123) is False
    
    def test_get_name_default(self):
        """Test default get_name implementation."""
        stage = MockStage()
        assert stage.get_name() == "MockStage"
    
    def test_get_name_different_class(self):
        """Test get_name with different class."""
        stage = FailingValidationStage()
        assert stage.get_name() == "FailingValidationStage"