from abc import ABC, abstractmethod
from typing import List
from ...struct_data import SourceModification, TransformedSource


class ISourceTransformer(ABC):
    @abstractmethod
    def transform(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        """Transform source code based on modifications."""
        pass
    
    @abstractmethod
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this transformer can handle the file type."""
        pass