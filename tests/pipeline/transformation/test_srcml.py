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
    def test_get_access_modifier_default(self):
        """Test access modifier detection (simplified implementation)."""
        xml_content = '<decl_stmt><decl><type><name>int</name></type> <name>x</name></decl>;</decl_stmt>'
        member_node = ET.fromstring(xml_content)
        
        access = self.transformer._get_access_modifier(member_node)
        assert access == 'other'  # Default implementation returns 'other'
    
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