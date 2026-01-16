"""Output writing interfaces and implementations."""

from .base import IOutputWriter, AppliedChange
from .mock import MockOutputWriter
from .file_writer import DirectFileWriter, DirectFileWriterAppliedChange
from .patch_generator import GitPatchGenerator

__all__ = [
    "IOutputWriter",
    "AppliedChange", 
    "MockOutputWriter",
    "DirectFileWriter",
    "DirectFileWriterAppliedChange",
    "GitPatchGenerator",
]