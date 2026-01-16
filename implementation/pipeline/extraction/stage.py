"""Extraction stage for the pipeline."""

from pathlib import Path
from typing import List
from ..stage import Stage
from .base import IStructExtractor
from ...struct_data.struct_info import StructInfo


class ExtractionStage(Stage[List[Path], List[StructInfo]]):
    """Stage that extracts struct information from object files."""
    
    def __init__(self, extractor: IStructExtractor):
        """Initialize extraction stage.
        
        Args:
            extractor: The struct extractor to use
        """
        self.extractor = extractor
    
    def process(self, objfiles: List[Path]) -> List[StructInfo]:
        """Extract struct information from object files.
        
        Args:
            objfiles: List of paths to .o files
            
        Returns:
            List of extracted StructInfo
        """
        return self.extractor.extract(objfiles)
    
    def validate_input(self, objfiles: List[Path]) -> bool:
        """Validate that all paths exist and are .o files.
        
        Args:
            objfiles: List of paths to validate
            
        Returns:
            True if all paths are valid .o files
        """
        for path in objfiles:
            if not path.exists():
                return False
            if path.suffix != '.o':
                return False
        return True