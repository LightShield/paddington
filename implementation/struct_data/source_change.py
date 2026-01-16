"""Source modification dataclasses for code transformations."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Location:
    """Location in source code."""
    
    file: str
    line: int
    column: int
    
    def __post_init__(self) -> None:
        """Validate location after initialization."""
        if self.line < 1:
            raise ValueError(f"Line number must be positive: {self.line}")
        if self.column < 0:
            raise ValueError(f"Column number cannot be negative: {self.column}")


@dataclass(frozen=True)
class Modification:
    """A single modification to source code."""
    
    type: str
    location: Location
    old_content: str
    new_content: str


@dataclass(frozen=True)
class SourceModification:
    """Modifications for a specific struct in a file."""
    
    file_path: str
    struct_name: str
    modifications: Tuple[Modification, ...]


@dataclass(frozen=True)
class TransformedSource:
    """Complete source transformation for a file."""
    
    file_path: str
    original_content: str
    new_content: str
    modifications: Tuple[SourceModification, ...]