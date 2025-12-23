"""Generate git patches for struct optimizations."""

import subprocess
from pathlib import Path
from typing import List, Optional
from ..core import StructInfo
from ..utils import Logger


def create_patch(
    file_paths, struct: StructInfo, patch_dir: Path, tree_id: str, order: int
) -> Optional[Path]:
    """Create a git patch file for a single struct optimization.

    Args:
        file_paths: Path or list of paths to modified files
        struct: Struct that was optimized
        patch_dir: Directory to save patch files
        tree_id: Dependency tree identifier (e.g., 'tree_001')
        order: Order within tree (e.g., 1, 2, 3)

    Returns:
        Path to generated patch file
    """
    log = Logger()
    
    # Handle single file or list
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    # Generate patch filename: tree_id_order_struct_name.patch
    patch_name = f"{tree_id}_{order:02d}_{struct.name}.patch"
    patch_path = patch_dir / patch_name

    # Create git diff for all files
    try:
        result = subprocess.run(
            ["git", "diff", "--no-color"] + file_paths,
            capture_output=True,
            text=True,
            cwd=Path(file_paths[0]).parent,
        )

        if result.returncode != 0:
            log.error(f"Failed to generate diff: {result.stderr}")
            return None

        # Write patch file
        with open(patch_path, "w") as f:
            f.write(result.stdout)

        log.debug(f"Created patch: {patch_name}")
        return patch_path

    except Exception as e:
        log.error(f"Error creating patch: {e}")
        return None


def generate_commit_message(struct: StructInfo, savings: int) -> str:
    """Generate conventional commit message for struct optimization.

    Args:
        struct: Optimized struct
        savings: Bytes saved

    Returns:
        Commit message following Conventional Commits format
    """
    type_name = "struct"

    if savings > 0:
        return f"""refactor: Optimize padding for {type_name} {struct.name}

Reorder members from largest to smallest to reduce padding.

Changes:
- {struct.name}: {struct.size} -> {struct.size - savings} bytes ({savings} bytes saved)

Location: {struct.file_path}:{struct.line}"""
    else:
        return f"""refactor: Normalize member order for {type_name} {struct.name}

Reorder members from largest to smallest for consistency.

Location: {struct.file_path}:{struct.line}"""


def write_apply_order(patch_dir: Path, patch_files: List[Path]) -> None:
    """Write APPLY_ORDER.txt with list of patches in order.

    Args:
        patch_dir: Directory containing patches
        patch_files: List of patch file paths in application order
    """
    order_file = patch_dir / "APPLY_ORDER.txt"

    with open(order_file, "w") as f:
        f.write("# Apply patches in this order:\n\n")
        for i, patch_file in enumerate(patch_files, 1):
            f.write(f"{i}. {patch_file.name}\n")
