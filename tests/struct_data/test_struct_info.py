"""Unit tests for StructInfo dataclass."""

import pytest

from implementation.struct_data.struct_info import StructInfo
from implementation.struct_data.member_info import MemberInfo


@pytest.mark.unit
class TestStructInfo:
    """Test cases for StructInfo dataclass."""
    
    def test_creation_with_required_fields(self):
        """Test creating StructInfo with required fields."""
        members = (
            MemberInfo("field1", "int", 4, 0, "public"),
            MemberInfo("field2", "char", 1, 4, "public"),
        )
        struct = StructInfo("TestStruct", 8, members)
        
        assert struct.name == "TestStruct"
        assert struct.size == 8
        assert struct.members == members
        assert struct.file_path is None
        assert struct.line is None
        assert struct.optimized_size is None
        assert struct.ignore is False
        assert struct.ignore_reason is None
    
    def test_creation_with_all_fields(self):
        """Test creating StructInfo with all fields."""
        members = (MemberInfo("field1", "int", 4, 0, "public"),)
        struct = StructInfo(
            name="TestStruct",
            size=8,
            members=members,
            file_path="/path/to/file.cpp",
            line=42,
            optimized_size=4,
            ignore=True,
            ignore_reason="User marked"
        )
        
        assert struct.name == "TestStruct"
        assert struct.size == 8
        assert struct.members == members
        assert struct.file_path == "/path/to/file.cpp"
        assert struct.line == 42
        assert struct.optimized_size == 4
        assert struct.ignore is True
        assert struct.ignore_reason == "User marked"
    
    def test_immutability(self):
        """Test that StructInfo is immutable."""
        members = (MemberInfo("field1", "int", 4, 0, "public"),)
        struct = StructInfo("TestStruct", 8, members)
        
        with pytest.raises(AttributeError):
            struct.name = "NewName"
    
    def test_negative_size(self):
        """Test validation of negative size."""
        members = (MemberInfo("field1", "int", 4, 0, "public"),)
        with pytest.raises(ValueError, match="Size cannot be negative"):
            StructInfo("TestStruct", -1, members)
    
    def test_invalid_line_number(self):
        """Test validation of line number."""
        members = (MemberInfo("field1", "int", 4, 0, "public"),)
        with pytest.raises(ValueError, match="Line number must be positive"):
            StructInfo("TestStruct", 8, members, line=0)
    
    def test_negative_optimized_size(self):
        """Test validation of negative optimized size."""
        members = (MemberInfo("field1", "int", 4, 0, "public"),)
        with pytest.raises(ValueError, match="Optimized size cannot be negative"):
            StructInfo("TestStruct", 8, members, optimized_size=-1)
    
    def test_calculate_padding_empty_struct(self):
        """Test padding calculation for empty struct."""
        struct = StructInfo("EmptyStruct", 1, ())
        assert struct.calculate_padding() == 1
    
    def test_calculate_padding_with_members(self):
        """Test padding calculation with members."""
        members = (
            MemberInfo("field1", "int", 4, 0, "public"),
            MemberInfo("field2", "char", 1, 4, "public"),
        )
        struct = StructInfo("TestStruct", 8, members)
        assert struct.calculate_padding() == 3  # 8 - (4 + 1)
    
    def test_is_leaf_with_basic_types(self):
        """Test is_leaf with only basic types."""
        members = (
            MemberInfo("field1", "int", 4, 0, "public"),
            MemberInfo("field2", "char", 1, 4, "public"),
            MemberInfo("field3", "double", 8, 8, "public"),
        )
        struct = StructInfo("TestStruct", 16, members)
        assert struct.is_leaf() is True
    
    def test_is_leaf_with_struct_types(self):
        """Test is_leaf with struct types."""
        members = (
            MemberInfo("field1", "int", 4, 0, "public"),
            MemberInfo("field2", "CustomStruct", 16, 4, "public"),
        )
        struct = StructInfo("TestStruct", 20, members)
        assert struct.is_leaf() is False
    
    def test_is_leaf_empty_struct(self):
        """Test is_leaf with empty struct."""
        struct = StructInfo("EmptyStruct", 1, ())
        assert struct.is_leaf() is True
    
    def test_get_dependencies_no_deps(self):
        """Test get_dependencies with no dependencies."""
        members = (
            MemberInfo("field1", "int", 4, 0, "public"),
            MemberInfo("field2", "char", 1, 4, "public"),
        )
        struct = StructInfo("TestStruct", 8, members)
        assert struct.get_dependencies() == set()
    
    def test_get_dependencies_with_deps(self):
        """Test get_dependencies with dependencies."""
        members = (
            MemberInfo("field1", "int", 4, 0, "public"),
            MemberInfo("field2", "CustomStruct", 16, 4, "public"),
            MemberInfo("field3", "AnotherStruct*", 8, 20, "public"),
        )
        struct = StructInfo("TestStruct", 28, members)
        deps = struct.get_dependencies()
        assert deps == {"CustomStruct", "AnotherStruct"}
    
    def test_is_struct_type_basic_types(self):
        """Test _is_struct_type with basic types."""
        struct = StructInfo("Test", 1, ())
        assert struct._is_struct_type("int") is False
        assert struct._is_struct_type("char") is False
        assert struct._is_struct_type("double") is False
        assert struct._is_struct_type("std::string") is False
    
    def test_is_struct_type_custom_types(self):
        """Test _is_struct_type with custom types."""
        struct = StructInfo("Test", 1, ())
        assert struct._is_struct_type("CustomStruct") is True
        assert struct._is_struct_type("MyClass*") is True
        assert struct._is_struct_type("SomeType&") is True
    
    def test_extract_struct_name(self):
        """Test _extract_struct_name method."""
        struct = StructInfo("Test", 1, ())
        assert struct._extract_struct_name("CustomStruct") == "CustomStruct"
        assert struct._extract_struct_name("MyClass*") == "MyClass"
        assert struct._extract_struct_name("SomeType&") == "SomeType"
        assert struct._extract_struct_name("ArrayType[]") == "ArrayType"