"""Base interface for struct extractors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from ...struct_data.struct_info import StructInfo


class IStructExtractor(ABC):
    """Interface for struct extractors."""
    
    @abstractmethod
    def extract(self, objfiles: List[Path]) -> List[StructInfo]:
        """Extract struct information from object files.
        
        Args:
            objfiles: List of paths to .o files
            
        Returns:
            List of StructInfo extracted from object files
        """
        pass
    
    @abstractmethod
    def supports_caching(self) -> bool:
        """Whether this extractor supports caching.
        
        Returns:
            True if caching is supported
        """
        pass