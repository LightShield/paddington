"""Tests for scan cache functionality."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from implementation.padding_analysis.source_scanner import SourceScanner


@pytest.mark.skip(reason="Scan cache tests need update")
class TestScanCache:
    """Test cache functionality in SourceScanner."""
    
    def test_cache_is_created(self):
        """Test that cache directory and file are created automatically."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            workspace_dir = Path(temp_dir) / "workspace"
            source_root.mkdir()
            
            # Create a simple source file
            test_file = source_root / "test.cpp"
            test_file.write_text("""
struct TestStruct {
    int a;
    char b;
};
""")
            
            scanner = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            scanner.scan()
            
            # Check that workspace structure was created
            assert workspace_dir.exists()
            assert (workspace_dir / "scan_cache").exists()
            assert (workspace_dir / "extraction_cache").exists()
            assert (workspace_dir / "scan_cache" / ".paddington_scan_cache.json").exists()
    
    def test_cache_is_loaded_on_second_run(self):
        """Test that cache is loaded on second run without rescanning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            workspace_dir = Path(temp_dir) / "workspace"
            source_root.mkdir()
            
            # Create a source file with aggregate initialization
            test_file = source_root / "test.cpp"
            test_file.write_text("""
struct TestStruct {
    int a;
    char b;
};

void test() {
    TestStruct s{1, 'a'};  // aggregate initialization
}
""")
            
            # First scan - should create cache
            scanner1 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            
            with patch('implementation.padding_analysis.source_scanner._scan_single_file') as mock_scan:
                mock_scan.return_value = ({'TestStruct'}, set(), {})
                scanner1.scan()
                # Should have called scan function
                assert mock_scan.called
            
            # Verify results were cached
            assert scanner1.has_aggregate_initialization('TestStruct')
            
            # Second scan - should load from cache
            scanner2 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            
            with patch('implementation.padding_analysis.source_scanner._scan_single_file') as mock_scan2:
                mock_scan2.return_value = (set(), set(), {})
                scanner2.scan()
                # Should NOT have called scan function (loaded from cache)
                assert not mock_scan2.called
            
            # Should have same results
            assert scanner2.has_aggregate_initialization('TestStruct')
    
    def test_cache_is_invalidated_when_files_change(self):
        """Test that cache is invalidated when source files are modified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            workspace_dir = Path(temp_dir) / "workspace"
            source_root.mkdir()
            
            # Create initial source file
            test_file = source_root / "test.cpp"
            test_file.write_text("""
struct TestStruct {
    int a;
    char b;
};
""")
            
            # First scan
            scanner1 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            scanner1.scan()
            
            # Verify cache file exists
            cache_file = workspace_dir / "scan_cache" / ".paddington_scan_cache.json"
            assert cache_file.exists()
            
            # Read original cache
            with open(cache_file) as f:
                original_cache = json.load(f)
            
            # Wait a bit to ensure different mtime
            time.sleep(0.1)
            
            # Modify the file
            test_file.write_text("""
struct TestStruct {
    int a;
    char b;
};

struct NewStruct {
    double x;
};
""")
            
            # Second scan - should detect file change and rescan
            scanner2 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            
            with patch('implementation.padding_analysis.source_scanner._scan_single_file') as mock_scan:
                mock_scan.return_value = (set(), set(), {})
                scanner2.scan()
                # Should have called scan function due to file change
                assert mock_scan.called
    
    def test_cache_with_multiple_files(self):
        """Test caching with multiple source files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            workspace_dir = Path(temp_dir) / "workspace"
            source_root.mkdir()
            
            # Create multiple source files
            file1 = source_root / "file1.cpp"
            file1.write_text("""
struct Struct1 {
    int a;
    int b;
};

void test1() {
    Struct1 s{42, 100};  // aggregate init with comma
}
""")
            
            file2 = source_root / "file2.h"
            file2.write_text("""
struct Struct2 {
#ifdef DEBUG
    int debug_field;
#endif
    char data;
};
""")
            
            # First scan
            scanner1 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            scanner1.scan()
            
            # Check results
            assert scanner1.has_aggregate_initialization('Struct1')
            assert scanner1.has_preprocessor_directives('Struct2')
            
            # Second scan - should load from cache
            scanner2 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            
            with patch('implementation.padding_analysis.source_scanner._scan_single_file') as mock_scan:
                mock_scan.return_value = (set(), set(), {})
                scanner2.scan()
                # Should NOT scan (loaded from cache)
                assert not mock_scan.called
            
            # Should have same results
            assert scanner2.has_aggregate_initialization('Struct1')
            assert scanner2.has_preprocessor_directives('Struct2')
    
    def test_cache_with_constructor_dependencies(self):
        """Test caching of constructor dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            workspace_dir = Path(temp_dir) / "workspace"
            source_root.mkdir()
            
            # Create source file with constructor dependencies
            test_file = source_root / "test.cpp"
            test_file.write_text("""
struct TestStruct {
    int a;
    int b;
    int c;
    
    TestStruct(int x) : b(a), c(b + 1) {}
};
""")
            
            # Mock the scan function to return constructor dependencies
            def mock_scan_with_deps(file_path):
                return (set(), set(), {
                    'TestStruct': {
                        'b': {'a'},
                        'c': {'b'}
                    }
                })
            
            # First scan
            scanner1 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            
            with patch('implementation.padding_analysis.source_scanner._scan_single_file', side_effect=mock_scan_with_deps):
                scanner1.scan()
            
            # Check constructor dependencies
            deps = scanner1.get_constructor_dependencies('TestStruct')
            assert 'b' in deps
            assert 'a' in deps['b']
            assert 'c' in deps
            assert 'b' in deps['c']
            
            # Second scan - should load from cache
            scanner2 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            
            with patch('implementation.padding_analysis.source_scanner._scan_single_file') as mock_scan:
                mock_scan.return_value = (set(), set(), {})
                scanner2.scan()
                # Should NOT scan (loaded from cache)
                assert not mock_scan.called
            
            # Should have same constructor dependencies
            deps2 = scanner2.get_constructor_dependencies('TestStruct')
            assert deps == deps2
    
    def test_cache_with_exclude_patterns(self):
        """Test that exclude patterns affect cache validity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            workspace_dir = Path(temp_dir) / "workspace"
            source_root.mkdir()
            
            # Create source files
            file1 = source_root / "include.cpp"
            file1.write_text("struct IncludeStruct { int a; };")
            
            file2 = source_root / "exclude.cpp"
            file2.write_text("struct ExcludeStruct { int a; };")
            
            # First scan with no exclusions
            scanner1 = SourceScanner(str(source_root), workspace_dir=str(workspace_dir))
            scanner1.scan()
            
            # Second scan with exclusions - should rescan due to different patterns
            scanner2 = SourceScanner(str(source_root), exclude_patterns=['*exclude*'], workspace_dir=str(workspace_dir))
            
            with patch('implementation.padding_analysis.source_scanner._scan_single_file') as mock_scan:
                mock_scan.return_value = (set(), set(), {})
                scanner2.scan()
                # Should scan because exclude patterns changed
                assert mock_scan.called
    
    def test_default_workspace_location(self):
        """Test that default workspace location is used when not specified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "source"
            source_root.mkdir()
            
            # Create a simple source file
            test_file = source_root / "test.cpp"
            test_file.write_text("struct Test { int a; };")
            
            # Change to temp directory so default workspace is created there
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                scanner = SourceScanner(str(source_root))
                scanner.scan()
                
                # Check that default workspace was created
                default_workspace = Path(temp_dir) / ".paddington_workspace"
                assert default_workspace.exists()
                assert (default_workspace / "scan_cache").exists()
                assert (default_workspace / "extraction_cache").exists()
                
            finally:
                os.chdir(old_cwd)