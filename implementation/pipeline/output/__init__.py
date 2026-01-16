"""Output writing interfaces and implementations."""

from .base import IOutputWriter, AppliedChange
from .mock import MockOutputWriter

__all__ = [
    "IOutputWriter",
    "AppliedChange", 
    "MockOutputWriter",
]