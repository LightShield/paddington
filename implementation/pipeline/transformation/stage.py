"""Transformation stage wrapper."""

from typing import List
from ..stage import Stage
from .base import ISourceTransformer
from ...struct_data.source_change import SourceModification, TransformedSource


class TransformationStage(Stage[List[SourceModification], List[TransformedSource]]):
    """Transform source code based on modifications."""
    
    def __init__(self, transformer: ISourceTransformer):
        self.transformer = transformer
    
    def process(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        """Transform source code."""
        return self.transformer.transform(modifications)
    
    def validate_input(self, modifications: List[SourceModification]) -> bool:
        """Validate input modifications."""
        return isinstance(modifications, list) and all(isinstance(m, SourceModification) for m in modifications)
