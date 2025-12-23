"""Build system integration for accurate type information."""

import json
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Dict, List, Optional
from ..utils import Logger


class BuildSystemTypeResolver:
    """Resolve actual type sizes using build system compilation."""
    
    def __init__(self, compile_commands_path: Optional[str] = None):
        self.compile_db = []
        self.log = Logger()
        
        if compile_commands_path and Path(compile_commands_path).exists():
            with open(compile_commands_path) as f:
                self.compile_db = json.load(f)
    
    def get_struct_sizes(self, file_path: str) -> Dict[str, int]:
        """Get actual struct sizes by compiling with real build flags."""
        
        # Find compilation entry
        compile_entry = self._find_compile_entry(file_path)
        if not compile_entry:
            self.log.debug(f"No compilation entry found for {file_path}")
            return {}
        
        # Extract struct names
        structs = self._extract_struct_names(file_path)
        if not structs:
            return {}
        
        # Create and compile size query program
        return self._get_sizes_via_compilation(file_path, structs, compile_entry)
    
    def _find_compile_entry(self, file_path: str) -> Optional[dict]:
        """Find compilation database entry for file."""
        file_path_resolved = Path(file_path).resolve()
        
        for entry in self.compile_db:
            entry_path = Path(entry.get('directory', '')) / entry['file']
            if entry_path.resolve() == file_path_resolved:
                return entry
        
        return None
    
    def _extract_struct_names(self, file_path: str) -> List[str]:
        """Extract struct/class names from source."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except:
            return []
        
        # Match struct/class definitions with bodies
        pattern = r'(?:struct|class)\s+(\w+)(?:\s*:\s*[^{]*)?[\s\n]*\{'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        # Filter out system types and template parameters
        return [name for name in set(matches) 
                if not name.startswith('_') and len(name) > 1]
    
    def _get_sizes_via_compilation(self, file_path: str, structs: List[str], 
                                  compile_entry: dict) -> Dict[str, int]:
        """Compile size query program and extract results."""
        
        # Create size query program
        program = self._create_size_program(file_path, structs)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(program)
            temp_cpp = f.name
        
        temp_exe = temp_cpp + '.exe'
        
        try:
            # Build compilation command from database entry
            compile_cmd = self._build_compile_command(compile_entry, temp_cpp, temp_exe)
            
            # Compile
            result = subprocess.run(compile_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.log.debug(f"Size query compilation failed: {result.stderr}")
                return {}
            
            # Run and parse
            run_result = subprocess.run([temp_exe], capture_output=True, text=True)
            if run_result.returncode != 0:
                return {}
            
            return self._parse_size_output(run_result.stdout)
            
        except Exception as e:
            self.log.debug(f"Size query failed: {e}")
            return {}
        finally:
            Path(temp_cpp).unlink(missing_ok=True)
            Path(temp_exe).unlink(missing_ok=True)
    
    def _create_size_program(self, original_file: str, structs: List[str]) -> str:
        """Create program to query struct sizes."""
        
        include_name = Path(original_file).name
        
        program = f'''
#include "{include_name}"
#include <iostream>

int main() {{
'''
        
        for struct_name in structs:
            program += f'''
    try {{
        std::cout << "SIZE:{struct_name}:" << sizeof({struct_name}) << std::endl;
    }} catch (...) {{}}
'''
        
        program += '''
    return 0;
}
'''
        return program
    
    def _build_compile_command(self, compile_entry: dict, source: str, output: str) -> List[str]:
        """Build compilation command from database entry."""
        
        args = compile_entry.get('arguments', [])[1:]  # Skip compiler name
        
        # Filter out problematic flags
        filtered_args = []
        skip_next = False
        
        for arg in args:
            if skip_next:
                skip_next = False
                continue
            
            if arg in ['-c', '-o']:
                skip_next = True
                continue
            
            if not (arg.endswith('.o') or arg.endswith('.cpp') or arg.endswith('.c')):
                filtered_args.append(arg)
        
        # Build final command
        return ['g++'] + filtered_args + [
            '-I' + str(Path(compile_entry['file']).parent),
            source, '-o', output
        ]
    
    def _parse_size_output(self, output: str) -> Dict[str, int]:
        """Parse size query output."""
        sizes = {}
        
        for line in output.strip().split('\n'):
            if line.startswith('SIZE:'):
                parts = line.split(':')
                if len(parts) == 3:
                    try:
                        sizes[parts[1]] = int(parts[2])
                    except ValueError:
                        pass
        
        return sizes
