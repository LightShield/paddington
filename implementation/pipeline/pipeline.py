import logging
from typing import List, Any
from .stage import Stage

logger = logging.getLogger(__name__)

class PipelineError(Exception):
    """Pipeline execution error."""
    
    def __init__(self, message: str, stage_name: str = None, stage_index: int = None):
        super().__init__(message)
        self.stage_name = stage_name
        self.stage_index = stage_index

class Pipeline:
    """Pipeline that chains multiple stages together."""
    
    def __init__(self, stages: List[Stage]):
        """Initialize pipeline with stages."""
        if not stages:
            raise ValueError("Pipeline must have at least one stage")
        self.stages = stages
    
    def run(self, initial_input: Any) -> Any:
        """Run all stages in sequence."""
        if not self.validate():
            raise PipelineError("Pipeline validation failed")
        
        current_data = initial_input
        
        for i, stage in enumerate(self.stages):
            stage_name = stage.get_name()
            logger.info(f"Running stage {i}: {stage_name}")
            
            try:
                if not stage.validate_input(current_data):
                    raise PipelineError(
                        f"Input validation failed for stage {stage_name}",
                        stage_name=stage_name,
                        stage_index=i
                    )
                
                current_data = stage.process(current_data)
                logger.info(f"Stage {i}: {stage_name} completed successfully")
                
            except Exception as e:
                error_msg = f"Stage {stage_name} failed: {str(e)}"
                logger.error(error_msg)
                raise PipelineError(
                    error_msg,
                    stage_name=stage_name,
                    stage_index=i
                ) from e
        
        return current_data
    
    def validate(self) -> bool:
        """Validate pipeline configuration."""
        if not self.stages:
            return False
        
        # Basic validation - stages exist and are Stage instances
        for stage in self.stages:
            if not isinstance(stage, Stage):
                return False
        
        return True