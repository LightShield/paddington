"""DwarfExtractor implementation using pyelftools."""

from pathlib import Path
from typing import List, Set
from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFRelocationError

from .base import IStructExtractor
from ...struct_data.struct_info import StructInfo
from ...struct_data.member_info import MemberInfo


class DwarfExtractor(IStructExtractor):
    """Extractor that uses pyelftools to extract struct information from DWARF debug info."""
    
    def extract(self, objfiles: List[Path]) -> List[StructInfo]:
        """Extract struct information from object files using DWARF debug info.
        
        Args:
            objfiles: List of paths to .o files
            
        Returns:
            List of StructInfo extracted from object files
        """
        all_structs = []
        
        for objfile in objfiles:
            try:
                structs = self._extract_from_file(objfile)
                all_structs.extend(structs)
            except (FileNotFoundError, ELFRelocationError, Exception):
                # Skip files with errors: no DWARF info, corrupted files, etc.
                continue
        
        return self._deduplicate_structs(all_structs)
    
    def supports_caching(self) -> bool:
        """Whether this extractor supports caching.
        
        Returns:
            True if caching is supported
        """
        return True
    
    def _extract_from_file(self, objfile: Path) -> List[StructInfo]:
        """Extract structs from a single object file."""
        structs = []
        
        with open(objfile, 'rb') as f:
            elf = ELFFile(f)
            
            if not elf.has_dwarf_info():
                return structs
            
            dwarf = elf.get_dwarf_info()
            
            for CU in dwarf.iter_CUs():
                for die in CU.iter_DIEs():
                    if die.tag in ['DW_TAG_structure_type', 'DW_TAG_class_type']:
                        struct = self._parse_struct(die, CU)
                        if struct:
                            structs.append(struct)
        
        return structs
    
    def _parse_struct(self, die, CU) -> StructInfo:
        """Parse a struct/class DIE."""
        name_attr = die.attributes.get('DW_AT_name')
        if not name_attr:
            return None
        
        name = name_attr.value
        if isinstance(name, bytes):
            name = name.decode()
        
        size_attr = die.attributes.get('DW_AT_byte_size')
        size = size_attr.value if size_attr else 0
        
        # Get source location
        file_path = None
        line = None
        
        if 'DW_AT_decl_file' in die.attributes:
            file_idx = die.attributes['DW_AT_decl_file'].value
            line_program = CU.dwarfinfo.line_program_for_CU(CU)
            if line_program and 0 < file_idx <= len(line_program['file_entry']):
                file_entry = line_program['file_entry'][file_idx - 1]
                file_path = file_entry.name.decode() if isinstance(file_entry.name, bytes) else file_entry.name
        
        if 'DW_AT_decl_line' in die.attributes:
            line = die.attributes['DW_AT_decl_line'].value
        
        # Extract members
        members = []
        for child in die.iter_children():
            if child.tag == 'DW_TAG_member':
                member = self._parse_member(child)
                if member:
                    members.append(member)
        
        return StructInfo(
            name=name,
            size=size,
            members=tuple(members),
            file_path=file_path,
            line=line
        )
    
    def _parse_member(self, die) -> MemberInfo:
        """Parse a member DIE."""
        name_attr = die.attributes.get('DW_AT_name')
        if not name_attr:
            return None
        
        name = name_attr.value
        if isinstance(name, bytes):
            name = name.decode()
        
        # Get type name (simplified - just use "unknown" for now)
        type_name = "unknown"
        
        # Get size (simplified - use 0 for now)
        size = 0
        
        # Get offset
        offset_attr = die.attributes.get('DW_AT_data_member_location')
        offset = offset_attr.value if offset_attr else 0
        
        return MemberInfo(
            name=name,
            type=type_name,
            size=size,
            offset=offset,
            access_modifier="public"  # Default for struct
        )
    
    def _deduplicate_structs(self, structs: List[StructInfo]) -> List[StructInfo]:
        """Deduplicate structs based on name, size, and member signature."""
        seen = set()
        unique = []
        
        for struct in structs:
            # Create signature for deduplication
            member_sig = tuple((m.name, m.type, m.size, m.offset) for m in struct.members)
            signature = (struct.name, struct.size, member_sig)
            
            if signature not in seen:
                seen.add(signature)
                unique.append(struct)
        
        return unique