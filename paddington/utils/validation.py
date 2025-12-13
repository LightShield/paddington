"""Input validation utilities."""

import subprocess
from pathlib import Path


def validate_path_exists(path: Path) -> bool:
    """Validate that path exists.

    Args:
        path: Path to validate

    Returns:
        True if path exists

    Raises:
        FileNotFoundError: If path doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    return True


def validate_git_repo(path: Path) -> bool:
    """Validate that path is in a git repository (for patch generation).

    Args:
        path: Path to check

    Returns:
        True if in git repo

    Raises:
        RuntimeError: If not in git repo
    """
    try:
        # Check if path is in a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            cwd=path if path.is_dir() else path.parent,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Path is not in a git repository: {path}\n"
                "Patch generation requires files to be in a git repo.\n"
                "Initialize with: git init"
            )

        return True
    except FileNotFoundError:
        raise RuntimeError(
            "git command not found. Please install git.\n"
            "Patch generation requires git to be installed."
        )


def validate_libclang_available() -> bool:
    """Validate that libclang is available.

    Returns:
        True if libclang can be loaded

    Raises:
        RuntimeError: If libclang not available
    """
    try:
        import clang.cindex  # noqa: F401

        # Just check if we can import, don't initialize yet
        return True
    except ImportError as e:
        raise RuntimeError(
            f"Failed to import libclang: {e}\n"
            "Please install libclang: pip install libclang"
        )


def validate_cpp_files_exist(path: Path) -> bool:
    """Validate that C++ files exist in path.

    Args:
        path: Path to check

    Returns:
        True if C++ files found

    Raises:
        ValueError: If no C++ files found
    """
    from .file_utils import find_cpp_files

    files = find_cpp_files(path)
    if not files:
        raise ValueError(
            f"No C++ files found in {path}\n"
            "Looking for files with extensions: .cpp, .cc, .cxx, .h, .hpp, .hxx"
        )

    return True
