"""Direct file writer implementation."""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List
from .base import IOutputWriter, AppliedChange
from ...struct_data import TransformedSource


class DirectFileWriterAppliedChange(AppliedChange):
    """Extended AppliedChange with backup path."""
    
    def __init__(self, file_path: str, backup_path: str, timestamp: datetime):
        super().__init__(file_path, timestamp)
        self.backup_path = backup_path


class DirectFileWriter(IOutputWriter):
    """Direct file writer that writes files with backup support."""
    
    def __init__(self, dry_run: bool = False):
        """Initialize direct file writer."""
        self._dry_run = dry_run
    
    def apply(self, transformed: List[TransformedSource]) -> List[AppliedChange]:
        """Apply transformed source code."""
        changes = []
        timestamp = datetime.now()
        
        for source in transformed:
            file_path = Path(source.file_path)
            
            if not self._dry_run:
                self._validate_writable(file_path)
                backup_path = self._create_backup(file_path)
                self._write_atomic(file_path, source.new_content)
            else:
                backup_path = str(file_path) + ".backup"
            
            changes.append(DirectFileWriterAppliedChange(
                file_path=str(file_path),
                backup_path=backup_path,
                timestamp=timestamp
            ))
        
        return changes
    
    def supports_dry_run(self) -> bool:
        """Whether this writer supports dry-run mode."""
        return True
    
    def _validate_writable(self, file_path: Path) -> None:
        """Validate file is writable."""
        if file_path.exists():
            if not os.access(file_path, os.W_OK):
                raise PermissionError(f"File not writable: {file_path}")
        else:
            parent = file_path.parent
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
            if not os.access(parent, os.W_OK):
                raise PermissionError(f"Directory not writable: {parent}")
    
    def _create_backup(self, file_path: Path) -> str:
        """Create backup file."""
        if not file_path.exists():
            return str(file_path) + ".backup"
        
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        backup_path.write_bytes(file_path.read_bytes())
        return str(backup_path)
    
    def _write_atomic(self, file_path: Path, content: str) -> None:
        """Write file atomically."""
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=file_path.parent,
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        
        temp_path.replace(file_path)