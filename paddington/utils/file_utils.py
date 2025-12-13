"""File system utilities."""

from pathlib import Path
from typing import List


def find_cpp_files(path: Path) -> List[Path]:
    """Find all C++ files in path."""
    if path.is_file():
        return [path]

    extensions = {".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"}
    return [f for f in path.rglob("*") if f.suffix in extensions]
