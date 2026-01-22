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
        all_structs = []
        
        # Use parallel processing for large file sets
        if len(objfiles) > 10:
            from multiprocessing import Pool, cpu_count
            import os
            
            # Use 80% of available cores
            num_workers = max(1, int(cpu_count() * 0.8))
            self.log.info(f"Extracting from {len(objfiles)} files using {num_workers} workers")
            
            # Process in parallel
            with Pool(num_workers) as pool:
                results = pool.map(self._extract_single_file, objfiles)
            
            # Flatten results
            for structs in results:
                if structs:
                    all_structs.extend(structs)
        else:
            # Serial processing for small sets
            for i, objfile in enumerate(objfiles, 1):
                if i % 100 == 0 or i == len(objfiles):
                    self.log.info(f"Extracting: {i}/{len(objfiles)} files")
                
                structs = self._extract_single_file(objfile)
                if structs:
                    all_structs.extend(structs)
        
        return self._deduplicate_structs(all_structs)
    
    def _extract_single_file(self, objfile: Path) -> List[StructInfo]:
        """Extract structs from a single .o file (for parallel processing)."""
        try:
            import os
            pid = os.getpid()
            self.log.debug(f"[PID {pid}] Processing {objfile.name}")
            cmd = self._pahole_cmd + ['-I', '-M', str(objfile)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log.debug(f"[PID {pid}] Skipped {objfile.name}: pahole error")
                return []
            
            structs = self._parse_pahole_output(result.stdout)
            self.log.debug(f"[PID {pid}] {objfile.name}: {len(structs)} structs")
            return structs
        except Exception as e:
            self.log.debug(f"[PID {pid}] Skipped {objfile.name}: {type(e).__name__}")
            return []
    
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
                            # Inheritance: take before colon
                            struct_name = full_decl.split(' : ')[0].strip()
                        elif 'typedef' in full_decl:
                            # Typedef: "typedef Name Name" -> last word
                            struct_name = full_decl.strip().split()[-1]
                        elif '<' in full_decl and '>' in full_decl:
                            # Template: keep whole thing (may have spaces/commas inside <>)
                            struct_name = full_decl.strip()
                        else:
                            # Simple: take first word
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
                            
                            # Skip holes, cacheline, access specifiers, vtable pointers, ancestor comments
                            if 'XXX' in mline or 'cacheline' in mline or mline.strip() in ['public:', 'protected:', 'private:', ''] or '()(void)' in mline or '<ancestor>' in mline:
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
                                
                                # Skip if member name is not a valid identifier (e.g., */ from comments)
                                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', member_name):
                                    i += 1
                                    continue
                                
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
        lines = output.splitlines()
        i = 0
        current_cpp_files = []
        
        while i < len(lines):
            line = lines[i]
            
            # Parse "Used at:" lines to find .cpp files
            used_at_match = re.match(r'/\*\s*Used at:\s*(.+?)\s*\*/', line)
            if used_at_match:
                file_path = used_at_match.group(1)
                # Check if it's a .cpp/.cc/.cxx file
                if any(file_path.endswith(ext) for ext in ['.cpp', '.cc', '.cxx', '.C']):
                    current_cpp_files.append(file_path)
                i += 1
                continue
            
            # Source location: /* <offset> /path/file.h:line */
            loc_match = re.match(r'/\*\s*<[0-9a-f]+>\s*(.+):(\d+)\s*\*/', line)
            if loc_match:
                line_num = int(loc_match.group(2))
                
                # Skip built-ins
                if line_num == 0:
                    current_cpp_files = []
                    i += 1
                    continue
                
                # Next line should be struct/class
                if i + 1 < len(lines):
                    struct_match = re.match(r'^(struct|class|union)\s+(.+?)\s*\{', lines[i + 1])
                    if struct_match:
                        # Extract struct name
                        full_decl = struct_match.group(2)
                        if ' : ' in full_decl:
                            struct_name = full_decl.split(' : ')[0].strip()
                        elif 'typedef' in full_decl:
                            struct_name = full_decl.strip().split()[-1]
                        elif '<' in full_decl and '>' in full_decl:
                            struct_name = full_decl.strip()
                        else:
                            # For non-template types with spaces, take first word
                            # But preserve full template names even if they have spaces
                            struct_name = full_decl.strip()
                        
                        # Associate cpp files with this struct
                        if current_cpp_files and struct_name:
                            if struct_name not in self._compilation_data:
                                self._compilation_data[struct_name] = []
                            self._compilation_data[struct_name].extend(current_cpp_files)
                        
                        # Reset for next struct
                        current_cpp_files = []
            
            i += 1
    
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
