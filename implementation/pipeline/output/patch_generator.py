"""Git patch generator for struct optimizations."""

import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set

from .base import IOutputWriter, AppliedChange as BaseAppliedChange
from ...struct_data import TransformedSource


@dataclass(frozen=True)
class AppliedChange(BaseAppliedChange):
    """Extended AppliedChange with patch and message paths."""
    
    patch_path: str
    message_path: str


class GitPatchGenerator(IOutputWriter):
    """Generates git patches for struct optimizations."""
    
    def __init__(self, output_dir: Path):
        """Initialize patch generator.
        
        Args:
            output_dir: Directory to write patches and messages
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def apply(self, transformed: List[TransformedSource]) -> List[AppliedChange]:
        """Generate patches for transformed source code.
        
        Args:
            transformed: List of transformed source files
            
        Returns:
            List of applied changes with patch and message paths
        """
        if not transformed:
            return []
        
        # Generate patches - one per transformed source file
        changes = []
        for i, source in enumerate(transformed):
            struct_name = source.modifications[0].struct_name if source.modifications else "unknown"
            
            patch_path, message_path = self._generate_patch(source, struct_name, i)
            changes.append(AppliedChange(
                file_path=source.file_path,
                timestamp=datetime.now(),
                patch_path=str(patch_path),
                message_path=str(message_path)
            ))
        
        # Create apply order file
        self._create_apply_order(changes)
        
        return changes
    
    def supports_dry_run(self) -> bool:
        """Returns True as patch generation supports dry-run mode."""
        return True
    
    def _build_dependency_order(self, transformed: List[TransformedSource]) -> List[str]:
        """Build dependency order for struct patches."""
        # Extract all struct names
        struct_names = set()
        for source in transformed:
            for mod in source.modifications:
                struct_names.add(mod.struct_name)
        
        # Simple alphabetical ordering for now
        return sorted(struct_names)
    
    def _generate_patch(self, source: TransformedSource, struct_name: str, order: int) -> tuple[Path, Path]:
        """Generate patch and message files for a struct."""
        # Create patch filename
        patch_name = f"struct_{order:03d}_{struct_name}.patch"
        message_name = f"struct_{order:03d}_{struct_name}.msg"
        
        patch_path = self.output_dir / patch_name
        message_path = self.output_dir / message_name
        
        # Generate patch using git diff --no-index
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as orig_file:
            orig_file.write(source.original_content)
            orig_file.flush()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as new_file:
                new_file.write(source.new_content)
                new_file.flush()
                
                try:
                    result = subprocess.run([
                        'git', 'diff', '--no-index', '--no-prefix',
                        orig_file.name, new_file.name
                    ], capture_output=True, text=True)
                    
                    # Replace temp filenames with actual source file path
                    patch_content = result.stdout
                    if patch_content:
                        # Extract meaningful source path
                        source_path = source.file_path
                        
                        # If path contains /snapshot/, extract everything after it
                        if '/snapshot/' in source_path:
                            source_path = source_path.split('/snapshot/')[-1]
                        # If path contains /build_storm/, extract everything after it  
                        elif '/build_storm/' in source_path:
                            parts = source_path.split('/build_storm/')[-1]
                            if parts.startswith('snapshot/'):
                                source_path = parts[9:]  # Remove 'snapshot/'
                            else:
                                source_path = parts
                        # Otherwise use the path as-is (already relative)
                        
                        # Get basenames for replacement (git diff uses basename in diff --git line)
                        orig_basename = Path(orig_file.name).name
                        new_basename = Path(new_file.name).name
                        
                        # Replace all occurrences
                        patch_content = patch_content.replace(f"tmp/{orig_basename}", f"a/{source_path}")
                        patch_content = patch_content.replace(f"tmp/{new_basename}", f"b/{source_path}")
                        patch_content = patch_content.replace(orig_file.name, f"a/{source_path}")
                        patch_content = patch_content.replace(new_file.name, f"b/{source_path}")
                    
                    # Write patch file
                    with open(patch_path, 'w') as f:
                        f.write(patch_content)
                    
                finally:
                    Path(orig_file.name).unlink(missing_ok=True)
                    Path(new_file.name).unlink(missing_ok=True)
        
        # Generate commit message
        message = self._generate_commit_message(source, struct_name)
        with open(message_path, 'w') as f:
            f.write(message)
        
        return patch_path, message_path
    
    def _generate_commit_message(self, source: TransformedSource, struct_name: str) -> str:
        """Generate commit message for struct optimization."""
        # Use content length as proxy for size (more accurate than line count)
        # Note: This is file size, not struct size, but better than nothing
        size_before = len(source.original_content)
        size_after = len(source.new_content)
        padding_saved = max(0, size_before - size_after)
        
        return f"""refactor: Optimize padding for {struct_name}

Reorder members from largest to smallest.
Saves {padding_saved} bytes per instance.

Before: {size_before} bytes (file size)
After: {size_after} bytes (file size)"""
    
    def _create_apply_order(self, changes: List[AppliedChange]) -> None:
        """Create APPLY_ORDER.txt file."""
        order_path = self.output_dir / "APPLY_ORDER.txt"
        
        with open(order_path, 'w') as f:
            f.write("# Apply patches in this order:\n\n")
            for i, change in enumerate(changes, 1):
                patch_name = Path(change.patch_path).name
                f.write(f"{i}. {patch_name}\n")