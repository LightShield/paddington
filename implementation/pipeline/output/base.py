"""Base interface for output writing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List
from ...struct_data import TransformedSource


@dataclass(frozen=True)
class AppliedChange:
    """Result of applying a change."""
    
    file_path: str
    timestamp: datetime


class IOutputWriter(ABC):
    """Interface for writing transformed source code."""
    
    @abstractmethod
    def apply(self, transformed: List[TransformedSource]) -> List[AppliedChange]:
        """Apply transformed source code."""
        pass
    
    @abstractmethod
    def supports_dry_run(self) -> bool:
        """Whether this writer supports dry-run mode."""
        pass