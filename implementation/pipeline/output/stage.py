"""Output stage wrapper."""

from typing import List
from ..stage import Stage
from .base import IOutputWriter, AppliedChange
from ...struct_data.source_change import TransformedSource


class OutputStage(Stage[List[TransformedSource], List[AppliedChange]]):
    """Apply transformed source code."""
    
    def __init__(self, writer: IOutputWriter):
        self.writer = writer
    
    def process(self, transformed: List[TransformedSource]) -> List[AppliedChange]:
        """Apply transformations."""
        return self.writer.apply(transformed)
    
    def validate_input(self, transformed: List[TransformedSource]) -> bool:
        """Validate input transformations."""
        return isinstance(transformed, list) and all(isinstance(t, TransformedSource) for t in transformed)
