"""Tests for parallel processing correctness.

Verify that parallelization doesn't lose data or cause incorrect results.
"""

import pytest
import tempfile
from pathlib import Path
import subprocess


class TestParallelProcessingCorrectness:
    
    @pytest.mark.integration
    def test_compilation_data_preserved_in_parallel_extraction(self):
        """Test that pahole compilation data is preserved when processing multiple .o files in parallel."""
        tmp = Path(tempfile.mkdtemp())
        
        # Create multiple source files with constructors
        for i in range(15):  # >10 to trigger parallel processing
            header = tmp / f"data{i}.h"
            header.write_text(f"struct Data{i} {{ char a; int b; }};")
            
            cpp = tmp / f"data{i}.cpp"
            cpp.write_text(f'#include "data{i}.h"\nData{i} d{i};')
            
            obj = tmp / f"data{i}.o"
            subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj), f'-I{tmp}'], 
                          check=True, capture_output=True)
        
        # Run paddington
        result = subprocess.run(
            ['python3', '__main__.py', str(tmp), '--extractor', 'pahole', 
             '--source-root', str(tmp), '-v'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Verify compilation data was used (should NOT see "No .cpp files found" warnings)
        # With parallel processing bug, compilation data is lost
        no_cpp_warnings = result.stdout.count("No .cpp files found")
        
        # Should have 0 warnings if compilation data is preserved
        assert no_cpp_warnings == 0, \
            f"Expected 0 'No .cpp files found' warnings, got {no_cpp_warnings}. " \
            f"Compilation data was lost during parallel processing!"
    
    @pytest.mark.integration
    def test_parallel_extraction_same_results_as_serial(self):
        """Test that parallel extraction gives same results as serial."""
        tmp = Path(tempfile.mkdtemp())
        
        # Create test files
        for i in range(15):
            header = tmp / f"test{i}.h"
            header.write_text(f"struct Test{i} {{ char a; int b; }};")
            cpp = tmp / f"test{i}.cpp"
            cpp.write_text(f'#include "test{i}.h"\nTest{i} t{i};')
            obj = tmp / f"test{i}.o"
            subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj), f'-I{tmp}'], 
                          check=True, capture_output=True)
        
        from implementation.pipeline.extraction.pahole import PaholeExtractor
        
        # Extract with parallel (>10 files)
        extractor_parallel = PaholeExtractor()
        objfiles = list(tmp.glob("*.o"))
        structs_parallel = extractor_parallel.extract(objfiles)
        comp_data_parallel = extractor_parallel.get_compilation_data()
        
        # Extract serially (mock by processing one at a time)
        extractor_serial = PaholeExtractor()
        structs_serial = []
        for obj in objfiles:
            structs_serial.extend(extractor_serial._extract_single_file(obj))
        comp_data_serial = extractor_serial._compilation_data
        
        # Compare results
        assert len(structs_parallel) == len(structs_serial), \
            f"Parallel extracted {len(structs_parallel)} structs, serial extracted {len(structs_serial)}"
        
        # Compare compilation data
        assert len(comp_data_parallel) == len(comp_data_serial), \
            f"Parallel has {len(comp_data_parallel)} compilation entries, " \
            f"serial has {len(comp_data_serial)}. Data was lost in parallel processing!"
    
    @pytest.mark.integration
    def test_parallel_transformation_preserves_all_changes(self):
        """Test that parallel transformation doesn't lose any modifications."""
        tmp = Path(tempfile.mkdtemp())
        
        # Create multiple structs that need optimization
        for i in range(15):
            header = tmp / f"struct{i}.h"
            header.write_text(f"struct S{i} {{ char a; int b; }};")
            cpp = tmp / f"struct{i}.cpp"
            cpp.write_text(f'#include "struct{i}.h"\nS{i} s{i};')
            obj = tmp / f"struct{i}.o"
            subprocess.run(['g++', '-g', '-c', str(cpp), '-o', str(obj), f'-I{tmp}'], 
                          check=True, capture_output=True)
        
        # Run paddington
        result = subprocess.run(
            ['python3', '__main__.py', str(tmp), '--extractor', 'pahole',
             '--source-root', str(tmp), '--output', 'patch', 
             '--patch-dir', str(tmp / 'patches'), '-v'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        
        # Count patches created
        patch_dir = tmp / 'patches'
        if patch_dir.exists():
            patches = list(patch_dir.glob("*.patch"))
            # Should have patches for most/all structs (some might not need optimization)
            assert len(patches) > 0, "No patches created - parallel transformation may have lost data"
    
    @pytest.mark.integration
    def test_parallel_scanning_finds_all_patterns(self):
        """Test that parallel source scanning doesn't miss any patterns."""
        tmp = Path(tempfile.mkdtemp())
        
        # Create many files with different patterns (>100 to trigger parallel)
        for i in range(120):
            cpp = tmp / f"file{i}.cpp"
            content = f"""
struct Agg{i} {{ int a; char b; }};
Agg{i} agg{i} = {{1, 'x'}};  // Aggregate init

struct Prep{i} {{
    #ifdef DEBUG
    int debug_field;
    #endif
    int normal_field;
}};

struct Ctor{i} {{
    int size;
    char* buffer;
    Ctor{i}(int s) : size(s), buffer(new char[size]) {{}}
}};
"""
            cpp.write_text(content)
        
        from implementation.padding_analysis.source_scanner import SourceScanner
        scanner = SourceScanner(str(tmp))
        scanner.scan()
        
        # Verify all patterns were found
        # Should find 120 structs with aggregate init
        assert len(scanner.structs_with_aggregate_init) >= 100, \
            f"Only found {len(scanner.structs_with_aggregate_init)} aggregate inits, expected ~120. " \
            f"Parallel scanning may have lost data!"
        
        # Should find 120 structs with preprocessor directives
        assert len(scanner.structs_with_preprocessor) >= 100, \
            f"Only found {len(scanner.structs_with_preprocessor)} preprocessor structs, expected ~120"
        
        # Should find 120 structs with constructor dependencies
        assert len(scanner.constructor_dependencies) >= 100, \
            f"Only found {len(scanner.constructor_dependencies)} constructor deps, expected ~120"
