#!/usr/bin/env python3
"""Test script to verify error handling in optimize.py"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from implementation.user_interactions.optimize import run
from argparse import Namespace

def test_file_not_found():
    """Test FileNotFoundError handling"""
    print("Testing FileNotFoundError handling...")
    
    # Create a file that exists for discovery but will be deleted before processing
    with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as f:
        temp_file = f.name
        f.write(b"fake object file content")
    
    try:
        # Mock the pipeline to raise FileNotFoundError
        with patch('implementation.user_interactions.optimize.Pipeline') as mock_pipeline_class:
            mock_pipeline = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline
            mock_pipeline.run.side_effect = FileNotFoundError("File not found")
            
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
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    print()

def test_permission_error():
    """Test PermissionError handling"""
    print("Testing PermissionError handling...")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as f:
        temp_file = f.name
        f.write(b"fake object file content")
    
    try:
        # Mock the pipeline to raise PermissionError
        with patch('implementation.user_interactions.optimize.Pipeline') as mock_pipeline_class:
            mock_pipeline = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline
            mock_pipeline.run.side_effect = PermissionError("Permission denied")
            
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
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    print()

def test_unexpected_error():
    """Test unexpected error handling"""
    print("Testing unexpected error handling...")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as f:
        temp_file = f.name
        f.write(b"fake object file content")
    
    try:
        # Mock the pipeline to raise a generic Exception
        with patch('implementation.user_interactions.optimize.Pipeline') as mock_pipeline_class:
            mock_pipeline = MagicMock()
            mock_pipeline_class.return_value = mock_pipeline
            mock_pipeline.run.side_effect = Exception("Something went wrong")
            
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
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    print()

if __name__ == "__main__":
    test_file_not_found()
    test_permission_error()
    test_unexpected_error()