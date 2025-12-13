"""Data models for struct analysis."""
from dataclasses import dataclass
from typing import List

@dataclass
class MemberInfo:
    name: str
    type_name: str
    size: int
    alignment: int
    offset: int

@dataclass
class StructInfo:
    name: str
    file_path: str
    line: int
    members: List[MemberInfo]
    total_size: int
    is_class: bool = False  # True for class, False for struct
    is_template: bool = False  # True for template definitions
    
    def calculate_padding(self) -> int:
        """Calculate total padding bytes in struct."""
        if not self.members:
            return 0
        
        padding = 0
        for i, member in enumerate(self.members):
            if i == 0:
                padding += member.offset
            else:
                prev = self.members[i-1]
                expected_offset = prev.offset + prev.size
                actual_offset = member.offset
                padding += actual_offset - expected_offset
        
        # Padding at end
        last_member = self.members[-1]
        data_end = last_member.offset + last_member.size
        padding += self.total_size - data_end
        
        return padding
    
    def calculate_optimal_size(self) -> int:
        """Calculate size if members were optimally ordered (largest to smallest)."""
        if not self.members:
            return 0
        
        sorted_members = sorted(self.members, key=lambda m: (m.size, m.alignment), reverse=True)
        
        offset = 0
        max_align = max(m.alignment for m in sorted_members)
        
        for member in sorted_members:
            if offset % member.alignment != 0:
                offset += member.alignment - (offset % member.alignment)
            offset += member.size
        
        if offset % max_align != 0:
            offset += max_align - (offset % max_align)
        
        return offset
