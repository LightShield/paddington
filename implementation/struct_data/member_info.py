"""MemberInfo dataclass for struct member information."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MemberInfo:
    """Immutable information about a struct member."""
    
    name: str
    type: str
    size: int
    offset: int
    access_modifier: str
    optimized_size: Optional[int] = None
    locked: bool = False
    
    def __post_init__(self) -> None:
        """Validate member info after initialization."""
        if self.access_modifier not in ("public", "private", "protected", "none"):
            raise ValueError(f"Invalid access_modifier: {self.access_modifier}")
        if self.size < 0:
            raise ValueError(f"Size cannot be negative: {self.size}")
        if self.offset < 0:
            raise ValueError(f"Offset cannot be negative: {self.offset}")
        if self.optimized_size is not None and self.optimized_size < 0:
            raise ValueError(f"Optimized size cannot be negative: {self.optimized_size}")