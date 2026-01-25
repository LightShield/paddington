"""Template type extraction utilities."""

import re
from typing import List, Set


def extract_template_types(struct_name: str) -> List[str]:
    """Extract all custom types from a template instantiation.
    
    Examples:
    - 'Foo<int>' → ['Foo']
    - 'Foo<Bar<int>>' → ['Foo', 'Bar']
    - 'vector<Foo<tuple<Bar, int>>>' → ['Bar']
    
    Args:
        struct_name: Template instantiation name
        
    Returns:
        List of custom type names (excluding built-in types)
    """
    if '<' not in struct_name:
        return []
    
    # Built-in types to exclude
    builtin_types = {
        'int', 'char', 'short', 'long', 'float', 'double', 'bool', 'void',
        'unsigned', 'signed', 'size_t', 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
        'int8_t', 'int16_t', 'int32_t', 'int64_t', 'wchar_t', 'char16_t', 'char32_t'
    }
    
    # Standard library types to exclude
    std_types = {
        'string', 'vector', 'list', 'map', 'set', 'unordered_map', 'unordered_set',
        'pair', 'tuple', 'array', 'deque', 'queue', 'stack', 'priority_queue',
        'shared_ptr', 'unique_ptr', 'weak_ptr', 'function', 'thread', 'mutex',
        'condition_variable', 'atomic', 'future', 'promise', 'optional', 'variant'
    }
    
    # Extract all type names from template parameters
    type_names = set()
    
    # Find all template instantiations
    template_pattern = r'(\w+)<([^<>]*(?:<[^<>]*>)*[^<>]*)>'
    
    def extract_from_match(match):
        base_type = match.group(1)
        params = match.group(2)
        
        # Add base type if it's not built-in or std
        if base_type not in builtin_types and base_type not in std_types:
            type_names.add(base_type)
        
        # Recursively extract from parameters
        extract_types_from_params(params)
    
    def extract_types_from_params(params: str):
        """Extract types from template parameter list."""
        # Handle nested templates
        nested_matches = re.finditer(template_pattern, params)
        for nested_match in nested_matches:
            extract_from_match(nested_match)
        
        # Extract simple type names (not in templates)
        # Split by comma and clean up
        param_parts = []
        depth = 0
        current_part = ""
        
        for char in params:
            if char == '<':
                depth += 1
            elif char == '>':
                depth -= 1
            elif char == ',' and depth == 0:
                param_parts.append(current_part.strip())
                current_part = ""
                continue
            current_part += char
        
        if current_part.strip():
            param_parts.append(current_part.strip())
        
        # Extract type names from each part
        for part in param_parts:
            # Remove template instantiations to get base types
            clean_part = re.sub(r'<[^<>]*(?:<[^<>]*>)*[^<>]*>', '', part)
            
            # Extract identifiers
            identifiers = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', clean_part)
            
            for identifier in identifiers:
                if (identifier not in builtin_types and 
                    identifier not in std_types and
                    not identifier.startswith('std')):
                    type_names.add(identifier)
    
    # Find all template instantiations in the struct name
    matches = re.finditer(template_pattern, struct_name)
    for match in matches:
        extract_from_match(match)
    
    return sorted(list(type_names))


def get_base_template_name(struct_name: str) -> str:
    """Extract base template name from instantiation.
    
    Examples:
    - 'Foo<int>' → 'Foo'
    - 'std::vector<int>' → 'std::vector'
    
    Args:
        struct_name: Template instantiation name
        
    Returns:
        Base template name without parameters
    """
    if '<' not in struct_name:
        return struct_name
    
    return struct_name.split('<')[0]


def is_template_instantiation(struct_name: str) -> bool:
    """Check if struct name is a template instantiation.
    
    Args:
        struct_name: Struct name to check
        
    Returns:
        True if it contains template parameters
    """
    return '<' in struct_name and '>' in struct_name