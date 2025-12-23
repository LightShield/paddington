"""Test utilities."""

import shutil
from typing import Optional


def find_cpp_compiler() -> Optional[str]:
    """Find available C++ compiler.
    
    Returns:
        Path to compiler or None if not found
    """
    compilers = ["clang++", "g++", "c++"]
    
    for compiler in compilers:
        if shutil.which(compiler):
            return compiler
    
    return None


def get_cpp_compile_command(compiler: str, files: list) -> list:
    """Get compilation command for syntax checking.
    
    Args:
        compiler: Compiler executable name
        files: List of source files
        
    Returns:
        Command list for subprocess
    """
    return [compiler, "-std=c++17", "-fsyntax-only"] + [str(f) for f in files]
