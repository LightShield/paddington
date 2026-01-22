#!/usr/bin/env python3

import tempfile
from pathlib import Path
from implementation.pipeline.transformation.srcml import SrcMLTransformer
from implementation.struct_data.source_change import SourceModification, Modification, Location

def test_debug():
    test_code = """class Test {
protected:
    int small_member;
    
    typedef struct {
        int value;
    } MyType;
    
    std::map<string, MyType> large_member;  // Uses MyType
};
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        test_file = tmpdir / "test.h"
        test_file.write_text(test_code)
        
        print(f"Test file: {test_file}")
        print(f"Test file exists: {test_file.exists()}")
        
        # Reorder to put large_member first (it's larger)
        mod = SourceModification(
            file_path=str(test_file),
            struct_name="Test",
            modifications=(
                Modification(
                    type='reorder',
                    location=Location(file=str(test_file), line=1, column=0),
                    old_content="members: small_member, large_member",
                    new_content="members: large_member, small_member",
                    access_strategy='preserve'
                ),
            ),
            access_strategy='preserve'
        )
        
        transformer = SrcMLTransformer()
        
        # Test XML conversion
        xml_content = transformer._source_to_xml(test_file)
        print(f"XML conversion successful: {xml_content is not None}")
        if xml_content:
            print(f"XML length: {len(xml_content)}")
            print("XML preview:")
            print(xml_content[:500])
        
        transformed = transformer.transform([mod])
        print(f"Transformation result: {len(transformed)} items")

if __name__ == "__main__":
    test_debug()