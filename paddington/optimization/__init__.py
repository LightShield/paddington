"""Optimization functionality."""
from .optimize import optimize_files
from .optimizer import is_leaf_struct, needs_optimization, get_optimal_member_order
from .rewriter import rewrite_struct_definition, rewrite_constructors

__all__ = [
    'optimize_files',
    'is_leaf_struct',
    'needs_optimization',
    'get_optimal_member_order',
    'rewrite_struct_definition',
    'rewrite_constructors'
]
