"""Tests for DWARF-based struct extraction."""

import subprocess
import tempfile
from pathlib import Path
import pytest
from paddington.core.models import MemberInfo, StructInfo
from paddington.core.dwarf_parser import parse_object_files, identify_leaves_and_order


@pytest.fixture
def simple_struct_obj():
    """Compile simple struct test case."""
    code = """
    struct Simple {
        char a;
        int b;
        char c;
    };
    
    int main() {
        Simple s;
        return 0;
    }
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(code)
        cpp_file = Path(f.name)
    
    obj_file = cpp_file.with_suffix('.o')
    subprocess.run(['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)], check=True)
    
    yield obj_file
    
    cpp_file.unlink(missing_ok=True)
    obj_file.unlink(missing_ok=True)


@pytest.fixture
def nested_struct_obj():
    """Compile nested struct test case."""
    code = """
    struct Inner {
        char a;
        int b;
    };
    
    struct Outer {
        int x;
        Inner inner;
        double y;
    };
    
    int main() {
        Outer o;
        return 0;
    }
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(code)
        cpp_file = Path(f.name)
    
    obj_file = cpp_file.with_suffix('.o')
    subprocess.run(['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)], check=True)
    
    yield obj_file
    
    cpp_file.unlink(missing_ok=True)
    obj_file.unlink(missing_ok=True)


@pytest.fixture
def template_obj():
    """Compile template test case."""
    code = """
    template<typename T>
    struct Container {
        T value;
        int count;
    };
    
    int main() {
        Container<int> c1;
        Container<double> c2;
        return 0;
    }
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(code)
        cpp_file = Path(f.name)
    
    obj_file = cpp_file.with_suffix('.o')
    subprocess.run(['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)], check=True)
    
    yield obj_file
    
    cpp_file.unlink(missing_ok=True)
    obj_file.unlink(missing_ok=True)


def test_simple_struct_extraction(simple_struct_obj):
    """Test extracting simple struct with padding."""
    structs = parse_object_files([simple_struct_obj])
    
    assert len(structs) == 1
    simple = structs[0]
    
    assert simple.name == "Simple"
    assert simple.size == 12
    assert len(simple.members) == 3
    
    # Check members
    assert simple.members[0].name == "a"
    assert simple.members[0].type == "char"
    assert simple.members[0].size == 1
    assert simple.members[0].offset == 0
    
    assert simple.members[1].name == "b"
    assert simple.members[1].type == "int"
    assert simple.members[1].size == 4
    assert simple.members[1].offset == 4
    
    assert simple.members[2].name == "c"
    assert simple.members[2].type == "char"
    assert simple.members[2].size == 1
    assert simple.members[2].offset == 8
    
    # Check padding calculation
    padding = simple.calculate_padding()
    assert padding == 6  # 3 bytes after 'a', 3 bytes trailing


def test_nested_struct_extraction(nested_struct_obj):
    """Test extracting nested structs."""
    structs = parse_object_files([nested_struct_obj])
    
    assert len(structs) == 2
    
    # Find structs by name
    inner = next(s for s in structs if s.name == "Inner")
    outer = next(s for s in structs if s.name == "Outer")
    
    # Check Inner
    assert inner.size == 8
    assert len(inner.members) == 2
    
    # Check Outer references Inner
    inner_member = next(m for m in outer.members if m.name == "inner")
    assert inner_member.type == "Inner"
    assert inner_member.size == 8


def test_leaf_identification(nested_struct_obj):
    """Test identifying leaf structs."""
    structs = parse_object_files([nested_struct_obj])
    all_names = {s.name for s in structs}
    
    inner = next(s for s in structs if s.name == "Inner")
    outer = next(s for s in structs if s.name == "Outer")
    
    assert inner.is_leaf(all_names) is True
    assert outer.is_leaf(all_names) is False


def test_dependency_ordering(nested_struct_obj):
    """Test bottom-up ordering of structs."""
    structs = parse_object_files([nested_struct_obj])
    ordered, visited = identify_leaves_and_order(structs)
    
    assert len(ordered) == 2
    assert len(visited) == 2
    
    # Inner should come before Outer (bottom-up)
    assert ordered[0].name == "Inner"
    assert ordered[1].name == "Outer"
    
    # All structs should be visited
    assert "Inner" in visited
    assert "Outer" in visited


def test_template_instantiations(template_obj):
    """Test that template instantiations are extracted as separate structs."""
    structs = parse_object_files([template_obj])
    
    assert len(structs) == 2
    
    names = {s.name for s in structs}
    assert "Container<int>" in names
    assert "Container<double>" in names
    
    # Check different sizes
    c_int = next(s for s in structs if s.name == "Container<int>")
    c_double = next(s for s in structs if s.name == "Container<double>")
    
    assert c_int.size == 8
    assert c_double.size == 16


def test_no_reoptimization_of_visited():
    """Test that visited structs are not reprocessed."""
    # Create simple dependency: A -> B -> C
    structs = [
        StructInfo(
            name="C",
            size=4,
            members=[MemberInfo("x", "int", 4, 0)]
        ),
        StructInfo(
            name="B",
            size=8,
            members=[MemberInfo("c", "C", 4, 0)]
        ),
        StructInfo(
            name="A",
            size=12,
            members=[MemberInfo("b", "B", 8, 0)]
        ),
    ]
    
    ordered, visited = identify_leaves_and_order(structs)
    
    # All should be visited exactly once
    assert len(visited) == 3
    assert len(ordered) == 3
    
    # Order should be C, B, A (bottom-up)
    assert ordered[0].name == "C"
    assert ordered[1].name == "B"
    assert ordered[2].name == "A"


def test_class_extraction():
    """Test that classes are extracted like structs."""
    code = """
    class MyClass {
    public:
        char a;
        int b;
    };
    
    int main() {
        MyClass obj;
        return 0;
    }
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(code)
        cpp_file = Path(f.name)
    
    obj_file = cpp_file.with_suffix('.o')
    subprocess.run(['g++', '-g', '-c', str(cpp_file), '-o', str(obj_file)], check=True)
    
    try:
        structs = parse_object_files([obj_file])
        assert len(structs) == 1
        assert structs[0].name == "MyClass"
    finally:
        cpp_file.unlink(missing_ok=True)
        obj_file.unlink(missing_ok=True)
