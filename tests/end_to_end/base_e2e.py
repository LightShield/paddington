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