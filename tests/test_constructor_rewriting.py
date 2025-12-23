"""Unit tests for constructor initializer list rewriting."""

import pytest
from paddington.optimization.rewriter import find_constructor_initializers, reorder_initializer_list
from paddington.core.models import MemberInfo


def test_inline_constructor_single_line():
    """Test: MyStruct() : a(1), b(2) {}"""
    content = "MyStruct() : a(1), b(2) {}"
    matches = find_constructor_initializers(content, "MyStruct")
    assert len(matches) == 1
    start, end, init_list = matches[0]
    assert "a(1), b(2)" in init_list


def test_inline_constructor_multiline():
    """Test: MyStruct() : a(1),\n      b(2) {}"""
    content = """MyStruct() : a(1),
      b(2) {}"""
    matches = find_constructor_initializers(content, "MyStruct")
    assert len(matches) == 1
    start, end, init_list = matches[0]
    assert "a(1)" in init_list and "b(2)" in init_list


def test_outline_constructor():
    """Test: MyStruct::MyStruct() : a(1), b(2) {}"""
    content = "MyStruct::MyStruct() : a(1), b(2) {}"
    matches = find_constructor_initializers(content, "MyStruct")
    assert len(matches) == 1
    start, end, init_list = matches[0]
    assert "a(1), b(2)" in init_list


def test_outline_constructor_multiline():
    """Test: MyStruct::MyStruct(...) : a(1),\n      b(2)\n{}"""
    content = """MyStruct::MyStruct(int x) : a(1),
      b(2)
{
    // body
}"""
    matches = find_constructor_initializers(content, "MyStruct")
    assert len(matches) == 1
    start, end, init_list = matches[0]
    assert "a(1)" in init_list and "b(2)" in init_list


def test_reorder_simple():
    """Test reordering a(1), b(2) -> b(2), a(1)"""
    init_list = "a(1), b(2)"
    new_order = [
        MemberInfo("b", "int", 4, 0),
        MemberInfo("a", "char", 1, 4)
    ]
    result = reorder_initializer_list(init_list, new_order)
    assert result == "b(2), a(1)"


def test_reorder_with_base_class():
    """Test: Base(x), a(1), b(2) -> Base(x), b(2), a(1)"""
    init_list = "Base(x), a(1), b(2)"
    new_order = [
        MemberInfo("b", "int", 4, 0),
        MemberInfo("a", "char", 1, 4)
    ]
    result = reorder_initializer_list(init_list, new_order)
    # Base class init should stay first
    assert result.startswith("Base(x)")
    assert "b(2)" in result
    assert "a(1)" in result


def test_replacement_preserves_formatting():
    """Test that replacement doesn't corrupt surrounding code"""
    content = """MyStruct::MyStruct() : a(1), b(2)
{
    doSomething();
}"""
    matches = find_constructor_initializers(content, "MyStruct")
    start, end, init_list = matches[0]
    
    new_init = "b(2), a(1)"
    result = content[:start] + new_init + content[end:]
    
    # Should preserve the newline and opening brace
    assert "b(2), a(1)\n{" in result or "b(2), a(1) {" in result
    assert "doSomething()" in result


def test_multiple_constructors():
    """Test multiple constructors in same file"""
    content = """
MyStruct::MyStruct() : a(1), b(2) {}
MyStruct::MyStruct(int x) : a(x), b(0) {}
"""
    matches = find_constructor_initializers(content, "MyStruct")
    assert len(matches) == 2


def test_constructor_with_body():
    """Test constructor with code in body - ensure body is preserved"""
    content = """axi_submaster_base::axi_submaster_base(int id)
    : m_snoop(NULL),
      m_id(id)
{

    m_snoop = getSomething(id);
}"""
    matches = find_constructor_initializers(content, "axi_submaster_base")
    assert len(matches) == 1
    start, end, init_list = matches[0]
    
    # Reorder: m_id before m_snoop
    new_order = [
        MemberInfo("m_id", "int", 4, 0),
        MemberInfo("m_snoop", "void*", 8, 4)
    ]
    new_init = reorder_initializer_list(init_list, new_order)
    result = content[:start] + new_init + content[end:]
    
    # Must preserve the opening brace and body
    assert "{" in result
    assert "m_snoop = getSomething(id)" in result
    # Should not corrupt the body
    assert "m_snoop = getSomething(id)" in result.split("{")[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
