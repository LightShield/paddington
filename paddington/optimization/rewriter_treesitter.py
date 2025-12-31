"""Tree-sitter based struct rewriter - syntax-aware without compilation."""

from tree_sitter import Language, Parser
import tree_sitter_cpp as tscpp
from typing import List, Dict
from ..core import StructInfo, MemberInfo
from ..utils import Logger


def rewrite_struct_treesitter(file_path: str, struct: StructInfo, new_order: List[MemberInfo]) -> str:
    """Rewrite struct using tree-sitter for syntax-aware parsing."""
    log = Logger()
    
    # Read file
    with open(file_path, 'rb') as f:
        source_code = f.read()
    
    # Parse with tree-sitter
    parser = Parser(Language(tscpp.language()))
    tree = parser.parse(source_code)
    
    # Find the struct/class node
    struct_node = find_struct_node(tree.root_node, struct.name, source_code)
    if not struct_node:
        log.warning(f"Could not find {struct.name} in tree-sitter AST")
        return source_code.decode('utf-8')
    
    # Extract field declarations with access specifiers
    members_info = extract_members_with_access(struct_node, struct.members, source_code)
    
    if len(members_info) != len(struct.members):
        missing = [m.name for m in struct.members if m.name not in members_info]
        log.warning(f"Tree-sitter found {len(members_info)}/{len(struct.members)} members (missing: {', '.join(missing[:3])})")
        return source_code.decode('utf-8')
    
    # Reorder members preserving access specifiers
    new_content = reorder_members_treesitter(source_code, struct_node, members_info, new_order)
    
    return new_content.decode('utf-8')


def find_struct_node(node, struct_name, source_code):
    """Find struct/class declaration node by name."""
    if node.type in ['struct_specifier', 'class_specifier']:
        # Check if this is the right struct
        for child in node.children:
            if child.type == 'type_identifier':
                name = source_code[child.start_byte:child.end_byte].decode('utf-8')
                if name == struct_name:
                    return node
    
    for child in node.children:
        result = find_struct_node(child, struct_name, source_code)
        if result:
            return result
    
    return None


def extract_members_with_access(struct_node, members, source_code):
    """Extract field declarations with their access specifiers."""
    members_info = {}  # member_name -> (node, access_spec, source_text)
    current_access = 'public' if struct_node.type == 'struct_specifier' else 'private'
    
    # Find the field_declaration_list (body of struct)
    body_node = None
    for child in struct_node.children:
        if child.type == 'field_declaration_list':
            body_node = child
            break
    
    if not body_node:
        return members_info
    
    # Scan through body
    for child in body_node.children:
        if child.type == 'access_specifier':
            # Extract access type (public/protected/private)
            access_text = source_code[child.start_byte:child.end_byte].decode('utf-8')
            current_access = access_text.rstrip(':').strip()
        elif child.type == 'field_declaration':
            # Extract field name
            field_name = extract_field_name(child, source_code)
            if field_name and field_name in [m.name for m in members]:
                source_text = source_code[child.start_byte:child.end_byte]
                members_info[field_name] = (child, current_access, source_text)
    
    return members_info


def extract_field_name(field_node, source_code):
    """Extract field name from field_declaration node."""
    for child in field_node.children:
        if child.type == 'field_identifier':
            return source_code[child.start_byte:child.end_byte].decode('utf-8')
        # Handle declarators
        if child.type in ['pointer_declarator', 'array_declarator', 'reference_declarator']:
            for subchild in child.children:
                if subchild.type == 'field_identifier':
                    return source_code[subchild.start_byte:subchild.end_byte].decode('utf-8')
    return None


def reorder_members_treesitter(source_code, struct_node, members_info, new_order):
    """Reorder members preserving access specifiers."""
    # Find body node
    body_node = None
    for child in struct_node.children:
        if child.type == 'field_declaration_list':
            body_node = child
            break
    
    if not body_node:
        return source_code
    
    # Build new body content
    new_body_parts = []
    current_access = None
    
    for member in new_order:
        if member.name in members_info:
            node, access_spec, source_text = members_info[member.name]
            
            # Add access specifier if changed
            if access_spec != current_access:
                new_body_parts.append(f"  {access_spec}:\n".encode('utf-8'))
                current_access = access_spec
            
            # Add member declaration
            new_body_parts.append(b"    ")
            new_body_parts.append(source_text)
            if not source_text.endswith(b'\n'):
                new_body_parts.append(b'\n')
    
    # Reconstruct file
    # Replace body content
    before_body = source_code[:body_node.start_byte + 1]  # Include opening {
    after_body = source_code[body_node.end_byte - 1:]     # Include closing }
    
    new_body = b''.join(new_body_parts)
    
    return before_body + b'\n' + new_body + after_body
