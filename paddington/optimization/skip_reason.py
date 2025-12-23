"""Skip reasons for struct optimization."""

from enum import Enum


class SkipReason(Enum):
    """Reasons why a struct was skipped during optimization."""
    
    NO_MEMBERS = "no members found"
    ZERO_SIZE = "struct has zero size"
    ZERO_SIZE_MEMBER = "contains zero-size member (opaque type)"
    NO_PADDING = "no padding to optimize (already optimal)"
    NO_SOURCE_LOCATION = "no source file location in DWARF"
    SOURCE_NOT_FOUND = "source file not found on disk"
    MEMBER_NOT_FOUND = "could not find all member declarations in source"
    MEMBER_MULTIPLE_LINES = "member found on multiple lines (likely #ifdef)"
    
    def __str__(self):
        return self.value
