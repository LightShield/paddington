"""Test constructor reordering across access sections."""

import pytest
import xml.etree.ElementTree as ET
from implementation.pipeline.transformation.srcml import SrcMLTransformer


@pytest.mark.unit
def test_constructor_reorder_across_access_sections():
    """Test that constructor initializers are reordered when members span access sections."""
    xml_content = '''
    <unit xmlns="http://www.srcML.org/srcML/src">
        <class>
            <name>TestClass</name>
            <block>{
                <public>public:
                    <decl_stmt><decl><type><name>int</name></type> <name>d</name></decl>;</decl_stmt>
                    <decl_stmt><decl><type><name>int</name></type> <name>c</name></decl>;</decl_stmt>
                </public>
                <private>private:
                    <decl_stmt><decl><type><name>int</name></type> <name>a</name></decl>;</decl_stmt>
                    <decl_stmt><decl><type><name>int</name></type> <name>b</name></decl>;</decl_stmt>
                </private>
                <constructor>
                    <name>TestClass</name>
                    <parameter_list>()</parameter_list>
                    <member_init_list>: <call><name>a</name><argument_list>(<argument><expr><name>0</name></expr></argument>)</argument_list></call>, <call><name>b</name><argument_list>(<argument><expr><name>1</name></expr></argument>)</argument_list></call>, <call><name>c</name><argument_list>(<argument><expr><name>2</name></expr></argument>)</argument_list></call>, <call><name>d</name><argument_list>(<argument><expr><name>3</name></expr></argument>)</argument_list></call> </member_init_list>
                    <block>{}</block>
                </constructor>
            }</block>
        </class>
    </unit>
    '''
    
    root = ET.fromstring(xml_content)
    transformer = SrcMLTransformer()
    
    # New order after optimization: d, c, a, b (declaration order)
    transformer._reorder_constructor_initializers(root, "TestClass", ["d", "c", "a", "b"])
    
    result_xml = ET.tostring(root, encoding='unicode')
    
    # Find initializer list
    init_start = result_xml.find('member_init_list>')
    init_end = result_xml.find('</ns0:member_init_list>')
    if init_end == -1:
        init_end = result_xml.find('</member_init_list>')
    
    init_section = result_xml[init_start:init_end]
    
    # Extract order
    d_pos = init_section.find(':name>d</')
    if d_pos == -1:
        d_pos = init_section.find('<name>d</name>')
    
    c_pos = init_section.find(':name>c</')
    if c_pos == -1:
        c_pos = init_section.find('<name>c</name>')
    
    a_pos = init_section.find(':name>a</')
    if a_pos == -1:
        a_pos = init_section.find('<name>a</name>')
    
    b_pos = init_section.find(':name>b</')
    if b_pos == -1:
        b_pos = init_section.find('<name>b</name>')
    
    assert d_pos != -1 and c_pos != -1 and a_pos != -1 and b_pos != -1, "All members should be in initializer list"
    assert d_pos < c_pos < a_pos < b_pos, f"Order should be d, c, a, b but got positions: d={d_pos}, c={c_pos}, a={a_pos}, b={b_pos}"
