"""Mach-O extractor using dwarfdump (for macOS)."""

import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional

from .base import IStructExtractor
from ...struct_data.struct_info import StructInfo
from ...struct_data.member_info import MemberInfo


class MachoExtractor(IStructExtractor):
    """Extract struct info from Mach-O files using dwarfdump (macOS)."""
    
    def extract(self, objfiles: List[Path]) -> List[StructInfo]:
        """Extract struct information from Mach-O object files."""
        all_structs = []
        
        for objfile in objfiles:
            try:
                structs = self._extract_from_file(objfile)
                all_structs.extend(structs)
            except Exception:
                continue
        
        return self._deduplicate_structs(all_structs)
    
    def supports_caching(self) -> bool:
        """Whether this extractor supports caching."""
        return True
    
    def _extract_from_file(self, objfile: Path) -> List[StructInfo]:
        """Extract structs from a single Mach-O file using dwarfdump."""
        result = subprocess.run(
            ['dwarfdump', str(objfile)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return []
        
        return self._parse_dwarfdump_output(result.stdout)
    
    def _parse_dwarfdump_output(self, output: str) -> List[StructInfo]:
        """Parse dwarfdump output to extract struct information."""
        structs = []
        lines = output.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Find structure type
            if 'DW_TAG_structure_type' in line or 'DW_TAG_class_type' in line:
                struct_info = self._parse_struct_die(lines, i)
                if struct_info:
                    structs.append(struct_info)
            
            i += 1
        
        return structs
    
    def _parse_struct_die(self, lines: List[str], start_idx: int) -> Optional[StructInfo]:
        """Parse a struct DIE from dwarfdump output."""
        name = None
        size = None
        file_path = None
        line_num = None
        members = []
        
        # Count spaces after colon for structure line
        struct_line = lines[start_idx]
        if ':' not in struct_line:
            return None
        after_colon = struct_line.split(':', 1)[1]
        struct_spaces = len(after_colon) - len(after_colon.lstrip())
        
        # Parse struct and children
        i = start_idx + 1
        while i < len(lines):
            line = lines[i]
            
            # Stop at next sibling (0x line with same or fewer spaces after colon)
            if ':' in line and line.lstrip().startswith('0x'):
                after_colon = line.split(':', 1)[1]
                current_spaces = len(after_colon) - len(after_colon.lstrip())
                if current_spaces <= struct_spaces:
                    break
            
            # Get struct name
            if 'DW_AT_name' in line and name is None:
                match = re.search(r'"([^"]+)"', line)
                if match:
                    name = match.group(1)
            
            # Get struct size
            if 'DW_AT_byte_size' in line and size is None:
                match = re.search(r'0x([0-9a-f]+)', line)
                if match:
                    size = int(match.group(1), 16)
                else:
                    match = re.search(r'\((\d+)\)', line)
                    if match:
                        size = int(match.group(1))
            
            # Get file
            if 'DW_AT_decl_file' in line and file_path is None:
                match = re.search(r'"([^"]+)"', line)
                if match:
                    file_path = match.group(1)
            
            # Get line number
            if 'DW_AT_decl_line' in line and line_num is None:
                match = re.search(r'\((\d+)\)', line)
                if match:
                    line_num = int(match.group(1))
            
            # Parse member
            if 'DW_TAG_member' in line:
                member = self._parse_member_die(lines, i)
                if member:
                    members.append(member)
            
            i += 1
        
        if name and size is not None:
            return StructInfo(
                name=name,
                size=size,
                members=tuple(members),
                file_path=file_path,
                line=line_num
            )
        
        return None
    
    def _parse_member_die(self, lines: List[str], start_idx: int) -> Optional[MemberInfo]:
        """Parse a member DIE from dwarfdump output."""
        name = None
        offset = None
        type_name = None
        type_size = None
        
        # Parse member attributes
        i = start_idx + 1
        while i < len(lines):
            line = lines[i]
            
            # Stop at next DIE
            if line and line[0] == '0' and 'DW_TAG' in line:
                break
            
            # Get member name
            if 'DW_AT_name' in line and name is None:
                match = re.search(r'"([^"]+)"', line)
                if match:
                    name = match.group(1)
            
            # Get offset
            if 'DW_AT_data_member_location' in line:
                match = re.search(r'0x([0-9a-f]+)', line)
                if match:
                    offset = int(match.group(1), 16)
                else:
                    match = re.search(r'\((\d+)\)', line)
                    if match:
                        offset = int(match.group(1))
            
            # Get type info (DW_AT_type shows type name and reference)
            if 'DW_AT_type' in line and type_name is None:
                # Format: DW_AT_type (0x0000006a "char")
                match = re.search(r'"([^"]+)"', line)
                if match:
                    type_name = match.group(1)
                    # Get size based on type
                    if type_name == 'char':
                        type_size = 1
                    elif type_name == 'short':
                        type_size = 2
                    elif type_name == 'int':
                        type_size = 4
                    elif type_name == 'long':
                        type_size = 8
                    elif type_name == 'float':
                        type_size = 4
                    elif type_name == 'double':
                        type_size = 8
                    else:
                        type_size = 4  # Default for unknown types
            
            i += 1
        
        if name and offset is not None and type_name and type_size:
            return MemberInfo(
                name=name,
                type=type_name,
                size=type_size,
                offset=offset,
                access_modifier="none"
            )
        
        return None
    
    def _deduplicate_structs(self, structs: List[StructInfo]) -> List[StructInfo]:
        """Remove duplicate structs."""
        seen = {}
        unique = []
        
        for struct in structs:
            key = (struct.name, struct.size, len(struct.members))
            if key not in seen:
                seen[key] = True
                unique.append(struct)
        
        return unique
