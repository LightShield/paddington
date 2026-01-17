"""Example of properly verified e2e test."""

import pytest
from pathlib import Path
from .base_e2e_proper import BaseE2ETest, E2ETestCase, StructExpectation


class TestProperVerification(BaseE2ETest):
    """E2E tests with proper verification."""
    
    @pytest.mark.e2e
    def test_simple_struct_optimization(self, tmp_path):
        """Test simple struct optimization with full verification."""
        test_case = E2ETestCase(
            name="simple_struct_optimization",
            cpp_code="""
            struct Simple {
                char a;      // 1 byte
                int b;       // 4 bytes
                char c;      // 1 byte
            };
            int main() { return 0; }
            """,
            flags={
                'apply': True,
                'output': 'file',
                'extractor': 'dwarf',
                'transformer': 'line-swap'
            },
            expected_structs=[
                StructExpectation(
                    name="Simple",
                    size_before=12,  # char(1) + pad(3) + int(4) + char(1) + pad(3)
                    size_after=8,    # int(4) + char(1) + char(1) + pad(2)
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],  # int first (largest)
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["APPLYING CHANGES"],
            expected_patches_count=None  # Using file output, not patches
        )
        
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_already_optimal_struct(self, tmp_path):
        """Test struct that's already optimal (no changes)."""
        test_case = E2ETestCase(
            name="already_optimal",
            cpp_code="""
            struct Optimal {
                double a;    // 8 bytes (largest first)
                int b;       // 4 bytes
                char c;      // 1 byte
            };
            int main() { return 0; }
            """,
            flags={
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Optimal",
                    size_before=16,  # Already optimal
                    size_after=16,   # No change
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['a', 'b', 'c'],  # Same order
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="no padding to save"
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"],
            expected_patches_count=0  # No optimization needed
        )
        
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_nested_struct_with_size_propagation(self, tmp_path):
        """Test nested structs with size propagation verification."""
        test_case = E2ETestCase(
            name="nested_struct_propagation",
            cpp_code="""
            struct Inner {
                char a;      // 1 byte
                int b;       // 4 bytes
                char c;      // 1 byte
            };
            struct Outer {
                char x;      // 1 byte
                Inner inner; // Size depends on Inner optimization
                int y;       // 4 bytes
            };
            int main() { return 0; }
            """,
            flags={
                'apply': True,
                'output': 'patch',
                'patch_dir': str(tmp_path / "patches"),
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Inner",
                    size_before=12,  # char + pad + int + char + pad
                    size_after=8,    # int + char + char + pad
                    member_order_before=['a', 'b', 'c'],
                    member_order_after=['b', 'a', 'c'],
                    padding_saved=4,
                    should_optimize=True
                ),
                StructExpectation(
                    name="Outer",
                    size_before=20,  # char + pad + Inner(12) + int
                    size_after=16,   # Inner(8) + int + char + pad (after Inner optimized)
                    member_order_before=['x', 'inner', 'y'],
                    member_order_after=['inner', 'y', 'x'],  # Reordered based on new Inner size
                    padding_saved=4,
                    should_optimize=True
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"],  # Default is dry-run
            expected_patches_count=2  # One patch per struct
        )
        
        self.run_test_case(test_case, tmp_path)
    
    @pytest.mark.e2e
    def test_min_savings_threshold(self, tmp_path):
        """Test minimum savings threshold skips small optimizations."""
        test_case = E2ETestCase(
            name="min_savings_threshold",
            cpp_code="""
            struct Small {
                char a;
                short b;  // Only 1 byte padding
            };
            int main() { return 0; }
            """,
            flags={
                'min_savings': 10,  # Require at least 10 bytes savings
                'extractor': 'dwarf'
            },
            expected_structs=[
                StructExpectation(
                    name="Small",
                    size_before=4,
                    size_after=4,  # Would save <10 bytes, so skipped
                    member_order_before=['a', 'b'],
                    member_order_after=['a', 'b'],  # No change
                    padding_saved=0,
                    should_optimize=False,
                    skip_reason="below threshold"
                )
            ],
            should_succeed=True,
            expected_output_contains=["DRY-RUN"],
            expected_patches_count=0
        )
        
        self.run_test_case(test_case, tmp_path)
    
    # Helper methods
    
    def compile_cpp(self, cpp_file, output_name="test.o"):
        """Compile C++ file."""
        obj_file = cpp_file.parent / output_name
        result = subprocess.run(
            ['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)],
            capture_output=True
        )
        assert result.returncode == 0, f"Compilation failed: {result.stderr.decode()}"
        return obj_file
    
    def run_optimize(self, obj_file, **kwargs):
        """Run paddingTON optimize command."""
        cmd = ['python', '__main__.py', str(obj_file)]
        
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
        if kwargs.get('verbose'):
            cmd.append('-vv')
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
    
    def extract_structs_from_dwarf(self, obj_file) -> Dict[str, Dict]:
        """Extract struct info from DWARF."""
        result = subprocess.run(
            ['dwarfdump', str(obj_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {}
        
        structs = {}
        lines = result.stdout.split('\n')
        current_struct = None
        
        for line in lines:
            if 'DW_TAG_structure_type' in line:
                current_struct = {'members': []}
            
            if current_struct is not None:
                if 'DW_AT_name' in line:
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        current_struct['name'] = match.group(1)
                
                if 'DW_AT_byte_size' in line:
                    match = re.search(r'0x([0-9a-f]+)', line)
                    if match:
                        current_struct['size'] = int(match.group(1), 16)
                    else:
                        match = re.search(r'\((\d+)\)', line)
                        if match:
                            current_struct['size'] = int(match.group(1))
                    
                    if 'name' in current_struct and 'size' in current_struct:
                        structs[current_struct['name']] = current_struct
                    current_struct = None
        
        return structs
    
    def verify_member_order_in_source(self, source_content, struct_name, expected_order):
        """Verify member order in source code."""
        struct_pattern = rf'struct\s+{struct_name}\s*\{{'
        match = re.search(struct_pattern, source_content)
        if not match:
            return False
        
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
        
        member_positions = {}
        for member in expected_order:
            match = re.search(rf'\b{member}\b', struct_body)
            if match:
                member_positions[member] = match.start()
        
        if len(member_positions) != len(expected_order):
            return False
        
        sorted_members = sorted(member_positions.items(), key=lambda x: x[1])
        actual_order = [m[0] for m in sorted_members]
        
        return actual_order == expected_order
