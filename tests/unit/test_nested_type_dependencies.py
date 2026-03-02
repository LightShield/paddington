"""Test for nested type dependency detection."""
import pytest
from pathlib import Path
from implementation.padding_analysis.source_scanner import _scan_single_file


def test_nested_type_with_dependent_member(tmp_path):
    """Test that structs with members depending on nested types are detected."""
    source = tmp_path / "test.h"
    source.write_text("""
class MyClass {
public:
    // Member using nested type
    al_sc_fifo<tid_req_ent_info> m_fifo;
    
private:
    // Nested type definition
    struct tid_req_ent_info {
        int x;
        int y;
    };
};
""")
    
    agg, prep, ctor, static_const, nested = _scan_single_file(source)
    
    # Should detect nested types
    assert 'MyClass' in nested
    assert 'nested_struct' in nested['MyClass']


def test_nested_enum_is_safe(tmp_path):
    """Test that nested enums don't flag the struct."""
    source = tmp_path / "test.h"
    source.write_text("""
class MyClass {
public:
    enum Color { RED, BLUE };
    int m_value;
};
""")
    
    agg, prep, ctor, static_const, nested = _scan_single_file(source)
    
    # Should NOT detect nested types (enum is safe)
    assert 'MyClass' not in nested
