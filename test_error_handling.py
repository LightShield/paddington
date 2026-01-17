#!/usr/bin/env python3
"""Test script to verify error handling in optimize.py"""

import sys
import os
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from implementation.user_interactions.optimize import run
from argparse import Namespace

def test_file_not_found():
    """Test FileNotFoundError handling"""
    print("Testing FileNotFoundError handling...")
    
    args = Namespace(
        path="nonexistent.o",
        apply=False,
        min_savings=1,
        access_modifier_strategy="preserve",
        extractor="dwarf",
        transformer="line-swap",
        output="file",
        patch_dir=None,
        include=None,
        exclude=None,
        verbose=1
    )
    
    result = run(args)
    print(f"Result: {result}")
    print()

def test_permission_error():
    """Test PermissionError handling"""
    print("Testing PermissionError handling...")
    
    # Create a temporary file and make it unreadable
    with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as f:
        temp_file = f.name
        f.write(b"fake object file content")
    
    # Make file unreadable
    os.chmod(temp_file, 0o000)
    
    try:
        args = Namespace(
            path=temp_file,
            apply=False,
            min_savings=1,
            access_modifier_strategy="preserve",
            extractor="dwarf",
            transformer="line-swap",
            output="file",
            patch_dir=None,
            include=None,
            exclude=None,
            verbose=1
        )
        
        result = run(args)
        print(f"Result: {result}")
    finally:
        # Clean up
        os.chmod(temp_file, 0o644)
        os.unlink(temp_file)
    print()

def test_multiple_files_with_errors():
    """Test processing multiple files with some errors"""
    print("Testing multiple files with mixed success/error...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create one valid file and one that will cause an error
        valid_file = Path(temp_dir) / "valid.o"
        valid_file.write_bytes(b"fake object file")
        
        # Create directory with mixed files
        args = Namespace(
            path=temp_dir,
            apply=False,
            min_savings=1,
            access_modifier_strategy="preserve",
            extractor="dwarf",
            transformer="line-swap",
            output="file",
            patch_dir=None,
            include=None,
            exclude=None,
            verbose=1
        )
        
        result = run(args)
        print(f"Result: {result}")
    print()

if __name__ == "__main__":
    test_file_not_found()
    test_permission_error()
    test_multiple_files_with_errors()