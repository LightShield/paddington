"""Data models for struct analysis."""

from dataclasses import dataclass
from typing import List, Set, Optional

__all__ = ["MemberInfo", "StructInfo"]


@dataclass
class MemberInfo:
    """Information about a struct/class member field.

    Attributes:
        name: Member variable name
        type: C++ type name (e.g., 'int', 'double', 'MyClass')
        size: Size in bytes
        offset: Byte offset from start of struct
    """

    name: str
    type: str
    size: int
    offset: int


@dataclass
class StructInfo:
    """Information about a struct/class definition.

    Attributes:
        name: Struct/class name
        size: Total size in bytes
        members: List of member fields
        file_path: Source file where struct is defined
        line: Line number where struct is defined
    """

    name: str
    size: int
    members: List[MemberInfo]
    file_path: Optional[str] = None
    line: Optional[int] = None

    def calculate_padding(self) -> int:
        """Calculate total padding bytes in struct.

        Returns:
            Total padding in bytes (includes internal padding and trailing padding)
        """
        if not self.members:
            return 0

        padding = 0
        for i, member in enumerate(self.members):
            if i == 0:
                padding += member.offset
            else:
                prev = self.members[i - 1]
                expected_offset = prev.offset + prev.size
                actual_offset = member.offset
                padding += actual_offset - expected_offset

        # Padding at end
        last_member = self.members[-1]
        data_end = last_member.offset + last_member.size
        padding += self.size - data_end

        return padding

    def calculate_optimal_size(self) -> int:
        """Calculate size if members were optimally ordered (largest to smallest).

        Returns:
            Optimal size in bytes with members ordered by size descending
        """
        if not self.members:
            return 0

        sorted_members = sorted(
            self.members, key=lambda m: (m.size, -m.offset), reverse=True
        )

        offset = 0
        max_align = max(m.size for m in sorted_members)  # Approximate alignment

        for member in sorted_members:
            align = member.size
            if offset % align != 0:
                offset += align - (offset % align)
            offset += member.size

        if offset % max_align != 0:
            offset += max_align - (offset % max_align)

        return offset

    def is_leaf(self, all_struct_names: Set[str]) -> bool:
        """Check if struct is a leaf (no members are other structs).
        
        Args:
            all_struct_names: Set of all known struct/class names
            
        Returns:
            True if all members are primitive types
        """
        return all(m.type not in all_struct_names for m in self.members)

    def get_dependencies(self, all_struct_names: Set[str]) -> Set[str]:
        """Get set of struct names this struct depends on.
        
        Args:
            all_struct_names: Set of all known struct/class names
            
        Returns:
            Set of struct names used as member types
        """
        return {m.type for m in self.members if m.type in all_struct_names}
