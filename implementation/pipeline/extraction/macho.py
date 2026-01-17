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
        
        # Parse struct attributes - look ahead from structure_type line
        i = start_idx
        indent_level = len(lines[i]) - len(lines[i].lstrip())
        
        # Continue while we're in this DIE (same or deeper indentation)
        i += 1
        while i < len(lines):
            line = lines[i]
            
            # Stop if we hit a new top-level DIE (0x at start)
            if line.strip().startswith('0x') and 'DW_TAG' in line:
                # Check if it's a sibling (same level) or child (deeper)
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level:
                    break
            
            # Get name
            if 'DW_AT_name' in line and name is None:  # First name is struct name
                match = re.search(r'"([^"]+)"', line)
                if match:
                    name = match.group(1)
            
            # Get size
            if 'DW_AT_byte_size' in line and size is None:  # First size is struct size
                match = re.search(r'0x([0-9a-f]+)', line)
                if match:
                    size = int(match.group(1), 16)
                else:
                    match = re.search(r'\((\d+)\)', line)
                    if match:
                        size = int(match.group(1))
            
            # Get file (first occurrence)
            if 'DW_AT_decl_file' in line and file_path is None:
                match = re.search(r'"([^"]+)"', line)
                if match:
                    file_path = match.group(1)
            
            # Get line
            if 'DW_AT_decl_line' in line and line_num is None:
                match = re.search(r'\((\d+)\)', line)
                if match:
                    line_num = int(match.group(1))
            
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
        size = None
        type_name = "unknown"
        
        i = start_idx + 1
        while i < len(lines) and not (lines[i].strip().startswith('0x') and 'DW_TAG' in lines[i]):
            line = lines[i]
            
            if 'DW_AT_name' in line:
                match = re.search(r'"([^"]+)"', line)
                if match:
                    name = match.group(1)
            
            if 'DW_AT_data_member_location' in line:
                match = re.search(r'\((\d+)\)', line)
                if match:
                    offset = int(match.group(1))
            
            # Type info would require following DW_AT_type reference
            # For now, use placeholder
            
            i += 1
        
        # Estimate size from offset differences (simplified)
        if name and offset is not None:
            return MemberInfo(
                name=name,
                type=type_name,
                size=4,  # Placeholder - would need type resolution
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
