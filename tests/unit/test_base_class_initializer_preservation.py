"""Test that base class initializers are preserved during reordering."""

import pytest
import xml.etree.ElementTree as ET
from implementation.pipeline.transformation.srcml import SrcMLTransformer


@pytest.mark.unit
def test_base_class_initializer_preserved():
    """Test that base class initializers are preserved when reordering members."""
    xml_content = '''
    <unit xmlns="http://www.srcML.org/srcML/src">
        <class>
            <name>Derived</name>
            <block>{
                <public>public:
                    <decl_stmt><decl><type><name>int</name></type> <name>b</name></decl>;</decl_stmt>
                    <decl_stmt><decl><type><name>int</name></type> <name>a</name></decl>;</decl_stmt>
                </public>
                <protected>protected:
                    <decl_stmt><decl><type><name>int</name></type> <name>c</name></decl>;</decl_stmt>
                </protected>
                <constructor>
                    <name>Derived</name>
                    <parameter_list>()</parameter_list>
                    <member_init_list>: <call><name>Base</name><argument_list>()</argument_list></call>, <call><name>c</name><argument_list>(<argument><expr><name>0</name></expr></argument>)</argument_list></call> </member_init_list>
                    <block>{}</block>
                </constructor>
            }</block>
        </class>
    </unit>
    '''
    
    root = ET.fromstring(xml_content)
    transformer = SrcMLTransformer()
    
    # Reorder only a and b (c is not in new_order)
    transformer._reorder_constructor_initializers(root, "Derived", ["b", "a", "c"])
    
    result_xml = ET.tostring(root, encoding='unicode')
    
    # Find initializer list
    init_start = result_xml.find('member_init_list>')
    init_end = result_xml.find('</ns0:member_init_list>')
    if init_end == -1:
        init_end = result_xml.find('</member_init_list>')
    
    init_section = result_xml[init_start:init_end]
    
    # Base class should come first
    base_pos = init_section.find(':name>Base</')
    if base_pos == -1:
        base_pos = init_section.find('<name>Base</name>')
    
    c_pos = init_section.find(':name>c</')
    if c_pos == -1:
        c_pos = init_section.find('<name>c</name>')
    
    assert base_pos != -1, f"Base class initializer should be preserved: {init_section[:200]}"
    assert c_pos != -1, "Member c should be in initializer list"
    assert base_pos < c_pos, "Base class should come before members"
