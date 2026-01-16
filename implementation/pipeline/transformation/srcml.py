"""SrcML-based source code transformer."""

import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

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
        modified_xml = self._modify_xml(xml_content, modification.struct_name)
        if not modified_xml:
            return original_content  # Return original if no changes
            
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
        """Convert source file to srcML XML."""
        try:
            result = subprocess.run(
                ['srcml', str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def _xml_to_source(self, xml_content: str) -> Optional[str]:
        """Convert srcML XML back to source code."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(xml_content)
                xml_file = f.name
            
            result = subprocess.run(
                ['srcml', xml_file],
                capture_output=True,
                text=True,
                check=True
            )
            
            Path(xml_file).unlink()  # Clean up temp file
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def _modify_xml(self, xml_content: str, struct_name: str) -> Optional[str]:
        """Modify XML to reorder struct members."""
        try:
            root = ET.fromstring(xml_content)
            
            # Find struct node by name
            struct_node = self._find_struct_node(root, struct_name)
            if struct_node is None:
                return None
                
            # Reorder member declarations
            self._reorder_members(struct_node)
            
            return ET.tostring(root, encoding='unicode')
        except ET.ParseError:
            return None
    
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
    
    def _reorder_members(self, struct_node: ET.Element) -> None:
        """Reorder member declarations within struct."""
        # Find all member declarations
        members = []
        for elem in struct_node:
            if elem.tag.endswith('decl_stmt') or elem.tag.endswith('function_decl'):
                members.append(elem)
        
        if len(members) <= 1:
            return
            
        # Simple reordering strategy: group by access modifiers
        public_members = []
        private_members = []
        protected_members = []
        other_members = []
        
        for member in members:
            access_type = self._get_access_modifier(member)
            if access_type == 'public':
                public_members.append(member)
            elif access_type == 'private':
                private_members.append(member)
            elif access_type == 'protected':
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