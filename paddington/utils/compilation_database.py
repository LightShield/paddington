"""Compilation database support."""
import json
from pathlib import Path
from typing import List, Dict, Optional
from .logger import Logger


def find_compilation_database(start_path: Path) -> Optional[Path]:
    """Find compile_commands.json in current or parent directories.
    
    Args:
        start_path: Starting directory to search from
        
    Returns:
        Path to compile_commands.json or None if not found
    """
    current = start_path if start_path.is_dir() else start_path.parent
    
    # Search up to 5 levels
    for _ in range(5):
        compile_db = current / "compile_commands.json"
        if compile_db.exists():
            return compile_db
        
        if current.parent == current:  # Reached root
            break
        current = current.parent
    
    return None


def load_compilation_database(db_path: Path) -> List[Dict]:
    """Load compilation database.
    
    Args:
        db_path: Path to compile_commands.json
        
    Returns:
        List of compilation entries
    """
    with open(db_path, 'r') as f:
        return json.load(f)


def get_files_from_compilation_database(db_path: Path) -> List[Path]:
    """Get list of source files from compilation database.
    
    Args:
        db_path: Path to compile_commands.json
        
    Returns:
        List of source file paths (resolved to absolute paths)
    """
    log = Logger()
    
    try:
        entries = load_compilation_database(db_path)
        files = []
        
        for entry in entries:
            file_rel = entry.get('file', '')
            directory = entry.get('directory', '')
            
            # Resolve relative paths using directory field
            if directory:
                file_path = Path(directory) / file_rel
            else:
                file_path = Path(file_rel)
            
            if file_path.exists():
                files.append(file_path)
            else:
                log.debug(f"File from compile_commands.json not found: {file_path}")
        
        log.debug(f"Found {len(files)} files in compilation database")
        return files
        
    except Exception as e:
        log.error(f"Error reading compilation database: {e}")
        return []


def should_use_compilation_database(path: Path) -> bool:
    """Check if we should use compilation database.
    
    Args:
        path: Path being analyzed
        
    Returns:
        True if compile_commands.json exists
    """
    return find_compilation_database(path) is not None
