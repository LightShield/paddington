"""Detect struct/class usage sites in code."""

from typing import List, Tuple
import clang.cindex as clang
from .models import StructInfo


class UsageSite:
    """Represents a usage site of a struct/class."""

    def __init__(self, file_path: str, line: int, column: int, usage_type: str):
        self.file_path = file_path
        self.line = line
        self.column = column
        self.usage_type = usage_type  # 'aggregate', 'constructor', 'smart_ptr'


def find_aggregate_initializations(
    translation_unit: clang.TranslationUnit, struct_name: str
) -> List[UsageSite]:
    """Find aggregate initialization sites for a struct."""
    usages = []

    def visit(cursor):
        # Look for InitListExpr with our struct type
        if cursor.kind == clang.CursorKind.INIT_LIST_EXPR:
            # Check if this initializes our struct
            if (
                cursor.type.spelling == struct_name
                or cursor.type.spelling == f"struct {struct_name}"
            ):
                usages.append(
                    UsageSite(
                        file_path=str(cursor.location.file),
                        line=cursor.location.line,
                        column=cursor.location.column,
                        usage_type="aggregate",
                    )
                )

        for child in cursor.get_children():
            visit(child)

    visit(translation_unit.cursor)
    return usages


def find_constructor_calls(
    translation_unit: clang.TranslationUnit, struct_name: str
) -> List[UsageSite]:
    """Find constructor call sites for a struct."""
    usages = []

    def visit(cursor):
        # Look for CXXConstructExpr
        if cursor.kind == clang.CursorKind.CALL_EXPR:
            # Check if calling our struct's constructor
            if struct_name in cursor.spelling:
                usages.append(
                    UsageSite(
                        file_path=str(cursor.location.file),
                        line=cursor.location.line,
                        column=cursor.location.column,
                        usage_type="constructor",
                    )
                )

        for child in cursor.get_children():
            visit(child)

    visit(translation_unit.cursor)
    return usages


def count_usages(translation_unit: clang.TranslationUnit, struct_name: str) -> int:
    """Count total usage sites for a struct."""
    aggregate = find_aggregate_initializations(translation_unit, struct_name)
    constructor = find_constructor_calls(translation_unit, struct_name)
    return len(aggregate) + len(constructor)
