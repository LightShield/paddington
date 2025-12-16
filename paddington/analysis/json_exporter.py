"""JSON export utilities for struct reference trees."""

import json
from typing import List, Dict, Any
from ..core import StructInfo


def struct_to_dict(struct: StructInfo) -> Dict[str, Any]:
    """Convert StructInfo to dictionary for JSON serialization.
    
    Args:
        struct: Struct information to convert
        
    Returns:
        Dictionary with struct name, size, and member details
    """
    return {
        "name": struct.name,
        "size": struct.total_size,
        "members": [
            {
                "name": member.name,
                "type": member.type_name,
                "size": member.size,
            }
            for member in struct.members
        ],
    }


def export_reference_tree(structs: List[StructInfo], output_path: str) -> None:
    """Export structs as JSON reference tree.
    
    Args:
        structs: List of analyzed structs
        output_path: Path to write JSON file
    """
    reference_tree = [struct_to_dict(s) for s in structs]
    
    with open(output_path, "w") as f:
        json.dump(reference_tree, f, indent=2)
