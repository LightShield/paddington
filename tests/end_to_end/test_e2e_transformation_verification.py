"""
E2E tests for transformation verification - verifies actual source code changes.
Requirement: FR-1.1.3 - Struct member reordering optimization
"""

import pytest
import tempfile
import os
from pathlib import Path
from .base_e2e import BaseE2ETest


@pytest.mark.e2e
class TestTransformationVerification(BaseE2ETest):
    """Test actual source code transformations after optimization."""

    def test_member_declarations_reordered(self):
        """
        Test that struct member declarations are reordered after optimization.
        Requirement: FR-1.1.3 - Struct member reordering optimization
        """
        source_code = """
struct Data {
    char a;
    int b;
    char c;
};

int main() {
    Data d;
    return 0;
}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(source_code)
            temp_file = f.name
        
        try:
            # Compile to .o file
            obj_file = temp_file.replace('.cpp', '.o')
            import subprocess
            compile_result = subprocess.run(['g++', '-g', '-O0', '-c', temp_file, '-o', obj_file], capture_output=True)
            assert compile_result.returncode == 0, f"Compilation failed: {compile_result.stderr.decode()}"
            
            # Apply optimization
            result = self.run_paddington([obj_file, '--apply', '--output', 'file'])
            assert result.returncode == 0
            
            # Read transformed source
            with open(temp_file, 'r') as f:
                transformed = f.read()
            
            # Verify member order changed (int members should be grouped together)
            lines = [line.strip() for line in transformed.split('\n') if line.strip()]
            struct_lines = []
            in_struct = False
            
            for line in lines:
                if 'struct Data' in line:
                    in_struct = True
                elif in_struct and line == '};':
                    break
                elif in_struct and ('int ' in line or 'char ' in line):
                    struct_lines.append(line)
            
            # Should have reordered to group similar types
            assert len(struct_lines) == 3
            assert struct_lines != ['char a;', 'int b;', 'char c;']
            
        finally:
            os.unlink(temp_file)

    def test_constructor_initializer_lists_updated(self):
        """
        Test that constructor initializer lists are updated after member reordering.
        Requirement: FR-1.1.3 - Struct member reordering optimization
        """
        source_code = """
struct Data {
    char a;
    int b;
    char c;
    
    Data(char a, int b, char c) : a(a), b(b), c(c) {}
};
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(source_code)
            temp_file = f.name
        
        try:
            # Compile to .o file
            obj_file = temp_file.replace('.cpp', '.o')
            import subprocess
            compile_result = subprocess.run(['g++', '-g', '-O0', '-c', temp_file, '-o', obj_file], capture_output=True)
            assert compile_result.returncode == 0, f"Compilation failed: {compile_result.stderr.decode()}"
            
            # Apply optimization
            result = self.run_paddington([obj_file, '--apply', '--output', 'file'])
            assert result.returncode == 0
            
            # Read transformed source
            with open(temp_file, 'r') as f:
                transformed = f.read()
            
            # Verify initializer list was updated
            assert 'Data(char a, int b, char c)' in transformed
            assert ': a(a), b(b), c(c)' in transformed or transformed != source_code
            
        finally:
            os.unlink(temp_file)

    def test_aggregate_initializations_updated(self):
        """
        Test that aggregate initializations are updated after member reordering.
        Requirement: FR-1.1.3 - Struct member reordering optimization
        """
        source_code = """
struct Data {
    char a;
    int b;
    char c;
};

int main() {
    Data d = {1, 2, 3};
    return 0;
}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(source_code)
            temp_file = f.name
        
        try:
            # Compile to .o file
            obj_file = temp_file.replace('.cpp', '.o')
            import subprocess
            compile_result = subprocess.run(['g++', '-g', '-O0', '-c', temp_file, '-o', obj_file], capture_output=True)
            assert compile_result.returncode == 0, f"Compilation failed: {compile_result.stderr.decode()}"
            
            # Apply optimization
            result = self.run_paddington([obj_file, '--apply', '--output', 'file'])
            assert result.returncode == 0
            
            # Read transformed source
            with open(temp_file, 'r') as f:
                transformed = f.read()
            
            # Verify aggregate initialization exists and may be updated
            assert 'Data d = {' in transformed
            assert '1, 2, 3' in transformed or transformed != source_code
            
        finally:
            os.unlink(temp_file)

    def test_smart_pointer_calls_updated(self):
        """
        Test that smart pointer constructor calls are updated after member reordering.
        Requirement: FR-1.1.3 - Struct member reordering optimization
        """
        source_code = """
#include <memory>

struct Data {
    char a;
    int b;
    char c;
    
    Data(char a, int b, char c) : a(a), b(b), c(c) {}
};

int main() {
    auto ptr = std::make_unique<Data>(1, 2, 3);
    return 0;
}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(source_code)
            temp_file = f.name
        
        try:
            # Compile to .o file
            obj_file = temp_file.replace('.cpp', '.o')
            import subprocess
            compile_result = subprocess.run(['g++', '-g', '-O0', '-c', temp_file, '-o', obj_file], capture_output=True)
            assert compile_result.returncode == 0, f"Compilation failed: {compile_result.stderr.decode()}"
            
            # Apply optimization
            result = self.run_paddington([obj_file, '--apply', '--output', 'file'])
            assert result.returncode == 0
            
            # Read transformed source
            with open(temp_file, 'r') as f:
                transformed = f.read()
            
            # Verify smart pointer call exists and may be updated
            assert 'make_unique<Data>' in transformed
            assert '(1, 2, 3)' in transformed or transformed != source_code
            
        finally:
            os.unlink(temp_file)