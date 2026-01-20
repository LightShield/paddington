"""OptimizationPlan dataclass for struct optimization plans."""

from dataclasses import dataclass
from typing import Optional, Tuple

from .struct_info import StructInfo
from .member_info import MemberInfo


@dataclass(frozen=True)
class OptimizationPlan:
    """Immutable optimization plan for a struct."""
    
    struct: StructInfo
    original_order: Tuple[MemberInfo, ...]
    optimal_order: Tuple[MemberInfo, ...]
    padding_saved: int
    skip_reason: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate optimization plan after initialization."""
        if self.padding_saved < 0:
            # Auto-fix: negative padding means reordering makes it worse
            # Set to 0 and mark as skipped
            object.__setattr__(self, 'padding_saved', 0)
            if not self.skip_reason:
                object.__setattr__(self, 'skip_reason', f"reordering increases size by {-self.padding_saved} bytes")
        
        # Verify that original and optimal orders contain the same members
        original_names = {member.name for member in self.original_order}
        optimal_names = {member.name for member in self.optimal_order}
        if original_names != optimal_names:
            raise ValueError("Original and optimal orders must contain the same members")