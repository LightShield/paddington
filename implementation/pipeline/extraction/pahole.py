"""Pahole extractor using pahole tool (Linux) or Docker (macOS)."""

import subprocess
import shutil
import re
from pathlib import Path
from typing import List, Optional

from .base import IStructExtractor
from ...struct_data.struct_info import StructInfo
from ...struct_data.member_info import MemberInfo
from ...utils import Logger


class PaholeExtractor(IStructExtractor):
    """Extract struct info using pahole (100x faster than DWARF parsing)."""
    
    def __init__(self):
        self.log = Logger()
        self._pahole_cmd = self._get_pahole_command()
    
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
        """Parse pahole -I -M output."""
        structs = []
        lines = output.splitlines()
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Source location: /* <offset> /path/file.h:line */
            loc_match = re.match(r'/\\*\\s*<[0-9a-f]+>\\s*(.+):(\\d+)\\s*\\*/', line)
            if loc_match:
                file_path = loc_match.group(1)
                line_num = int(loc_match.group(2))
                i += 1
                
                # Next line should be struct/class
                if i < len(lines):
                    struct_match = re.match(r'^(struct|class)\\s+(\\S+)\\s*\\{', lines[i])
                    if struct_match:
                        struct_name = struct_match.group(2)
                        i += 1
                        members = []
                        struct_size = 0
                        
                        while i < len(lines):
                            mline = lines[i]
                            
                            if mline.strip() == '};':
                                i += 1
                                break
                            
                            # Size line
                            size_match = re.search(r'/\\*\\s*size:\\s*(\\d+)', mline)
                            if size_match:
                                struct_size = int(size_match.group(1))
                                i += 1
                                continue
                            
                            # Skip holes, cacheline, access specifiers
                            if 'XXX' in mline or 'cacheline' in mline or mline.strip() in ['public:', 'protected:', 'private:', '']:
                                i += 1
                                continue
                            
                            # Member line: type name; /* offset size */
                            member_match = re.match(r'\\s+(\\S+)\\s+(\\S+);\\s*/\\*\\s*(\\d+)\\s+(\\d+)\\s*\\*/', mline)
                            if member_match:
                                member_type = member_match.group(1)
                                member_name = member_match.group(2)
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
