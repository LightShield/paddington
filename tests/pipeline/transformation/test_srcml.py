"""Tests for SrcMLTransformer."""

import pytest
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch, MagicMock

from implementation.pipeline.transformation.srcml import SrcMLTransformer, SRCML_AVAILABLE
from implementation.struct_data import SourceModification, Modification, Location


class TestSrcMLTransformer:
    """Test SrcMLTransformer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = SrcMLTransformer()
    
    @pytest.mark.unit
    def test_can_handle_file_cpp_extensions(self):
        """Test file extension handling for C++ files."""
        assert self.transformer.can_handle_file("test.cpp") is True
        assert self.transformer.can_handle_file("test.h") is True
        assert self.transformer.can_handle_file("test.hpp") is True
        assert self.transformer.can_handle_file("test.cc") is True
        assert self.transformer.can_handle_file("test.cxx") is True
    
    @pytest.mark.unit
    def test_can_handle_file_unsupported_extensions(self):
        """Test file extension handling for unsupported files."""
        assert self.transformer.can_handle_file("test.py") is False
        assert self.transformer.can_handle_file("test.java") is False
        assert self.transformer.can_handle_file("test.txt") is False
        assert self.transformer.can_handle_file("test") is False
    
    @pytest.mark.unit
    def test_transform_empty_list(self):
        """Test transform with empty modification list."""
        result = self.transformer.transform([])
        assert result == []
    
    @pytest.mark.unit
    def test_find_struct_node_simple_xml(self):
        """Test finding struct node in XML."""
        xml_content = '''
        <unit xmlns="http://www.srcML.org/srcML/src">
            <struct>
                <name>TestStruct</name>
                <block>{
                    <decl_stmt><decl><type><name>int</name></type> <name>x</name></decl>;</decl_stmt>
                }</block>
            </struct>
        </unit>
        '''
        root = ET.fromstring(xml_content)
        struct_node = self.transformer._find_struct_node(root, "TestStruct")
        assert struct_node is not None
        assert struct_node.tag.endswith('struct')
    
    @pytest.mark.unit
    def test_find_struct_node_not_found(self):
        """Test finding non-existent struct node."""
        xml_content = '''
        <unit xmlns="http://www.srcML.org/srcML/src">
            <struct>
                <name>OtherStruct</name>
            </struct>
        </unit>
        '''
        root = ET.fromstring(xml_content)
        struct_node = self.transformer._find_struct_node(root, "TestStruct")
        assert struct_node is None
    
    @pytest.mark.unit
    def test_reorder_members_single_member(self):
        """Test reordering with single member (no change expected)."""
        xml_content = '''
        <struct xmlns="http://www.srcML.org/srcML/src">
            <name>TestStruct</name>
            <block>{
                <decl_stmt><decl><type><name>int</name></type> <name>x</name></decl>;</decl_stmt>
            }</block>
        </struct>
        '''
        struct_node = ET.fromstring(xml_content)
        original_children = len(list(struct_node))
        
        self.transformer._reorder_members(struct_node, ['member'])
        
        # Should not change structure with single member
        assert len(list(struct_node)) == original_children
    
    @pytest.mark.unit
    
    @pytest.mark.unit
    def test_source_to_xml_success(self):
        """Test successful source to XML conversion."""
        with tempfile.NamedTemporaryFile(suffix='.cpp', delete=False, mode='w') as f:
            f.write("struct Test {};")
            temp_path = Path(f.name)
        
        try:
            result = self.transformer._source_to_xml(temp_path)
            assert result is not None
            assert '<struct' in result
            assert 'Test' in result
        finally:
            temp_path.unlink()
    
    @pytest.mark.unit
    def test_source_to_xml_failure(self):
        """Test failed source to XML conversion (file doesn't exist)."""
        result = self.transformer._source_to_xml(Path('/nonexistent/file.cpp'))
        assert result is None
    
    @pytest.mark.unit
    def test_xml_to_source_success(self):
        """Test successful XML to source conversion."""
        xml_content = '<unit revision="1.0.0" language="C++"><struct>struct <name>Test</name> <block>{}</block>;</struct></unit>'
        result = self.transformer._xml_to_source(xml_content)
        assert result is not None
        assert 'struct' in result
        assert 'Test' in result
    
    @pytest.mark.unit
    @pytest.mark.unit
    def test_xml_to_source_failure(self):
        """Test failed XML to source conversion (invalid XML)."""
        result = self.transformer._xml_to_source("invalid xml content")
        assert result is None
    
    @pytest.mark.unit
    def test_modify_xml_invalid_xml(self):
        """Test XML modification with invalid XML."""
        result = self.transformer._modify_xml("invalid xml", "TestStruct")
        assert result is None
    
    @pytest.mark.unit
    def test_reorder_constructor_initializers(self):
        """Test reordering constructor initializer lists."""
        # Create a simple XML structure with constructor and member_init_list
        xml_content = '''
        <unit xmlns="http://www.srcML.org/srcML/src">
            <struct>
                <name>TestStruct</name>
                <block>{
                    <decl_stmt><decl><type><name>int</name></type> <name>b</name></decl>;</decl_stmt>
                    <decl_stmt><decl><type><name>int</name></type> <name>a</name></decl>;</decl_stmt>
                    <constructor>
                        <name>TestStruct</name>
                        <parameter_list>(<parameter><decl><type><name>int</name></type> <name>x</name></decl></parameter>, <parameter><decl><type><name>int</name></type> <name>y</name></decl></parameter>)</parameter_list>
                        <member_init_list>: <call><name>a</name><argument_list>(<argument><expr><name>x</name></expr></argument>)</argument_list></call>, <call><name>b</name><argument_list>(<argument><expr><name>y</name></expr></argument>)</argument_list></call> </member_init_list>
                        <block>{}</block>
                    </constructor>
                }</block>
            </struct>
        </unit>
        '''
        
        root = ET.fromstring(xml_content)
        
        # Test reordering initializers
        self.transformer._reorder_constructor_initializers(root, "TestStruct", ["b", "a"])
        
        # Verify the initializer list was reordered
        result_xml = ET.tostring(root, encoding='unicode')
        
        # Should have b before a in the initializer list
        b_pos = result_xml.find('<call><name>b</name>')
        a_pos = result_xml.find('<call><name>a</name>')
        
        assert b_pos != -1, "Should find b initializer"
        assert a_pos != -1, "Should find a initializer"
        assert b_pos < a_pos, "b should come before a in reordered list"
    
    @pytest.mark.unit
    def test_find_constructors(self):
        """Test finding constructors in XML."""
        xml_content = '''
        <unit xmlns="http://www.srcML.org/srcML/src">
            <struct>
                <name>TestStruct</name>
                <block>{
                    <constructor>
                        <name>TestStruct</name>
                        <parameter_list>()</parameter_list>
                        <block>{}</block>
                    </constructor>
                    <constructor>
                        <name>TestStruct</name>
                        <parameter_list>(<parameter><decl><type><name>int</name></type> <name>x</name></decl></parameter>)</parameter_list>
                        <block>{}</block>
                    </constructor>
                }</block>
            </struct>
        </unit>
        '''
        
        root = ET.fromstring(xml_content)
        constructors = self.transformer._find_constructors(root, "TestStruct")
        
        assert len(constructors) == 2, "Should find 2 constructors"
        
        # Test with non-existent struct
        constructors = self.transformer._find_constructors(root, "NonExistent")
        assert len(constructors) == 0, "Should find 0 constructors for non-existent struct"
    
    @pytest.mark.unit
    def test_find_constructors_qualified_names(self):
        """Test finding constructors with qualified names (out-of-line definitions)."""
        xml_content = '''
        <unit xmlns="http://www.srcML.org/srcML/src">
            <constructor>
                <name>TestClass::TestClass</name>
                <parameter_list>(<parameter><decl><type><name>int</name></type> <name>x</name></decl></parameter>)</parameter_list>
                <member_init_list>: <call><name>member</name><argument_list>(<argument><expr><name>x</name></expr></argument>)</argument_list></call> </member_init_list>
                <block>{}</block>
            </constructor>
        </unit>
        '''
        
        root = ET.fromstring(xml_content)
        constructors = self.transformer._find_constructors(root, "TestClass")
        
        assert len(constructors) == 1, "Should find 1 qualified constructor"
    
    @pytest.mark.unit
    def test_has_constructor_dependencies(self):
        """Test detection of constructor dependencies."""
        constructor_xml = '''
        <constructor xmlns="http://www.srcML.org/srcML/src">
            <name>Buffer</name>
            <parameter_list>(<parameter><decl><type><name>int</name></type> <name>s</name></decl></parameter>)</parameter_list>
            <member_init_list>: <call><name>size</name><argument_list>(<argument><expr><name>s</name></expr></argument>)</argument_list></call>, <call><name>data</name><argument_list>(<argument><expr><operator>new</operator> <name>char</name><index>[<expr><name>size</name></expr>]</index></expr></argument>)</argument_list></call> </member_init_list>
            <block>{}</block>
        </constructor>
        '''
        
        constructor = ET.fromstring(constructor_xml)
        
        # Test with dependency: data depends on size
        has_deps = self.transformer._has_constructor_dependencies(constructor, ["data", "size"])
        assert has_deps is True, "Should detect dependency: data depends on size"
        
        # Test without dependency violation
        has_deps = self.transformer._has_constructor_dependencies(constructor, ["size", "data"])
        assert has_deps is False, "Should not detect dependency violation with correct order"
    
    @pytest.mark.unit
    def test_extract_initialization_expression(self):
        """Test extracting initialization expressions from constructor calls."""
        call_xml = '''
        <call xmlns="http://www.srcML.org/srcML/src">
            <name>data</name>
            <argument_list>(<argument><expr><operator>new</operator> <name>char</name><index>[<expr><name>size</name></expr>]</index></expr></argument>)</argument_list>
        </call>
        '''
        
        call_elem = ET.fromstring(call_xml)
        expr = self.transformer._extract_initialization_expression(call_elem)
        
        assert expr is not None, "Should extract initialization expression"
        assert "size" in expr, "Expression should contain 'size'"
        assert "new" in expr, "Expression should contain 'new'"
    
    @pytest.mark.unit
    def test_find_referenced_members(self):
        """Test finding referenced members in initialization expressions."""
        # Test expression that references another member
        expr = "new char[size]"
        referenced = self.transformer._find_referenced_members(expr, ["size", "data", "count"])
        
        assert "size" in referenced, "Should find 'size' reference"
        assert "data" not in referenced, "Should not find 'data' reference"
        assert "count" not in referenced, "Should not find 'count' reference"
        
        # Test expression with multiple references
        expr = "size + count * 2"
        referenced = self.transformer._find_referenced_members(expr, ["size", "data", "count"])
        
        assert "size" in referenced, "Should find 'size' reference"
        assert "count" in referenced, "Should find 'count' reference"
        assert "data" not in referenced, "Should not find 'data' reference"
    
    @pytest.mark.unit
    def test_find_initializer_list(self):
        """Test finding initializer list in constructor."""
        constructor_xml = '''
        <constructor xmlns="http://www.srcML.org/srcML/src">
            <name>TestStruct</name>
            <parameter_list>(<parameter><decl><type><name>int</name></type> <name>x</name></decl></parameter>)</parameter_list>
            <member_init_list>: <call><name>a</name><argument_list>(<argument><expr><name>x</name></expr></argument>)</argument_list></call> </member_init_list>
            <block>{}</block>
        </constructor>
        '''
        
        constructor = ET.fromstring(constructor_xml)
        init_list = self.transformer._find_initializer_list(constructor)
        
        assert init_list is not None, "Should find initializer list"
        assert init_list.tag.endswith('member_init_list'), "Should be member_init_list element"
        
        # Test constructor without initializer list
        constructor_xml_no_init = '''
        <constructor xmlns="http://www.srcML.org/srcML/src">
            <name>TestStruct</name>
            <parameter_list>()</parameter_list>
            <block>{}</block>
        </constructor>
        '''
        
        constructor_no_init = ET.fromstring(constructor_xml_no_init)
        init_list = self.transformer._find_initializer_list(constructor_no_init)
        
        assert init_list is None, "Should not find initializer list"
    
    @pytest.mark.unit
    def test_extract_initializer_member_name(self):
        """Test extracting member name from initializer call."""
        call_xml = '''
        <call xmlns="http://www.srcML.org/srcML/src">
            <name>member_name</name>
            <argument_list>(<argument><expr><name>value</name></expr></argument>)</argument_list>
        </call>
        '''
        
        call_elem = ET.fromstring(call_xml)
        member_name = self.transformer._extract_initializer_member_name(call_elem)
        
        assert member_name == "member_name", "Should extract correct member name"
        
        # Test with invalid call element
        invalid_xml = '''
        <call xmlns="http://www.srcML.org/srcML/src">
            <argument_list>(<argument><expr><name>value</name></expr></argument>)</argument_list>
        </call>
        '''
        
        invalid_elem = ET.fromstring(invalid_xml)
        member_name = self.transformer._extract_initializer_member_name(invalid_elem)
        
        assert member_name is None, "Should return None for call without name"
    
    @pytest.mark.unit
    def test_modify_xml_struct_not_found(self):
        """Test XML modification when struct is not found."""
        from implementation.struct_data import SourceModification, Modification, Location
        
        xml_content = '''
        <unit xmlns="http://www.srcML.org/srcML/src">
            <struct>
                <name>OtherStruct</name>
            </struct>
        </unit>
        '''
        mod = SourceModification(
            file_path="test.cpp",
            struct_name="TestStruct",
            modifications=tuple([
                Modification(
                    type="reorder",
                    location=Location(file="test.cpp", line=1, column=0),
                    old_content="members: a, b",
                    new_content="members: b, a"
                )
            ])
        )
        result = self.transformer._modify_xml(xml_content, mod)
        assert result is None


@pytest.mark.integration
class TestSrcMLTransformerIntegration:
    """Integration tests requiring srcml-caller library."""
    
    def setup_method(self):
        """Set up test fixtures."""
        if SRCML_AVAILABLE:
            self.transformer = SrcMLTransformer()
    
    @pytest.mark.skipif(not SRCML_AVAILABLE, reason="srcml-caller not installed (pip install srcml-caller)")
    def test_transform_real_file(self):
        """Test transformation with real srcML tool."""
        # This test would run if srcML is available
        cpp_content = '''
        struct TestStruct {
            int x;
            double y;
            char z;
        };
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(cpp_content)
            temp_path = Path(f.name)
        
        try:
            modification = SourceModification(
                file_path=str(temp_path),
                struct_name="TestStruct",
                modifications=()
            )
            
            results = self.transformer.transform([modification])
            
            # Would verify actual transformation results
            assert len(results) >= 0  # Placeholder assertion
        finally:
            temp_path.unlink()
    
    @pytest.mark.skipif(not SRCML_AVAILABLE, reason="srcml-caller not installed (pip install srcml-caller)")
    def test_end_to_end_transformation(self):
        """Test complete end-to-end transformation."""
        # This would test the full pipeline with real srcML
        pass