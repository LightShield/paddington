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
from ...utils.logger import log


class SrcMLTransformer(ISourceTransformer):
    """Transform C++ source code using srcML."""
    
    SUPPORTED_EXTENSIONS = {'.cpp', '.h', '.hpp', '.cc', '.cxx'}
    
    def __init__(self):
        pass
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this transformer can handle the file type."""
        return Path(file_path).suffix in self.SUPPORTED_EXTENSIONS
    
    def transform(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        """Transform source code based on modifications."""
        log.info(f"Transforming {len(modifications)} files")
        
        # Use parallel processing for large sets
        if len(modifications) > 10:
            from multiprocessing import Pool, cpu_count
            
            num_workers = max(1, int(cpu_count() * 0.8))
            log.debug(f"Using {num_workers} workers for transformation")
            
            with Pool(num_workers) as pool:
                results = pool.map(self._transform_file_wrapper, modifications)
            
            # Filter out None results
            return [r for r in results if r is not None]
        else:
            # Serial processing for small sets
            results = []
            for i, mod in enumerate(modifications, 1):
                if i % 10 == 0:
                    log.info(f"  Transforming: {i}/{len(modifications)}")
                
                try:
                    log.debug(f"Transforming {mod.file_path}")
                    transformed = self._transform_file(mod)
                    if transformed:
                        results.append(transformed)
                    else:
                        log.debug(f"Transformation returned None for {mod.file_path}")
                except Exception as e:
                    log.warning(f"Failed to transform {mod.file_path}: {e}")
                    import traceback
                    log.debug(f"Traceback: {traceback.format_exc()}")
            
            return results
    
    def _transform_file_wrapper(self, modification: SourceModification):
        """Wrapper for parallel processing (catches exceptions)."""
        try:
            import os
            pid = os.getpid()
            log.debug(f"[PID {pid}] Transforming {modification.file_path}")
            result = self._transform_file(modification)
            if result:
                log.debug(f"[PID {pid}] Success: {modification.file_path}")
            return result
        except Exception as e:
            import os
            pid = os.getpid()
            log.debug(f"[PID {pid}] Failed: {modification.file_path}: {e}")
            return None
                
        return results
    
    def _transform_file(self, modification: SourceModification) -> Optional[TransformedSource]:
        """Transform a single file."""
        import os
        pid = os.getpid()
        
        file_path = Path(modification.file_path)
        
        if not file_path.exists():
            log.debug(f"[PID {pid}] File does not exist: {file_path}")
            return None
            
        original_content = file_path.read_text()
        
        # Convert source to XML
        xml_content = self._source_to_xml(file_path)
        if not xml_content:
            log.debug(f"[PID {pid}] Failed to convert source to XML: {file_path}")
            return None
            
        # Parse and modify XML
        modified_xml = self._modify_xml(xml_content, modification)
        if not modified_xml:
            log.debug(f"[PID {pid}] XML modification returned None for: {file_path}")
            return None  # Return None if no changes
            
        # Convert XML back to source
        new_content = self._xml_to_source(modified_xml)
        if not new_content:
            log.debug(f"[PID {pid}] Failed to convert XML back to source: {file_path}")
            return None
        
        # Skip if content didn't actually change
        if original_content == new_content:
            log.debug(f"Content unchanged for: {file_path}")
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
                log.debug("No new order found in modification")
                return None
            
            import os
            pid = os.getpid()
            log.debug(f"[PID {pid}] New order: {new_order}")
            
            # Check if we need to reorder members (has 'reorder' modification)
            has_member_reorder = any(m.type == 'reorder' for m in modification.modifications)
            
            # For files with struct definitions, find and reorder struct members
            if has_member_reorder:
                # Find struct node by name
                struct_node = self._find_struct_node(root, modification.struct_name)
                if struct_node is None:
                    log.debug(f"[PID {pid}] Struct node not found: {modification.struct_name}")
                    return None
                
                log.debug(f"[PID {pid}] Found struct node: {modification.struct_name}")
                
                # Reorder member declarations
                original_xml = ET.tostring(root, encoding='unicode')
                self._reorder_members(struct_node, new_order)
            else:
                original_xml = ET.tostring(root, encoding='unicode')
            
            # Handle constructors - skip if has dependencies, otherwise reorder
            struct_node = self._find_struct_node(root, modification.struct_name)
            
            if struct_node:
                # Check for inline constructors
                found_constructor = False
                has_constructor_with_deps = False
                for elem in struct_node.iter():
                    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if tag == 'constructor':
                        found_constructor = True
                        init_list = self._find_initializer_list(elem)
                        if init_list and self._has_constructor_dependencies(elem, new_order):
                            log.info(f"SKIPPING {modification.struct_name} - constructor has dependencies")
                            has_constructor_with_deps = True
                            break
                
                if has_constructor_with_deps:
                    return None
                
                # Fallback: only if srcML didn't find constructor but file might have one
                if not found_constructor:
                    if self._has_inline_constructor_fallback(modification.file_path, modification.struct_name):
                        log.info(f"SKIPPING {modification.struct_name} - has inline constructor (fallback, can't analyze)")
                        return None
                
                # Reorder inline constructors if present
                if found_constructor:
                    self._reorder_constructor_initializers(root, modification.struct_name, new_order)
            
            # Check for out-of-line constructors
            constructors = self._find_constructors(root, modification.struct_name)
            if constructors:
                # Check dependencies
                for constructor in constructors:
                    if self._has_constructor_dependencies(constructor, new_order):
                        log.info(f"SKIPPING {modification.struct_name} - out-of-line constructor has dependencies")
                        return None
                # Reorder out-of-line constructors
                self._reorder_constructor_initializers(root, modification.struct_name, new_order)
            
            # Check if any changes were made
            modified_xml = ET.tostring(root, encoding='unicode')
            if original_xml == modified_xml:
                # No changes were made (possibly due to missing members or other issues)
                log.debug("No changes were made to XML")
                return None
            
            return modified_xml
        except (ET.ParseError, Exception) as e:
            log.debug(f"XML modification failed: {e}")
            return None
    
    def _extract_new_order(self, mod: SourceModification) -> list:
        """Extract new member order from modifications."""
        for m in mod.modifications:
            if m.type in ['reorder', 'reorder_constructors']:
                content = m.new_content
                if content.startswith("members: "):
                    return [n.strip() for n in content[9:].split(',')]
        return []
    
    def _find_struct_node(self, root: ET.Element, struct_name: str) -> Optional[ET.Element]:
        """Find struct node by name in XML tree (namespace-aware).
        
        For template instantiations like 'Foo<int>', look for template definition 'template<...> struct Foo'.
        For namespace-qualified names like 'NS::Foo', look for 'Foo' in namespace 'NS'.
        """
        # Extract base name if namespace-qualified
        base_name = struct_name.split('::')[-1] if '::' in struct_name else struct_name
        
        # First try to find template definition
        template_struct = self._find_template_struct_node(root, base_name)
        if template_struct:
            return template_struct
        
        # Fallback to regular struct search
        for elem in root.iter():
            # Check if it's a struct/class element
            if elem.tag.endswith('}struct') or elem.tag.endswith('}class') or elem.tag == 'struct' or elem.tag == 'class':
                # Look for name child element
                for child in elem:
                    if (child.tag.endswith('}name') or child.tag == 'name'):
                        # Match base name (without namespace)
                        if child.text == base_name or child.text == struct_name:
                            return elem
        return None
    
    def _find_template_struct_node(self, root: ET.Element, struct_name: str) -> Optional[ET.Element]:
        """Find template struct definition for the given struct name.
        
        Looks for patterns like:
        template<typename T> struct Foo { ... }
        """
        # Look for template elements
        for elem in root.iter():
            if elem.tag.endswith('}template') or elem.tag == 'template':
                # Find the struct/class declaration within this template
                struct_elem = self._find_struct_in_template(elem, struct_name)
                if struct_elem:
                    return struct_elem
        
        return None
    
    def _find_struct_in_template(self, template_elem: ET.Element, struct_name: str) -> Optional[ET.Element]:
        """Find struct declaration within a template element."""
        for child in template_elem:
            # Look for struct or class elements
            if child.tag.endswith('}struct') or child.tag.endswith('}class') or child.tag == 'struct' or child.tag == 'class':
                # Check if this struct has the right name
                for grandchild in child:
                    if (grandchild.tag.endswith('}name') or grandchild.tag == 'name') and grandchild.text == struct_name:
                        return child
        
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
        member_containers = {}
        static_members_found = 0
        
        for container in containers:
            for elem in list(container):
                if 'decl_stmt' in elem.tag:
                    # Check if this is a static member
                    elem_str = ET.tostring(elem, encoding='unicode')
                    is_static = 'static' in elem_str
                    
                    if is_static:
                        static_members_found += 1
                        log.debug(f"Found static member, keeping in place")
                    
                    # Extract member name
                    member_name = self._extract_member_name(elem)
                    
                    if member_name and member_name in new_order and not is_static:
                        # This is a non-static data member we need to reorder
                        member_decls[member_name] = elem
                        member_containers[member_name] = container
                    # Static members are left in place (not added to member_decls)
        
        log.debug(f"Found {static_members_found} static members to preserve")
        
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
        
        # Remove only the non-static member declarations we're reordering
        removed_count = 0
        for container in containers:
            for elem in list(container):
                if 'decl_stmt' in elem.tag:
                    member_name = self._extract_member_name(elem)
                    is_in_decls = member_name in member_decls
                    elem_str = ET.tostring(elem, encoding='unicode')
                    is_static_now = 'static' in elem_str
                    
                    log.debug(f"Checking {member_name}: in_member_decls={is_in_decls}, is_static={is_static_now}")
                    
                    if member_name in member_decls:
                        container.remove(elem)
                        removed_count += 1
                        log.debug(f"Removing {member_name} for reordering")
                    else:
                        log.debug(f"Keeping {member_name} in place")
        
        log.debug(f"Removed {removed_count} members for reordering")
        
        # Group by container to maintain access modifier boundaries
        members_by_container = {}
        for member_name in new_order_filtered:
            if member_name in member_containers:
                container = member_containers[member_name]
                if container not in members_by_container:
                    members_by_container[container] = []
                members_by_container[container].append(member_name)
        
        # Handle nested type definitions and static members
        # Strategy: Move nested types and static members to top, then insert data members after
        nested_types_by_container = {}
        static_members_by_container = {}
        
        for container in members_by_container.keys():
            nested_types = []
            static_members = []
            
            for elem in list(container):
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                
                # Check for nested types (including using statements)
                if tag in ['typedef', 'using', 'struct', 'enum', 'class', 'union']:
                    nested_types.append(elem)
                    container.remove(elem)
                # Check for static members
                elif 'decl_stmt' in elem.tag:
                    elem_str = ET.tostring(elem, encoding='unicode')
                    if 'static' in elem_str or 'extern' in elem_str:
                        # This is a static/extern member - move to top
                        static_members.append(elem)
                        container.remove(elem)
            if nested_types:
                nested_types_by_container[container] = nested_types
            if static_members:
                static_members_by_container[container] = static_members
        
        # Re-insert nested types and static members at the top of each container
        for container in members_by_container.keys():
            offset = 0
            # Insert nested types first
            if container in nested_types_by_container:
                for i, type_elem in enumerate(nested_types_by_container[container]):
                    container.insert(i, type_elem)
                offset += len(nested_types_by_container[container])
            # Insert static members after nested types
            if container in static_members_by_container:
                for i, static_elem in enumerate(static_members_by_container[container]):
                    container.insert(offset + i, static_elem)
                offset += len(static_members_by_container[container])
        
        # Re-insert data members in new order, after nested types and static members
        for container, member_names in members_by_container.items():
            # Calculate offset: nested types + static members
            offset = len(nested_types_by_container.get(container, []))
            offset += len(static_members_by_container.get(container, []))
            
            for i, member_name in enumerate(member_names):
                if member_name in member_decls:
                    container.insert(offset + i, member_decls[member_name])
    
    def _has_nested_type_dependencies(self, containers: list, new_order: list) -> bool:
        """Check if there are nested type definitions that could cause forward reference errors."""
        # Find all nested type definitions (typedef, struct, enum, class)
        type_definitions = {}  # type_name -> element
        member_declarations = {}  # member_name -> (member_type, element)
        
        for container in containers:
            for elem in list(container):
                # Check for nested type definitions
                if (elem.tag.endswith('}typedef') or elem.tag == 'typedef'):
                    type_name = self._extract_typedef_name(elem)
                    if type_name:
                        type_definitions[type_name] = elem
                elif (elem.tag.endswith('}struct') or elem.tag == 'struct' or
                      elem.tag.endswith('}enum') or elem.tag == 'enum' or
                      elem.tag.endswith('}class') or elem.tag == 'class'):
                    # Only consider nested types (not the main class/struct)
                    type_name = self._extract_type_name(elem)
                    if type_name and self._is_nested_type(elem):
                        type_definitions[type_name] = elem
                
                # Check for member declarations
                elif 'decl_stmt' in elem.tag:
                    member_name = self._extract_member_name(elem)
                    if member_name and member_name in new_order:
                        member_type = self._extract_member_type(elem)
                        member_declarations[member_name] = (member_type, elem)
        
        # If no type definitions, no forward reference issues
        if not type_definitions:
            return False
        
        # Check if any member uses a nested type that would be moved before it
        for member_name, (member_type, member_elem) in member_declarations.items():
            for type_name, type_elem in type_definitions.items():
                # Check if member uses this type
                if type_name in member_type:
                    # Check if reordering would move member before type definition
                    if self._would_create_forward_reference_detailed(member_name, type_name, new_order, containers):
                        return True
        
        return False
    
    def _extract_typedef_name(self, elem: ET.Element) -> Optional[str]:
        """Extract typedef name from typedef element."""
        # For typedef, the name is usually the last name element
        names = []
        for child in elem.iter():
            if (child.tag.endswith('}name') or child.tag == 'name') and child.text:
                names.append(child.text.strip())
        
        # Return the last name (the typedef name)
        return names[-1] if names else None
    
    def _is_nested_type(self, elem: ET.Element) -> bool:
        """Check if this is a nested type definition (not the main class)."""
        # Simple heuristic: if it has a name and is not at the top level
        return self._extract_type_name(elem) is not None
    
    def _would_create_forward_reference_detailed(self, member_name: str, type_name: str, 
                                               new_order: list, containers: list) -> bool:
        """Check if reordering would create a forward reference error."""
        # Find current positions of member and type
        member_pos = -1
        type_pos = -1
        
        pos = 0
        for container in containers:
            for elem in list(container):
                if 'decl_stmt' in elem.tag:
                    elem_member_name = self._extract_member_name(elem)
                    if elem_member_name == member_name:
                        member_pos = pos
                elif (elem.tag.endswith('}typedef') or elem.tag == 'typedef'):
                    elem_type_name = self._extract_typedef_name(elem)
                    if elem_type_name == type_name:
                        type_pos = pos
                elif (elem.tag.endswith('}struct') or elem.tag == 'struct' or
                      elem.tag.endswith('}enum') or elem.tag == 'enum' or
                      elem.tag.endswith('}class') or elem.tag == 'class'):
                    elem_type_name = self._extract_type_name(elem)
                    if elem_type_name == type_name:
                        type_pos = pos
                pos += 1
        
        # If we couldn't find positions, be conservative
        if member_pos == -1 or type_pos == -1:
            return True
        
        # Check new positions after reordering
        member_new_index = new_order.index(member_name) if member_name in new_order else -1
        
        # If member would be moved to an earlier position and type is currently after it,
        # this could create a forward reference
        if member_new_index != -1 and type_pos > member_pos:
            # Member is being moved up in the order - potential forward reference
            return True
        
        return False
    
    def _extract_type_name(self, elem: ET.Element) -> Optional[str]:
        """Extract type name from typedef, struct, enum, or class definition."""
        # Look for name element in the type definition
        for child in elem:
            if (child.tag.endswith('}name') or child.tag == 'name') and child.text:
                return child.text.strip()
        return None
    
    def _extract_member_type(self, decl_stmt: ET.Element) -> str:
        """Extract the type information from a member declaration."""
        # Get all text content from the declaration to check for type usage
        type_text = ""
        for elem in decl_stmt.iter():
            if elem.text:
                type_text += elem.text + " "
        return type_text.strip()
    
    def _would_create_forward_reference(self, member_elem: ET.Element, type_elem: ET.Element, 
                                      member_name: str, new_order: list) -> bool:
        """Check if reordering would create a forward reference error."""
        # Simple heuristic: if member is being moved to first half of new order,
        # and there are type definitions, it's potentially risky
        member_index = new_order.index(member_name) if member_name in new_order else -1
        if member_index != -1 and member_index < len(new_order) // 2:
            # Member is being moved to first half - potential forward reference
            return True
        
        return False

    def _extract_member_name(self, decl_stmt: ET.Element) -> Optional[str]:
        """Extract member name from declaration statement."""
        # Navigate through decl_stmt -> decl -> name
        # The variable name is typically the last <name>, but we need to exclude:
        # - Names inside <index> tags (array sizes like [NUM])
        # - Type names
        
        # Find the <decl> element
        decl = None
        for elem in decl_stmt:
            if 'decl' in elem.tag:
                decl = elem
                break
        
        if decl is None:
            return None
        
        # Find the <name> element that's a direct child of <decl> (not inside <index>)
        # This is the variable name
        for elem in decl:
            if 'name' in elem.tag and elem.text:
                # This is the variable name (comes after type)
                # Skip if it's a type name
                type_names = {'char', 'int', 'double', 'float', 'long', 'short', 'bool', 'void',
                             'unsigned', 'signed', 'const', 'volatile', 'static'}
                if elem.text not in type_names:
                    return elem.text
        
        return None

    def _reorder_constructor_initializers(self, root: ET.Element, struct_name: str, new_order: list) -> None:
        """Reorder constructor initializer lists to match new member order.
        
        Args:
            root: XML root element
            struct_name: Name of the struct/class
            new_order: List of member names in the new optimized order (may be subset of all members)
        """
        # Try to extract full member declaration order from struct
        struct_node = self._find_struct_node(root, struct_name)
        
        if struct_node:
            # Struct definition is in this file - extract full member order
            full_member_order = self._extract_member_declaration_order(struct_node)
            if full_member_order:
                # Build complete order: apply new_order to members that were optimized,
                # keep others in their original positions
                complete_order = self._merge_member_orders(full_member_order, new_order)
                log.debug(f"Struct {struct_name}: full_order has {len(full_member_order)} members, "
                         f"new_order has {len(new_order)} members, "
                         f"complete_order has {len(complete_order)} members")
            else:
                # Fallback to new_order if extraction fails
                complete_order = new_order
                log.debug(f"Struct {struct_name}: Could not extract full member order, using new_order")
        else:
            # Struct definition is in another file (.cpp with out-of-line constructor)
            # Use new_order directly - it should contain the complete optimized order
            complete_order = new_order
            log.debug(f"Struct {struct_name}: No struct node found, using new_order")
        
        # Find all constructor definitions for this struct/class
        constructors = self._find_constructors(root, struct_name)
        
        for constructor in constructors:
            # Check for constructor dependencies first
            if self._has_constructor_dependencies(constructor, complete_order):
                log.debug(f"Skipping constructor reordering for {struct_name} due to member dependencies")
                continue
                
            # Find member initializer list
            init_list = self._find_initializer_list(constructor)
            if init_list:
                self._reorder_initializer_list(init_list, complete_order)
    
    def _extract_member_declaration_order(self, struct_node: ET.Element) -> list:
        """Extract all member variable names in declaration order from struct.
        
        Traverses all access sections (public, private, protected) and collects
        member variable declarations in the order they appear.
        """
        members = []
        
        # Find the block element (struct body)
        block = None
        for child in struct_node:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag == 'block':
                block = child
                break
        
        if not block:
            log.debug("No block element found in struct")
            return members
        
        # Iterate through block content in order
        for elem in block:
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            # Look for member declarations (decl_stmt elements)
            if tag == 'decl_stmt':
                # Extract member name from declaration
                member_name = self._extract_member_name_from_decl(elem)
                if member_name:
                    members.append(member_name)
            # Also check inside access specifier blocks (public:, private:, protected:)
            elif tag in ['public', 'private', 'protected']:
                # These contain decl_stmt elements
                for child in elem:
                    child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if child_tag == 'decl_stmt':
                        member_name = self._extract_member_name_from_decl(child)
                        if member_name:
                            members.append(member_name)
        
        return members
    
    def _extract_member_name_from_decl(self, decl_stmt: ET.Element) -> Optional[str]:
        """Extract member variable name from a declaration statement."""
        # Find <decl> element
        for child in decl_stmt:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag == 'decl':
                # Find <name> element that's the variable name (not type name)
                for elem in child:
                    elem_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if elem_tag == 'name' and elem.text:
                        # Skip type names
                        type_names = {'char', 'int', 'double', 'float', 'long', 'short', 
                                     'bool', 'void', 'unsigned', 'signed', 'const', 
                                     'volatile', 'static', 'uint', 'uint64', 'uint32',
                                     'uint16', 'uint8', 'int64', 'int32', 'int16', 'int8'}
                        if elem.text not in type_names:
                            return elem.text
        return None
    
    def _merge_member_orders(self, full_order: list, optimized_subset: list) -> list:
        """Merge full member order with optimized subset.
        
        Args:
            full_order: All members in original declaration order
            optimized_subset: Subset of members in new optimized order
        
        Returns:
            Complete member order with optimized members in new positions,
            non-optimized members in original positions
        """
        # Create result list
        result = []
        
        # Track which members from full_order have been placed
        placed = set()
        
        # Find position of first optimized member in full_order
        first_opt_idx = None
        for i, member in enumerate(full_order):
            if member in optimized_subset:
                first_opt_idx = i
                break
        
        if first_opt_idx is None:
            # No optimized members found, return full order
            return full_order
        
        # Add members before first optimized member
        result.extend(full_order[:first_opt_idx])
        placed.update(full_order[:first_opt_idx])
        
        # Add optimized members in new order
        result.extend(optimized_subset)
        placed.update(optimized_subset)
        
        # Add remaining members after optimized section
        for member in full_order[first_opt_idx:]:
            if member not in placed:
                result.append(member)
                placed.add(member)
        
        return result

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
                        log.debug(f"Dependency violation: {member_name} depends on {ref_member}")
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

    def _has_inline_constructor_fallback(self, file_path: str, struct_name: str) -> bool:
        """Fallback detection for inline constructors using grep.
        
        srcML sometimes fails to parse constructors in complex files.
        This provides a simple regex-based fallback.
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for constructor pattern: struct_name() with optional parameters
            import re
            # Match: struct_name(...) followed by : or {
            pattern = r'\b' + re.escape(struct_name) + r'\s*\([^)]*\)\s*[:{\n]'
            if re.search(pattern, content):
                return True
            
            return False
        except Exception as e:
            log.debug(f"Fallback constructor detection failed for {file_path}: {e}")
            return False
    
    def _find_constructors(self, root: ET.Element, struct_name: str) -> list:
        """Find all constructor definitions for the given struct/class.
        
        For template structs, looks for both template and non-template constructors.
        """
        constructors = []
        
        # Look for constructor definitions (both inline and out-of-line)
        for elem in root.iter():
            if self._is_constructor(elem, struct_name):
                constructors.append(elem)
        
        # Also look for template constructors
        template_constructors = self._find_template_constructors(root, struct_name)
        constructors.extend(template_constructors)
        
        return constructors
    
    def _find_template_constructors(self, root: ET.Element, struct_name: str) -> list:
        """Find template constructor definitions."""
        constructors = []
        
        # Look for template elements containing constructors
        for elem in root.iter():
            if elem.tag.endswith('}template') or elem.tag == 'template':
                # Look for constructors within this template
                for child in elem.iter():
                    if self._is_constructor(child, struct_name):
                        constructors.append(child)
        
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
            if child_tag == 'name':
                # Handle both simple names and qualified names (ClassName::ClassName)
                name_parts = []
                if child.text and child.text.strip():
                    # Simple name directly in text or qualified name as plain text
                    name_text = child.text.strip()
                    if '::' in name_text:
                        # Handle qualified name like "TestClass::TestClass"
                        parts = name_text.split('::')
                        name_parts.extend(parts)
                    else:
                        # Simple name
                        name_parts.append(name_text)
                else:
                    # Qualified name - extract from children
                    for grandchild in child:
                        gc_tag = grandchild.tag.split('}')[-1] if '}' in grandchild.tag else grandchild.tag
                        if gc_tag == 'name' and grandchild.text:
                            name_parts.append(grandchild.text.strip())
                
                # Check if any part matches struct_name (for ClassName::ClassName, both parts should match)
                if struct_name in name_parts:
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
        """Reorder initializers in the member initializer list.
        
        Args:
            init_list: The member initializer list XML element
            new_order: Complete member declaration order (all members, not just optimized ones)
        """
        # Extract current initializers and preserve original order
        initializers = {}
        original_order = []
        
        for child in list(init_list):
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'call':
                member_name = self._extract_initializer_member_name(child)
                if member_name:
                    initializers[member_name] = child
                    original_order.append(member_name)
        
        if not initializers:
            return
        
        # Build final order: use new_order for members that are in it,
        # keep others in original positions
        new_order_set = set(new_order)
        final_order = []
        
        # Add members in new_order that exist in initializers
        for member in new_order:
            if member in initializers:
                final_order.append(member)
        
        # Add remaining members (not in new_order) in their original order
        for member in original_order:
            if member not in new_order_set:
                final_order.append(member)
        
        # Clear and rebuild
        init_list.clear()
        init_list.text = ": "
        init_list.tail = None
        
        # Add all initializers in final order
        for i, member_name in enumerate(final_order):
            if i > 0:
                list(init_list)[-1].tail = ", "
            init_list.append(initializers[member_name])
        
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
