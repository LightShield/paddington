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
from ...utils import Logger


class SrcMLTransformer(ISourceTransformer):
    """Transform C++ source code using srcML."""
    
    SUPPORTED_EXTENSIONS = {'.cpp', '.h', '.hpp', '.cc', '.cxx'}
    
    def __init__(self):
        self.log = Logger()
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this transformer can handle the file type."""
        return Path(file_path).suffix in self.SUPPORTED_EXTENSIONS
    
    def transform(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        """Transform source code based on modifications."""
        self.log.info(f"Transforming {len(modifications)} files")
        results = []
        
        for i, mod in enumerate(modifications, 1):
            if i % 10 == 0:
                self.log.info(f"  Transforming: {i}/{len(modifications)}")
            
            try:
                self.log.debug(f"Transforming {mod.file_path}")
                transformed = self._transform_file(mod)
                if transformed:
                    results.append(transformed)
                else:
                    self.log.debug(f"Transformation returned None for {mod.file_path}")
            except Exception as e:
                # Log error but continue processing other files
                self.log.warning(f"Failed to transform {mod.file_path}: {e}")
                import traceback
                self.log.debug(f"Traceback: {traceback.format_exc()}")
                
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
            
        result = TransformedSource(
            file_path=str(file_path),
            original_content=original_content,
            new_content=new_content,
            modifications=(modification,)
        )
        return result
    
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
        except Exception as e:
            return None
    
    def _modify_xml(self, xml_content: str, modification: SourceModification) -> Optional[str]:
        """Modify XML to reorder struct members."""
        try:
            # Fix srcML XML namespace issue - add all required namespace declarations
            if 'xmlns:' not in xml_content or 'xmlns:cpp=' not in xml_content:
                # Add all srcML namespaces to unit tag
                namespaces = (
                    'xmlns="http://www.srcML.org/srcML/src" '
                    'xmlns:cpp="http://www.srcML.org/srcML/cpp" '
                    'xmlns:pos="http://www.srcML.org/srcML/position" '
                )
                xml_content = xml_content.replace('<unit', f'<unit {namespaces}', 1)
            
            # Register srcML namespaces
            ET.register_namespace('', 'http://www.srcML.org/srcML/src')
            ET.register_namespace('pos', 'http://www.srcML.org/srcML/position')
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Extract new member order from modification
            new_order = self._extract_new_order(modification)
            if not new_order:
                return None
            
            # Find struct node by name
            struct_node = self._find_struct_node(root, modification.struct_name)
            if struct_node is None:
                return None
            
            # Check for constructor dependencies before making any changes
            constructors = self._find_constructors(root, modification.struct_name)
            has_dependencies = False
            
            for constructor in constructors:
                if self._has_constructor_dependencies(constructor, new_order):
                    has_dependencies = True
                    break
            
            if has_dependencies:
                self.log.debug(f"Skipping optimization of {modification.struct_name} due to constructor dependencies")
                return None
                
            # Reorder member declarations
            original_xml = ET.tostring(root, encoding='unicode')
            self._reorder_members(struct_node, new_order)
            
            # Reorder constructor initializer lists
            self._reorder_constructor_initializers(root, modification.struct_name, new_order)
            
            # Check if any changes were made
            modified_xml = ET.tostring(root, encoding='unicode')
            if original_xml == modified_xml:
                # No changes were made (possibly due to missing members or other issues)
                return None
            
            return modified_xml
        except (ET.ParseError, Exception) as e:
            self.log.debug(f"XML modification failed: {e}")
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
        """Find struct node by name in XML tree (namespace-aware)."""
        # srcML uses namespaces, so we need to check tag endings
        for elem in root.iter():
            # Check if it's a struct/class element
            if elem.tag.endswith('}struct') or elem.tag.endswith('}class') or elem.tag == 'struct' or elem.tag == 'class':
                # Look for name child element
                for child in elem:
                    if (child.tag.endswith('}name') or child.tag == 'name') and child.text == struct_name:
                        return elem
        return None
    
    def _reorder_members(self, struct_node: ET.Element, new_order: list) -> None:
        """Reorder member declarations within struct according to new_order."""
        # Find block element (struct body)
        block = None
        for child in struct_node:
            if 'block' in child.tag:
                block = child
                break
        
        if block is None:
            return
        
        # Find ALL access modifier containers (may have multiple protected/private sections)
        # srcML structure: block -> public/private/protected -> decl_stmt
        containers = []
        for child in block:
            if 'public' in child.tag or 'private' in child.tag or 'protected' in child.tag:
                containers.append(child)
        
        # If no access modifiers, use block directly
        if not containers:
            containers = [block]
        
        # Find all member declaration statements across ALL containers and map by name
        member_decls = {}
        member_containers = {}  # Track which container each member is in
        
        for container in containers:
            for elem in list(container):
                if 'decl_stmt' in elem.tag:
                    # Extract member name from this declaration
                    member_name = self._extract_member_name(elem)
                    # Only include members that are in the new_order (from DWARF)
                    if member_name and member_name in new_order:
                        member_decls[member_name] = elem
                        member_containers[member_name] = container
        
        # Check if we found all the members we need to reorder
        if not member_decls:
            return
        
        # Allow partial match if we found at least 80% of members
        # (some members may be in #ifdef blocks that srcML doesn't parse as decl_stmt)
        match_ratio = len(member_decls) / len(new_order)
        if match_ratio < 0.8:
            # Too many missing members - unsafe to reorder
            return
        
        # Filter new_order to only include members we actually found
        new_order_filtered = [name for name in new_order if name in member_decls]
        
        # Remove all member declarations from their containers
        for container in containers:
            for elem in list(container):
                if 'decl_stmt' in elem.tag:
                    member_name = self._extract_member_name(elem)
                    if member_name in member_decls:
                        container.remove(elem)
        
        # Re-insert in new order, keeping each member in its original container
        # Group by container to maintain access modifier boundaries
        members_by_container = {}
        for member_name in new_order_filtered:
            if member_name in member_containers:
                container = member_containers[member_name]
                if container not in members_by_container:
                    members_by_container[container] = []
                members_by_container[container].append(member_name)
        
        # Insert members back into their original containers in new order
        for container, member_names in members_by_container.items():
            for i, member_name in enumerate(member_names):
                if member_name in member_decls:
                    container.insert(i, member_decls[member_name])
    
    def _extract_member_name(self, decl_stmt: ET.Element) -> Optional[str]:
        """Extract member name from declaration statement."""
        # Navigate through decl_stmt -> decl -> name
        # Get the LAST name element (variable name, not type name)
        names = []
        for elem in decl_stmt.iter():
            if 'name' in elem.tag and elem.text:
                names.append(elem.text)
        
        # Return last name (variable name), skip type names
        if names:
            # Filter out common type names
            type_names = {'char', 'int', 'double', 'float', 'long', 'short', 'bool', 'void'}
            for name in reversed(names):
                if name not in type_names:
                    return name
        
        return None

    def _reorder_constructor_initializers(self, root: ET.Element, struct_name: str, new_order: list) -> None:
        """Reorder constructor initializer lists to match new member order."""
        # Find all constructor definitions for this struct/class
        constructors = self._find_constructors(root, struct_name)
        
        for constructor in constructors:
            # Check for constructor dependencies first
            if self._has_constructor_dependencies(constructor, new_order):
                self.log.debug(f"Skipping constructor reordering for {struct_name} due to member dependencies")
                continue
                
            # Find member initializer list
            init_list = self._find_initializer_list(constructor)
            if init_list:
                self._reorder_initializer_list(init_list, new_order)

    def _has_constructor_dependencies(self, constructor: ET.Element, new_order: list) -> bool:
        """Check if constructor has member dependencies that would be violated by reordering."""
        init_list = self._find_initializer_list(constructor)
        if not init_list:
            return False
        
        # Extract member initializations and their expressions
        member_inits = {}
        
        for child in init_list:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'call':
                member_name = self._extract_initializer_member_name(child)
                if member_name and member_name in new_order:
                    # Extract the initialization expression
                    init_expr = self._extract_initialization_expression(child)
                    member_inits[member_name] = init_expr
        
        # Check for dependencies: if member A's initialization references member B,
        # then B must be initialized before A
        for member_name, init_expr in member_inits.items():
            if init_expr:
                # Check if this initialization references other members
                referenced_members = self._find_referenced_members(init_expr, new_order)
                for ref_member in referenced_members:
                    # Check if reordering would violate dependency
                    member_index = new_order.index(member_name) if member_name in new_order else -1
                    ref_index = new_order.index(ref_member) if ref_member in new_order else -1
                    
                    if member_index != -1 and ref_index != -1 and member_index < ref_index:
                        # Dependency violation: member_name depends on ref_member
                        # but would be initialized before it in new order
                        self.log.debug(f"Dependency violation: {member_name} depends on {ref_member}")
                        return True
        
        return False
    
    def _extract_initialization_expression(self, call_elem: ET.Element) -> Optional[str]:
        """Extract the initialization expression from a constructor call."""
        # Look for argument_list element
        for child in call_elem:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'argument_list':
                # Convert the argument list to string to analyze
                return ET.tostring(child, encoding='unicode', method='text').strip()
        
        return None
    
    def _find_referenced_members(self, init_expr: str, member_names: list) -> list:
        """Find which members are referenced in an initialization expression."""
        referenced = []
        
        if not init_expr:
            return referenced
        
        # Simple heuristic: look for member names in the expression
        # This is a basic implementation - could be enhanced with proper parsing
        for member_name in member_names:
            # Look for the member name as a whole word
            import re
            pattern = r'\b' + re.escape(member_name) + r'\b'
            if re.search(pattern, init_expr):
                referenced.append(member_name)
        
        return referenced

    def _find_constructors(self, root: ET.Element, struct_name: str) -> list:
        """Find all constructor definitions for the given struct/class."""
        constructors = []
        
        # Look for constructor definitions (both inline and out-of-line)
        for elem in root.iter():
            if self._is_constructor(elem, struct_name):
                constructors.append(elem)
        
        return constructors

    def _is_constructor(self, elem: ET.Element, struct_name: str) -> bool:
        """Check if element is a constructor for the given struct/class."""
        # Check for constructor element (handle namespaced tags)
        tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag_name != 'constructor':
            return False
        
        # Look for constructor name matching struct name
        for child in elem:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'name' and child.text and child.text.strip() == struct_name:
                return True
        
        # Also check for qualified constructor names (e.g., "ClassName::ClassName")
        for child in elem:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'name' and child.text:
                # Handle qualified names like "TestClass::TestClass"
                name_parts = child.text.strip().split('::')
                if len(name_parts) >= 2 and name_parts[-1] == struct_name:
                    return True
                # Handle simple names
                elif child.text.strip() == struct_name:
                    return True
        
        return False

    def _find_initializer_list(self, constructor: ET.Element) -> Optional[ET.Element]:
        """Find the member initializer list in a constructor."""
        # Look for member_init_list element (handle namespaced tags)
        for child in constructor:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'member_init_list':
                return child
        
        return None

    def _reorder_initializer_list(self, init_list: ET.Element, new_order: list) -> None:
        """Reorder initializers in the member initializer list."""
        # Extract current initializers (call elements)
        initializers = {}
        non_member_elements = []
        
        # Collect all child elements
        children = list(init_list)
        
        for child in children:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'call':
                member_name = self._extract_initializer_member_name(child)
                if member_name and member_name in new_order:
                    initializers[member_name] = child
                else:
                    # Keep non-member initializers (like base class calls)
                    non_member_elements.append(child)
            else:
                # Keep text nodes, punctuation, etc.
                non_member_elements.append(child)
        
        if not initializers:
            return
        
        # Clear the initializer list
        init_list.clear()
        init_list.text = ": "
        init_list.tail = None
        
        # Add non-member elements first (base class initializers)
        base_class_calls = []
        other_elements = []
        
        for elem in non_member_elements:
            elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if elem_tag == 'call':
                # This is likely a base class call
                base_class_calls.append(elem)
            else:
                other_elements.append(elem)
        
        # Add base class calls first
        for base_call in base_class_calls:
            init_list.append(base_call)
            base_call.tail = ", "
        
        # Add member initializers in new order
        member_count = 0
        for member_name in new_order:
            if member_name in initializers:
                if member_count > 0 or len(base_class_calls) > 0:
                    # Add comma separator
                    if len(list(init_list)) > 0:
                        list(init_list)[-1].tail = ", "
                
                init_list.append(initializers[member_name])
                member_count += 1
        
        # Set final tail
        if len(list(init_list)) > 0:
            list(init_list)[-1].tail = " "

    def _is_member_initializer_call(self, elem: ET.Element) -> bool:
        """Check if element is a member initializer call."""
        tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        return tag_name == 'call'

    def _extract_initializer_member_name(self, call_elem: ET.Element) -> Optional[str]:
        """Extract member name from initializer call element."""
        # Look for the name child element in the call
        for child in call_elem:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'name' and child.text:
                name = child.text.strip()
                # Handle qualified names (e.g., "Base::member" -> "member")
                if '::' in name:
                    return name.split('::')[-1]
                return name
        
        return None
