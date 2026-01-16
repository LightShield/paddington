"""Mock struct extractor for testing."""

from pathlib import Path
from typing import List
from .base import IStructExtractor
from ...struct_data.struct_info import StructInfo


class MockExtractor(IStructExtractor):
    """Mock struct extractor that returns hardcoded data for testing."""
    
    def __init__(self, return_structs: List[StructInfo] = None):
        """Initialize mock extractor.
        
        Args:
            return_structs: List of StructInfo to return from extract()
        """
        self._return_structs = return_structs or []
    
    def extract(self, objfiles: List[Path]) -> List[StructInfo]:
        """Return configured struct information.
        
        Args:
            objfiles: List of paths to .o files (ignored)
            
        Returns:
            Configured list of StructInfo
        """
        return self._return_structs.copy()
    
    def supports_caching(self) -> bool:
        """Mock always supports caching.
        
        Returns:
            True
        """
        return True