"""Test constructor reordering matches member declaration order."""

import pytest
import xml.etree.ElementTree as ET
from implementation.pipeline.transformation.srcml import SrcMLTransformer


@pytest.mark.unit
def test_constructor_order_matches_declaration_after_reorder():
    """Test that after reordering members, constructor matches new declaration order."""
    # Simulate: members a,b,c reordered to c,b,a
    # Constructor should change from a,b,c to c,b,a
    xml_content = '''
    <unit xmlns="http://www.srcML.org/srcML/src">
        <class>
            <name>Test</name>
            <block>{
                <decl_stmt><decl><type><name>int</name></type> <name>a</name></decl>;</decl_stmt>
                <decl_stmt><decl><type><name>int</name></type> <name>b</name></decl>;</decl_stmt>
                <decl_stmt><decl><type><name>int</name></type> <name>c</name></decl>;</decl_stmt>
                <constructor>
                    <name>Test</name>
                    <parameter_list>()</parameter_list>
                    <member_init_list>: <call><name>a</name><argument_list>(<argument><expr><name>0</name></expr></argument>)</argument_list></call>, <call><name>b</name><argument_list>(<argument><expr><name>1</name></expr></argument>)</argument_list></call>, <call><name>c</name><argument_list>(<argument><expr><name>2</name></expr></argument>)</argument_list></call> </member_init_list>
                    <block>{}</block>
                </constructor>
            }</block>
        </class>
    </unit>
    '''
    
    root = ET.fromstring(xml_content)
    transformer = SrcMLTransformer()
    
    # Step 1: Reorder members to c, b, a
    struct_node = transformer._find_struct_node(root, "Test")
    transformer._reorder_members(struct_node, ["c", "b", "a"])
    
    # Step 2: Reorder constructor to match
    transformer._reorder_constructor_initializers(root, "Test", ["c", "b", "a"])
    
    result_xml = ET.tostring(root, encoding='unicode')
    
    # Find initializer list
    init_start = result_xml.find('member_init_list>')
    init_end = result_xml.find('</member_init_list>')
    if init_end == -1:
        init_end = result_xml.find('</ns0:member_init_list>')
    
    init_section = result_xml[init_start:init_end]
    
    # Extract positions
    c_pos = init_section.find('name>c<')
    b_pos = init_section.find('name>b<')
    a_pos = init_section.find('name>a<')
    
    assert c_pos != -1 and b_pos != -1 and a_pos != -1, "All members should be in initializer list"
    assert c_pos < b_pos < a_pos, f"Order should be c, b, a but got positions: c={c_pos}, b={b_pos}, a={a_pos}. Init section: {init_section[:200]}"
