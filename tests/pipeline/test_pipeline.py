import pytest
import logging
from unittest.mock import Mock, patch
from implementation.pipeline.pipeline import Pipeline, PipelineError
from implementation.pipeline.stage import Stage

class StringToIntStage(Stage[str, int]):
    """Stage that converts string to its length."""
    
    def process(self, input_data: str) -> int:
        return len(input_data)
    
    def validate_input(self, input_data: str) -> bool:
        return isinstance(input_data, str)

class IntToStringStage(Stage[int, str]):
    """Stage that converts int to string."""
    
    def process(self, input_data: int) -> str:
        return f"Length: {input_data}"
    
    def validate_input(self, input_data: int) -> bool:
        return isinstance(input_data, int) and input_data >= 0

class FailingStage(Stage[str, str]):
    """Stage that always fails processing."""
    
    def process(self, input_data: str) -> str:
        raise ValueError("Processing failed")
    
    def validate_input(self, input_data: str) -> bool:
        return True

class InvalidInputStage(Stage[str, str]):
    """Stage that always fails input validation."""
    
    def process(self, input_data: str) -> str:
        return input_data.upper()
    
    def validate_input(self, input_data: str) -> bool:
        return False

@pytest.mark.unit
class TestPipelineError:
    """Test cases for PipelineError."""
    
    def test_pipeline_error_basic(self):
        """Test basic PipelineError creation."""
        error = PipelineError("Test error")
        assert str(error) == "Test error"
        assert error.stage_name is None
        assert error.stage_index is None
    
    def test_pipeline_error_with_stage_info(self):
        """Test PipelineError with stage information."""
        error = PipelineError("Test error", stage_name="TestStage", stage_index=1)
        assert str(error) == "Test error"
        assert error.stage_name == "TestStage"
        assert error.stage_index == 1

@pytest.mark.unit
class TestPipeline:
    """Test cases for Pipeline class."""
    
    def test_pipeline_creation_empty_stages(self):
        """Test pipeline creation with empty stages list."""
        with pytest.raises(ValueError, match="Pipeline must have at least one stage"):
            Pipeline([])
    
    def test_pipeline_creation_valid(self):
        """Test valid pipeline creation."""
        stage = StringToIntStage()
        pipeline = Pipeline([stage])
        assert len(pipeline.stages) == 1
        assert pipeline.stages[0] is stage
    
    def test_validate_empty_stages(self):
        """Test validation with empty stages."""
        pipeline = Pipeline.__new__(Pipeline)  # Bypass __init__
        pipeline.stages = []
        assert pipeline.validate() is False
    
    def test_validate_invalid_stage_type(self):
        """Test validation with non-Stage object."""
        pipeline = Pipeline.__new__(Pipeline)  # Bypass __init__
        pipeline.stages = ["not a stage"]
        assert pipeline.validate() is False
    
    def test_validate_valid_stages(self):
        """Test validation with valid stages."""
        stage = StringToIntStage()
        pipeline = Pipeline([stage])
        assert pipeline.validate() is True
    
    def test_run_single_stage_success(self):
        """Test successful run with single stage."""
        stage = StringToIntStage()
        pipeline = Pipeline([stage])
        
        result = pipeline.run("hello")
        assert result == 5
    
    def test_run_multiple_stages_success(self):
        """Test successful run with multiple stages."""
        stage1 = StringToIntStage()
        stage2 = IntToStringStage()
        pipeline = Pipeline([stage1, stage2])
        
        result = pipeline.run("hello")
        assert result == "Length: 5"
    
    def test_run_validation_failure(self):
        """Test run with pipeline validation failure."""
        pipeline = Pipeline.__new__(Pipeline)  # Bypass __init__
        pipeline.stages = []
        
        with pytest.raises(PipelineError, match="Pipeline validation failed"):
            pipeline.run("test")
    
    def test_run_stage_input_validation_failure(self):
        """Test run with stage input validation failure."""
        stage = InvalidInputStage()
        pipeline = Pipeline([stage])
        
        with pytest.raises(PipelineError) as exc_info:
            pipeline.run("test")
        
        error = exc_info.value
        assert "Input validation failed" in str(error)
        assert error.stage_name == "InvalidInputStage"
        assert error.stage_index == 0
    
    def test_run_stage_processing_failure(self):
        """Test run with stage processing failure."""
        stage = FailingStage()
        pipeline = Pipeline([stage])
        
        with pytest.raises(PipelineError) as exc_info:
            pipeline.run("test")
        
        error = exc_info.value
        assert "FailingStage failed" in str(error)
        assert error.stage_name == "FailingStage"
        assert error.stage_index == 0
        assert isinstance(error.__cause__, ValueError)
    
    @patch('implementation.pipeline.pipeline.logger')
    def test_run_logging(self, mock_logger):
        """Test that pipeline run logs appropriately."""
        stage = StringToIntStage()
        pipeline = Pipeline([stage])
        
        pipeline.run("hello")
        
        # Check that info logs were called
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_any_call("Running stage 0: StringToIntStage")
        mock_logger.info.assert_any_call("Stage 0: StringToIntStage completed successfully")
    
    @patch('implementation.pipeline.pipeline.logger')
    def test_run_error_logging(self, mock_logger):
        """Test that pipeline run logs errors appropriately."""
        stage = FailingStage()
        pipeline = Pipeline([stage])
        
        with pytest.raises(PipelineError):
            pipeline.run("test")
        
        # Check that error log was called
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "FailingStage failed" in error_call
    
    def test_run_multiple_stages_failure_in_second(self):
        """Test run with failure in second stage."""
        stage1 = StringToIntStage()
        stage2 = FailingStage()  # This expects string but will get int
        pipeline = Pipeline([stage1, stage2])
        
        # Need to create a stage that fails with int input
        class IntFailingStage(Stage[int, str]):
            def process(self, input_data: int) -> str:
                raise ValueError("Int processing failed")
            def validate_input(self, input_data: int) -> bool:
                return True
        
        stage2 = IntFailingStage()
        pipeline = Pipeline([stage1, stage2])
        
        with pytest.raises(PipelineError) as exc_info:
            pipeline.run("hello")
        
        error = exc_info.value
        assert error.stage_index == 1
        assert error.stage_name == "IntFailingStage"