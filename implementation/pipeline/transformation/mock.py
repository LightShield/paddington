from typing import List, Optional
from .base import ISourceTransformer
from ...struct_data import SourceModification, TransformedSource


class MockTransformer(ISourceTransformer):
    def __init__(self, 
                 transform_result: Optional[List[TransformedSource]] = None,
                 can_handle_result: bool = True):
        self._transform_result = transform_result or []
        self._can_handle_result = can_handle_result
    
    def transform(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        return self._transform_result
    
    def can_handle_file(self, file_path: str) -> bool:
        return self._can_handle_result