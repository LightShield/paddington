"""Immutable data structures for paddingTON."""

from .member_info import MemberInfo
from .struct_info import StructInfo
from .optimization_plan import OptimizationPlan
from .source_change import SourceModification, TransformedSource, Modification, Location

__all__ = [
    "MemberInfo",
    "StructInfo", 
    "OptimizationPlan",
    "SourceModification",
    "TransformedSource",
    "Modification",
    "Location",
]