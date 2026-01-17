"""Base class for end-to-end tests."""

import subprocess
import tempfile
from pathlib import Path


class BaseE2ETest:
    """Base class for E2E tests with common utilities."""
    
    def compile_cpp(self, code, tmpdir):
        """Compile C++ code and return .o file path."""
        tmpdir = Path(tmpdir)
        cpp_file = tmpdir / "test.cpp"
        cpp_file.write_text(code)
        
        obj_file = tmpdir / "test.o"
        result = subprocess.run(
            ['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        return obj_file
    
    def run_optimize(self, obj_file, **kwargs):
        """Run optimize command with given arguments."""
        cmd = ['python', '__main__.py', str(obj_file)]
        
        # Add optional arguments
        if kwargs.get('apply'):
            cmd.append('--apply')
        if 'extractor' in kwargs:
            cmd.extend(['--extractor', kwargs['extractor']])
        if 'transformer' in kwargs:
            cmd.extend(['--transformer', kwargs['transformer']])
        if 'output' in kwargs:
            cmd.extend(['--output', kwargs['output']])
        if 'patch_dir' in kwargs:
            cmd.extend(['--patch-dir', str(kwargs['patch_dir'])])
        if 'access_modifier_strategy' in kwargs:
            cmd.extend(['--access-modifier-strategy', kwargs['access_modifier_strategy']])
        if kwargs.get('verbose'):
            cmd.append('-vv')
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
    
    def assert_success(self, result):
        """Assert that command succeeded."""
        assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    def assert_output_contains(self, result, text):
        """Assert that output contains specified text."""
        assert text in result.stdout, f"Output missing '{text}': {result.stdout}"
    
    def get_struct_size_from_dwarf(self, obj_file, struct_name):
        """Extract struct size from DWARF debug info."""
        import re
        result = subprocess.run(
            ['dwarfdump', str(obj_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return None
        
        # Parse DWARF output for struct size
        lines = result.stdout.split('\n')
        in_struct = False
        for i, line in enumerate(lines):
            if 'DW_TAG_structure_type' in line:
                # Check next few lines for name
                for j in range(i, min(i+10, len(lines))):
                    if 'DW_AT_name' in lines[j] and struct_name in lines[j]:
                        in_struct = True
                    if in_struct and 'DW_AT_byte_size' in lines[j]:
                        # Extract size
                        match = re.search(r'0x([0-9a-f]+)', lines[j])
                        if match:
                            return int(match.group(1), 16)
                        match = re.search(r'\((\d+)\)', lines[j])
                        if match:
                            return int(match.group(1))
                in_struct = False
        
        return None
    
    def compile_and_get_size(self, code, tmpdir, struct_name):
        """Compile code and return struct size from DWARF."""
        obj_file = self.compile_cpp(code, tmpdir)
        return self.get_struct_size_from_dwarf(obj_file, struct_name)