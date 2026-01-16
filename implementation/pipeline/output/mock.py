"""Mock output writer for testing."""

from datetime import datetime
from typing import List
from .base import IOutputWriter, AppliedChange
from ...struct_data import TransformedSource


class MockOutputWriter(IOutputWriter):
    """Mock output writer for testing."""
    
    def __init__(self, dry_run_support: bool = True):
        """Initialize mock writer."""
        self._dry_run_support = dry_run_support
        self._applied_changes: List[AppliedChange] = []
    
    def apply(self, transformed: List[TransformedSource]) -> List[AppliedChange]:
        """Apply transformed source code."""
        changes = [
            AppliedChange(
                file_path=source.file_path,
                timestamp=datetime.now()
            )
            for source in transformed
        ]
        self._applied_changes.extend(changes)
        return changes
    
    def supports_dry_run(self) -> bool:
        """Whether this writer supports dry-run mode."""
        return self._dry_run_support
    
    @property
    def applied_changes(self) -> List[AppliedChange]:
        """Get all applied changes."""
        return self._applied_changes.copy()