"""SrcML-based source code transformer."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

try:
    import srcml_caller
    SRCML_AVAILABLE = True
except ImportError:
    SRCML_AVAILABLE = False

from .base import ISourceTransformer
from ...struct_data import SourceModification, TransformedSource


class SrcMLTransformer(ISourceTransformer):
    """Transform C++ source code using srcML."""
    
    SUPPORTED_EXTENSIONS = {'.cpp', '.h', '.hpp', '.cc', '.cxx'}
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this transformer can handle the file type."""
        return Path(file_path).suffix in self.SUPPORTED_EXTENSIONS
    
    def transform(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        """Transform source code based on modifications."""
        results = []
        
        for mod in modifications:
            try:
                transformed = self._transform_file(mod)
                if transformed:
                    results.append(transformed)
            except Exception as e:
                # Log error but continue processing other files
                print(f"Error transforming {mod.file_path}: {e}")
                
        return results
    
    def _transform_file(self, modification: SourceModification) -> Optional[TransformedSource]:
        """Transform a single file."""
        file_path = Path(modification.file_path)
        
        if not file_path.exists():
            return None
            
        original_content = file_path.read_text()
        
        # Convert source to XML
        xml_content = self._source_to_xml(file_path)
        if not xml_content:
            return None
            
        # Parse and modify XML
        modified_xml = self._modify_xml(xml_content, modification)
        if not modified_xml:
            return None  # Return None if no changes
            
        # Convert XML back to source
        new_content = self._xml_to_source(modified_xml)
        if not new_content:
            return None
            
        return TransformedSource(
            file_path=str(file_path),
            original_content=original_content,
            new_content=new_content,
            modifications=(modification,)
        )
    
    def _source_to_xml(self, file_path: Path) -> Optional[str]:
        """Convert source file to srcML XML using srcml-caller library."""
        if not SRCML_AVAILABLE:
            return None
        
        try:
            # Read source file
            with open(file_path, 'r') as f:
                source_content = f.read()
            
            # Convert to XML using srcml-caller
            xml_str = srcml_caller.cpp_to_srcml(source_content, include_positions=True)
            return xml_str
        except Exception:
            return None
    
    def _xml_to_source(self, xml_content: str) -> Optional[str]:
        """Convert srcML XML back to source code using srcml-caller library."""
        if not SRCML_AVAILABLE:
            return None
        
        try:
            source = srcml_caller.to_code(xml_content)
            return source
        except Exception:
            return None
    
    def _modify_xml(self, xml_content: str, modification: SourceModification) -> Optional[str]:
        """Modify XML to reorder struct members."""
        try:
            root = ET.fromstring(xml_content)
            
            # Extract new member order from modification
            new_order = self._extract_new_order(modification)
            if not new_order:
                return None
            
            # Find struct node by name
            struct_node = self._find_struct_node(root, modification.struct_name)
            if struct_node is None:
                return None
                
            # Reorder member declarations
            self._reorder_members(struct_node, new_order)
            
            return ET.tostring(root, encoding='unicode')
        except ET.ParseError:
            return None
    
    def _extract_new_order(self, mod: SourceModification) -> list:
        """Extract new member order from modifications."""
        for m in mod.modifications:
            if m.type == 'reorder':
                content = m.new_content
                if content.startswith("members: "):
                    return [n.strip() for n in content[9:].split(',')]
        return []
    
    def _find_struct_node(self, root: ET.Element, struct_name: str) -> Optional[ET.Element]:
        """Find struct node by name in XML tree."""
        # Handle namespaced XML from srcML
        for elem in root.iter():
            if elem.tag.endswith('struct'):
                # Look for name element - handle both namespaced and non-namespaced
                for child in elem:
                    if child.tag.endswith('name') and child.text == struct_name:
                        return elem
        return None
    
    def _reorder_members(self, struct_node: ET.Element, new_order: list) -> None:
        """Reorder member declarations within struct according to new_order."""
        # Find block element (struct body)
        block = None
        for child in struct_node:
            if child.tag.endswith('block'):
                block = child
                break
        
        if block is None:
            return
        
        # Find all member declaration statements
        member_decls = {}
        for elem in list(block):
            if elem.tag.endswith('decl_stmt'):
                # Extract member name
                for decl in elem.iter():
                    if decl.tag.endswith('name') and decl.text:
                        member_name = decl.text
                        if member_name in new_order:
                            member_decls[member_name] = elem
                            break
        
        if not member_decls or len(member_decls) != len(new_order):
            return
        
        # Remove all member declarations from block
        for elem in list(block):
            if elem.tag.endswith('decl_stmt'):
                block.remove(elem)
        
        # Re-add in new order
        # Find where to insert (after access specifiers, before methods)
        insert_index = 0
        for i, elem in enumerate(block):
            if elem.tag.endswith('public') or elem.tag.endswith('private') or elem.tag.endswith('protected'):
                insert_index = i + 1
                break
        
        # Insert members in new order
        for i, member_name in enumerate(new_order):
            if member_name in member_decls:
                block.insert(insert_index + i, member_decls[member_name])
                protected_members.append(member)
            else:
                other_members.append(member)
        
        # Remove original members
        for member in members:
            struct_node.remove(member)
        
        # Add back in order: public, protected, private, others
        for member_list in [public_members, protected_members, private_members, other_members]:
            for member in member_list:
                struct_node.append(member)
    
    def _get_access_modifier(self, member_node: ET.Element) -> str:
        """Get access modifier for a member (simplified)."""
        # This is a simplified implementation
        # In practice, you'd need more sophisticated parsing
        return 'other'