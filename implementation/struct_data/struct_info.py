"""StructInfo dataclass for struct information."""

from dataclasses import dataclass
from typing import Optional, Tuple, Set

from .member_info import MemberInfo


@dataclass(frozen=True)
class StructInfo:
    """Immutable information about a struct."""
    
    name: str
    size: int
    members: Tuple[MemberInfo, ...]
    file_path: Optional[str] = None
    line: Optional[int] = None
    optimized_size: Optional[int] = None
    ignore: bool = False
    ignore_reason: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate struct info after initialization."""
        if self.size < 0:
            raise ValueError(f"Size cannot be negative: {self.size}")
        if self.line is not None and self.line < 1:
            raise ValueError(f"Line number must be positive: {self.line}")
        if self.optimized_size is not None and self.optimized_size < 0:
            raise ValueError(f"Optimized size cannot be negative: {self.optimized_size}")
    
    def calculate_padding(self) -> int:
        """Calculate total padding bytes in the struct."""
        if not self.members:
            return self.size
        
        total_member_size = sum(member.size for member in self.members)
        return self.size - total_member_size
    
    def is_leaf(self) -> bool:
        """Check if this struct has no dependencies on other structs."""
        for member in self.members:
            if self._is_struct_type(member.type):
                return False
        return True
    
    def get_dependencies(self) -> Set[str]:
        """Get set of struct types this struct depends on."""
        dependencies = set()
        for member in self.members:
            if self._is_struct_type(member.type):
                dependencies.add(self._extract_struct_name(member.type))
        return dependencies
    
    def _is_struct_type(self, type_name: str) -> bool:
        """Check if a type name represents a struct type."""
        # Simple heuristic: struct types typically don't contain basic type keywords
        basic_types = {"int", "char", "float", "double", "bool", "void", "short", "long"}
        clean_type = type_name.strip().split()[0].rstrip("*&[]")
        return clean_type not in basic_types and not clean_type.startswith("std::")
    
    def _extract_struct_name(self, type_name: str) -> str:
        """Extract struct name from type string."""
        return type_name.strip().split()[0].rstrip("*&[]")