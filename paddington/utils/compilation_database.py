"""Compilation database support."""
import json
from pathlib import Path
from typing import List, Dict, Optional
import clang.cindex as clang
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


def get_build_command_for_file(db_path: Path, file_path: Path) -> Optional[str]:
    """Get build command for a specific file from compilation database.
    
    Args:
        db_path: Path to compile_commands.json
        file_path: File to get build command for
        
    Returns:
        Build command string or None if not found
    """
    log = Logger()
    
    try:
        compdb = clang.CompilationDatabase.fromDirectory(str(db_path.parent))
        
        file_variants = [
            str(file_path),
            str(file_path.resolve()),
            file_path.name,
        ]
        
        for variant in file_variants:
            commands = compdb.getCompileCommands(variant)
            if commands:
                # Get the command string
                cmd = commands[0]
                # Reconstruct command from arguments
                return ' '.join(cmd.arguments)
        
        return None
        
    except Exception as e:
        log.debug(f"Could not get build command: {e}")
        return None


def should_use_compilation_database(path: Path) -> bool:
    """Check if we should use compilation database.
    
    Args:
        path: Path being analyzed
        
    Returns:
        True if compile_commands.json exists
    """
    return find_compilation_database(path) is not None


def get_compile_args_for_file(db_path: Path, file_path: Path) -> Optional[List[str]]:
    """Get compile arguments for a specific file from compilation database.
    
    Args:
        db_path: Path to compile_commands.json
        file_path: File to get arguments for
        
    Returns:
        List of compile arguments or None if not found
    """
    log = Logger()
    
    try:
        # Use libclang's compilation database API
        compdb = clang.CompilationDatabase.fromDirectory(str(db_path.parent))
        
        # Try to get commands for this file
        # Try both absolute and relative paths
        file_variants = [
            str(file_path),
            str(file_path.resolve()),
            file_path.name,
        ]
        
        for variant in file_variants:
            commands = compdb.getCompileCommands(variant)
            if commands:
                # Extract relevant parsing flags
                args = list(commands[0].arguments)
                directory = Path(commands[0].directory)
                parse_args = []
                
                for arg in args:
                    # Include C++ standard, include paths, and defines
                    if arg.startswith('-std='):
                        parse_args.append(arg)
                    elif arg.startswith('-I'):
                        # Resolve relative include paths
                        include_path = arg[2:]  # Remove -I
                        if not Path(include_path).is_absolute():
                            include_path = str(directory / include_path)
                        parse_args.append(f'-I{include_path}')
                    elif arg.startswith('-D'):
                        parse_args.append(arg)
                    elif arg.startswith('-isystem'):
                        parse_args.append(arg)
                
                log.debug(f"Found {len(parse_args)} compile args for {file_path.name}")
                return parse_args
        
        return None
        
    except Exception as e:
        log.debug(f"Could not get compile args: {e}")
        return None
