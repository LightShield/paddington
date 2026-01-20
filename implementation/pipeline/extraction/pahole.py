"""Pahole extractor using pahole tool (Linux) or Docker (macOS)."""

import subprocess
import shutil
import re
from pathlib import Path
from typing import List, Optional, Dict

from .base import IStructExtractor
from ...struct_data.struct_info import StructInfo
from ...struct_data.member_info import MemberInfo
from ...utils import Logger


class PaholeExtractor(IStructExtractor):
    """Extract struct info using pahole (100x faster than DWARF parsing)."""
    
    def __init__(self):
        self.log = Logger()
        self._pahole_cmd = self._get_pahole_command()
        self._compilation_data: Dict[str, List[str]] = {}
    
    def get_compilation_data(self) -> Dict[str, List[str]]:
        """Get compilation data mapping struct names to their .cpp files."""
        return self._compilation_data.copy()
    
    def _get_pahole_command(self) -> List[str]:
        """Get pahole command (native or Docker)."""
        # Try native pahole first
        if shutil.which('pahole'):
            return ['pahole']
        
        # Try Docker wrapper
        docker_script = Path(__file__).parent.parent.parent.parent / 'docker_pahole.sh'
        if docker_script.exists():
            return [str(docker_script)]
        
        raise FileNotFoundError('pahole not found. Install dwarves package or use Docker.')
    
    def extract(self, objfiles: List[Path]) -> List[StructInfo]:
        """Extract struct information from object files using pahole."""
        self.log.info(f"Extracting from {len(objfiles)} files using pahole")
        all_structs = []
        
        for i, objfile in enumerate(objfiles, 1):
            if i % 10 == 0 or i in [1, 100, 500, 1000]:
                self.log.info(f"  Processing: {i}/{len(objfiles)}")
            
            try:
                self.log.debug(f"Running pahole on {objfile.name}")
                cmd = self._pahole_cmd + ['-I', '-M', str(objfile)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.log.debug(f"  Skipped: pahole returned {result.returncode}")
                    continue
                
                structs = self._parse_pahole_output(result.stdout)
                all_structs.extend(structs)
                self.log.debug(f"  Found {len(structs)} structs")
            except Exception as e:
                self.log.debug(f"  Skipped: {type(e).__name__}: {e}")
                continue
        
        return self._deduplicate_structs(all_structs)
    
    def supports_caching(self) -> bool:
        """Whether this extractor supports caching."""
        return True
    
    def _parse_pahole_output(self, output: str) -> List[StructInfo]:
        """Parse pahole -I -M output and collect source file information."""
        structs = []
        lines = output.splitlines()
        i = 0
        
        # First pass: collect all source file locations for compilation data
        self._collect_source_file_mappings(output)
        
        while i < len(lines):
            line = lines[i]
            
            # Source location: /* <offset> /path/file.h:line */
            loc_match = re.match(r'/\*\s*<[0-9a-f]+>\s*(.+):(\d+)\s*\*/', line)
            if loc_match:
                file_path = loc_match.group(1)
                line_num = int(loc_match.group(2))
                
                # Skip built-in types with line 0
                if line_num == 0:
                    i += 1
                    continue
                
                i += 1
                
                # Next line should be struct/class
                if i < len(lines):
                    # Match struct/class with name, handle inheritance, typedef, templates
                    struct_match = re.match(r'^(struct|class)\s+(.+?)\s*\{', lines[i])
                    if struct_match:
                        # Extract struct name from complex declarations
                        full_decl = struct_match.group(2)
                        if ' : ' in full_decl:
                            # Inheritance: "Name : public Base" -> "Name"
                            struct_name = full_decl.split(' : ')[0].strip().split()[-1]
                        elif 'typedef' in full_decl:
                            # Typedef: "typedef Name Name" -> last word
                            struct_name = full_decl.strip().split()[-1]
                        else:
                            # Simple/template: "Name" or "Name<T>" -> first word
                            struct_name = full_decl.split()[0] if ' ' in full_decl else full_decl
                        i += 1
                        members = []
                        struct_size = 0
                        
                        while i < len(lines):
                            mline = lines[i]
                            
                            if mline.strip() == '};':
                                i += 1
                                break
                            
                            # Size line
                            size_match = re.search(r'/\*\s*size:\s*(\d+)', mline)
                            if size_match:
                                struct_size = int(size_match.group(1))
                                i += 1
                                continue
                            
                            # Skip holes, cacheline, access specifiers, vtable pointers
                            if 'XXX' in mline or 'cacheline' in mline or mline.strip() in ['public:', 'protected:', 'private:', ''] or '()(void)' in mline:
                                i += 1
                                continue
                            
                            # Member line: type name; /* offset size */
                            # Use non-greedy match to handle complex types with spaces
                            member_match = re.match(r'\s+(.+?)\s+(\S+);?\s*/\*\s*(\d+)\s+(\d+)\s*\*/', mline)
                            if member_match:
                                # Extract member name (last word, handle arrays like name[4])
                                full_member = member_match.group(1) + ' ' + member_match.group(2)
                                parts = full_member.split()
                                member_name = parts[-1].rstrip(';').split('[')[0]
                                member_type = ' '.join(parts[:-1])  # Type may have spaces
                                member_offset = int(member_match.group(3))
                                member_size = int(member_match.group(4))
                                
                                members.append(MemberInfo(
                                    name=member_name,
                                    type=member_type,
                                    size=member_size,
                                    offset=member_offset,
                                    access_modifier="none"
                                ))
                            
                            i += 1
                        
                        if struct_name and struct_size > 0:
                            structs.append(StructInfo(
                                name=struct_name,
                                size=struct_size,
                                members=tuple(members),
                                file_path=file_path,
                                line=line_num
                            ))
            
            i += 1
        
        return structs
    
    def _collect_source_file_mappings(self, output: str):
        """Collect source file mappings from pahole output for compilation data."""
        # Parse structs from output and map to potential .cpp files
        source_locations = {}
        lines = output.splitlines()
        
        # Extract struct names and their header locations from the output
        struct_info = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Source location: /* <offset> /path/file.h:line */
            loc_match = re.match(r'/\*\s*<[0-9a-f]+>\s*(.+):(\d+)\s*\*/', line)
            if loc_match:
                file_path = loc_match.group(1)
                line_num = int(loc_match.group(2))
                
                if line_num > 0 and i + 1 < len(lines):
                    next_line = lines[i + 1]
                    struct_match = re.match(r'^(struct|class)\s+(.+?)\s*\{', next_line)
                    if struct_match:
                        # Extract struct name
                        full_decl = struct_match.group(2)
                        if ' : ' in full_decl:
                            struct_name = full_decl.split(' : ')[0].strip().split()[-1]
                        elif 'typedef' in full_decl:
                            struct_name = full_decl.strip().split()[-1]
                        else:
                            struct_name = full_decl.split()[0] if ' ' in full_decl else full_decl
                        
                        struct_info.append((struct_name, file_path))
            i += 1
        
        # For each struct, try to find corresponding .cpp files
        for struct_name, header_path in struct_info:
            # Try to infer .cpp file from header path
            header_path_obj = Path(header_path)
            potential_cpp_files = []
            
            # Look for .cpp files with same base name in same directory
            base_name = header_path_obj.stem
            parent_dir = header_path_obj.parent
            
            for ext in ['.cpp', '.cc', '.cxx', '.C']:
                cpp_file = parent_dir / (base_name + ext)
                if cpp_file.exists():
                    potential_cpp_files.append(str(cpp_file))
            
            # Also look for common patterns like impl/ subdirectory
            impl_dir = parent_dir / 'impl'
            if impl_dir.exists():
                for ext in ['.cpp', '.cc', '.cxx', '.C']:
                    cpp_file = impl_dir / (base_name + ext)
                    if cpp_file.exists():
                        potential_cpp_files.append(str(cpp_file))
            
            # Look in src/ subdirectory
            src_dir = parent_dir / 'src'
            if src_dir.exists():
                for ext in ['.cpp', '.cc', '.cxx', '.C']:
                    cpp_file = src_dir / (base_name + ext)
                    if cpp_file.exists():
                        potential_cpp_files.append(str(cpp_file))
            
            # If no direct match found, create a heuristic mapping
            # This helps the planning stage know about the struct even without exact .cpp file
            if not potential_cpp_files:
                # Use header path but change extension to .cpp as a fallback
                fallback_cpp = header_path_obj.with_suffix('.cpp')
                potential_cpp_files = [str(fallback_cpp)]
            
            if potential_cpp_files:
                source_locations[struct_name] = potential_cpp_files
        
        # Store in compilation data
        self._compilation_data.update(source_locations)
        self.log.debug(f"Collected compilation data for {len(self._compilation_data)} structs")
    
    def _deduplicate_structs(self, structs: List[StructInfo]) -> List[StructInfo]:
        """Remove duplicate structs."""
        seen = {}
        unique = []
        
        for struct in structs:
            sig = (struct.name, struct.size, tuple((m.name, m.type, m.size, m.offset) for m in struct.members))
            if sig not in seen:
                seen[sig] = True
                unique.append(struct)
        
        self.log.debug(f"Deduplication: {len(structs)} -> {len(unique)} structs")
        return unique
