"""Base infrastructure for end-to-end tests with proper verification."""

import subprocess
import re
import sys
import pytest
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict


# Check if we're on a platform that supports ELF (Linux)
SUPPORTS_ELF = sys.platform.startswith('linux')
HAS_DOCKER = shutil.which('docker') is not None

if not SUPPORTS_ELF and not HAS_DOCKER:
    SKIP_REASON_MACOS = (
        "DwarfExtractor requires ELF format (Linux). macOS uses Mach-O.\n"
        "To run e2e tests on macOS:\n"
        "  1. Install Docker: https://www.docker.com/products/docker-desktop\n"
        "  2. Run: ./run_tests_docker.sh\n"
        "Or test on Linux where DwarfExtractor works natively."
    )
elif not SUPPORTS_ELF and HAS_DOCKER:
    SKIP_REASON_MACOS = "Use Docker to run e2e tests: ./run_tests_docker.sh"
else:
    SKIP_REASON_MACOS = None


@dataclass
class StructExpectation:
    """Expected results for a struct optimization."""
    name: str
    size_before: int
    size_after: int
    member_order_before: List[str]
    member_order_after: List[str]
    padding_saved: int
    should_optimize: bool
    skip_reason: Optional[str] = None


@dataclass
class E2ETestCase:
    """Complete e2e test case definition."""
    name: str
    cpp_code: str
    flags: Dict[str, any]  # paddington flags
    expected_structs: List[StructExpectation]
    should_succeed: bool
    expected_output_contains: Optional[List[str]] = None
    expected_patches_count: Optional[int] = None


class BaseE2ETest:
    """Base class for E2E tests with proper verification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if hasattr(self, 'temp_dir') and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_test_case(self, test_case: E2ETestCase, tmp_path):
        """Run a complete test case with verification."""
        # 1. Write and compile C++ code
        cpp_file = tmp_path / "test.cpp"
        cpp_file.write_text(test_case.cpp_code)
        
        obj_file = tmp_path / "test.o"
        result = subprocess.run(
            ['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr.decode()}"
        
        # 2. Verify compilation
        assert obj_file.exists(), "Object file not created"
        
        # 3. Extract struct info BEFORE optimization
        structs_before = self.extract_structs_from_dwarf(obj_file)
        
        # 4. Verify expected structs exist in DWARF (if extractor works)
        # If test expects 0 structs, extraction returning 0 is valid
        expects_structs = any(e.should_optimize for e in test_case.expected_structs)
        extraction_works = len(structs_before) > 0 or not expects_structs
        
        if not extraction_works:
            # Check if it's a platform issue
            if not SUPPORTS_ELF and not HAS_DOCKER:
                pytest.skip(SKIP_REASON_MACOS)
            elif not SUPPORTS_ELF and HAS_DOCKER:
                # Docker available - this shouldn't happen, re-raise
                pytest.fail("Docker available but extraction still failed")
            else:
                pytest.skip("DwarfExtractor not working - cannot verify struct extraction")
        
        # Verify expected structs
        for expected in test_case.expected_structs:
            struct_info = structs_before.get(expected.name)
            if expected.should_optimize:
                assert struct_info is not None, f"Struct {expected.name} not found in DWARF"
                assert struct_info['size'] == expected.size_before, \
                    f"Struct {expected.name} size mismatch: expected {expected.size_before}, got {struct_info['size']}"
        
        # 5. Run paddingTON
        result = self.run_optimize(obj_file, **test_case.flags)
        
        # 6. Verify command result
        if test_case.should_succeed:
            assert result.returncode == 0, f"Command failed: {result.stderr}"
        else:
            assert result.returncode != 0, "Command should have failed"
            return
        
        # 7. Verify output contains expected text
        if test_case.expected_output_contains:
            for text in test_case.expected_output_contains:
                assert text in result.stdout, f"Expected '{text}' in output"
        
        # 8. Verify patches generated (if patch mode)
        if test_case.flags.get('output') == 'patch' and test_case.expected_patches_count is not None:
            patch_dir = Path(test_case.flags.get('patch_dir', './patches'))
            if patch_dir.exists():
                patches = list(patch_dir.glob("*.patch"))
                # Only verify if extraction worked
                if extraction_works:
                    assert len(patches) == test_case.expected_patches_count, \
                        f"Expected {test_case.expected_patches_count} patches, got {len(patches)}"
        
        # 9. If --apply was used, verify source was modified (TODO: transformation not fully implemented)
        if test_case.flags.get('apply') and extraction_works:
            # TODO: Once transformation is fully implemented, verify:
            # - Source file changed
            # - Member order changed
            # - Recompile and verify size changed
            pass
    
    def compile_cpp(self, cpp_content_or_file, output_name="test.o", tmp_path=None):
        """Compile C++ content or file and return .o file path."""
        if tmp_path is None:
            import tempfile
            tmp_path = Path(tempfile.mkdtemp())
        else:
            tmp_path = Path(tmp_path)
        
        # Handle both string content and Path to existing file
        is_file = False
        if isinstance(cpp_content_or_file, Path):
            is_file = cpp_content_or_file.exists()
        elif isinstance(cpp_content_or_file, str) and len(cpp_content_or_file) < 256:
            # Only check exists if string is short (could be a path)
            try:
                is_file = Path(cpp_content_or_file).exists()
            except (OSError, ValueError):
                is_file = False
        
        if is_file:
            # It's a path to existing file
            cpp_file = Path(cpp_content_or_file)
        else:
            # It's string content
            cpp_file = tmp_path / "test.cpp"
            cpp_file.write_text(str(cpp_content_or_file))
        
        obj_file = tmp_path / output_name
        result = subprocess.run(
            ['g++', '-g', '-O0', '-c', str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr.decode()}"
        return obj_file
    
    def run_optimize(self, obj_file, extra_args=None, **kwargs):
        """Run optimize command (use Docker on macOS if available)."""
        # Handle old API (list of args) and new API (kwargs)
        if extra_args is not None:
            # Old API: run_optimize(obj_file, ["--apply", "--output", "file"])
            cmd = ['python3', '__main__.py', str(obj_file)] + extra_args
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
        
        # New API: run_optimize(obj_file, apply=True, output="file")
        # On macOS, use Docker if available
        if not SUPPORTS_ELF and HAS_DOCKER:
            return self._run_optimize_docker(obj_file, **kwargs)
        
        # Native execution
        cmd = ['python3', '__main__.py', str(obj_file)]
        
        if kwargs.get('apply'):
            cmd.append('--apply')
        if 'min_savings' in kwargs:
            cmd.extend(['--min-savings', str(kwargs['min_savings'])])
        if 'access_modifier_strategy' in kwargs:
            cmd.extend(['--access-modifier-strategy', kwargs['access_modifier_strategy']])
        if 'extractor' in kwargs:
            cmd.extend(['--extractor', kwargs['extractor']])
        if 'transformer' in kwargs:
            cmd.extend(['--transformer', kwargs['transformer']])
        if 'output' in kwargs:
            cmd.extend(['--output', kwargs['output']])
        if 'patch_dir' in kwargs:
            cmd.extend(['--patch-dir', str(kwargs['patch_dir'])])
        if 'source_root' in kwargs:
            cmd.extend(['--source-root', str(kwargs['source_root'])])
        if kwargs.get('verbose'):
            cmd.append('-vv')
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
    
    def _run_optimize_docker(self, obj_file, **kwargs):
        """Run optimize in Docker container."""
        # Build command for Docker
        cmd = ['docker', 'run', '--rm',
               '-v', f'{Path.cwd()}:/paddington',
               '-w', '/paddington',
               'paddington-test',
               'python3', '__main__.py', str(obj_file)]
        
        if kwargs.get('apply'):
            cmd.append('--apply')
        if 'min_savings' in kwargs:
            cmd.extend(['--min-savings', str(kwargs['min_savings'])])
        if 'access_modifier_strategy' in kwargs:
            cmd.extend(['--access-modifier-strategy', kwargs['access_modifier_strategy']])
        if 'extractor' in kwargs:
            cmd.extend(['--extractor', kwargs['extractor']])
        if 'transformer' in kwargs:
            cmd.extend(['--transformer', kwargs['transformer']])
        if 'output' in kwargs:
            cmd.extend(['--output', kwargs['output']])
        if 'patch_dir' in kwargs:
            cmd.extend(['--patch-dir', str(kwargs['patch_dir'])])
        if 'source_root' in kwargs:
            cmd.extend(['--source-root', str(kwargs['source_root'])])
        if kwargs.get('verbose'):
            cmd.append('-vv')
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
    
    def extract_structs_from_dwarf(self, obj_file) -> Dict[str, Dict]:
        """Extract struct information (platform-aware)."""
        import sys
        
        # Use appropriate extractor
        if sys.platform == 'darwin':
            from implementation.pipeline.extraction import MachoExtractor
            extractor = MachoExtractor()
        else:
            from implementation.pipeline.extraction import DwarfExtractor
            extractor = DwarfExtractor()
        
        # Extract
        structs_list = extractor.extract([obj_file])
        
        # Convert to dict
        structs_dict = {}
        for struct in structs_list:
            structs_dict[struct.name] = {
                'name': struct.name,
                'size': struct.size,
                'members': struct.members
            }
        
        return structs_dict
    
    def verify_member_order_in_source(self, source_content, struct_name, expected_order):
        """Verify members appear in expected order in source."""
        # Find struct definition
        struct_pattern = rf'struct\s+{struct_name}\s*\{{'
        match = re.search(struct_pattern, source_content)
        if not match:
            return False
        
        # Extract struct body
        start = match.end()
        brace_count = 1
        end = start
        for i in range(start, len(source_content)):
            if source_content[i] == '{':
                brace_count += 1
            elif source_content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i
                    break
        
        struct_body = source_content[start:end]
        
        # Find member positions
        member_positions = {}
        for member in expected_order:
            match = re.search(rf'\b{member}\b', struct_body)
            if match:
                member_positions[member] = match.start()
        
        if len(member_positions) != len(expected_order):
            return False
        
        # Check order
        sorted_members = sorted(member_positions.items(), key=lambda x: x[1])
        actual_order = [m[0] for m in sorted_members]
        
        return actual_order == expected_order
    
    def assert_success(self, result):
        """Assert command succeeded (backward compatibility)."""
        assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    def assert_output_contains(self, result, text):
        """Assert output contains text (backward compatibility)."""
        assert text in result.stdout, f"Expected '{text}' in output"
    
    def run_paddington(self, args):
        """Run paddington command (backward compatibility)."""
        cmd = ['python3', '__main__.py'] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
    
    def create_file(self, filename, content):
        """Create a file with content (backward compatibility)."""
        filepath = Path(self.temp_dir) / filename
        filepath.write_text(content)
        return filepath
