from abc import ABC, abstractmethod
from typing import TypeVar, Generic

TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')

class Stage(ABC, Generic[TInput, TOutput]):
    """Base class for pipeline stages."""
    
    @abstractmethod
    def process(self, input_data: TInput) -> TOutput:
        """Process input and return output."""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: TInput) -> bool:
        """Validate input before processing."""
        pass
    
    def get_name(self) -> str:
        """Get stage name for logging."""
        return self.__class__.__name__