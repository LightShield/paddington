"""JSON-based type resolver using debug info from object files."""

import json
from pathlib import Path
from typing import Dict, Optional
from .models import MemberInfo, StructInfo


class JsonTypeResolver:
    """Resolves struct types from JSON debug info extracted from object files."""
    
    def __init__(self, json_path: str):
        """Initialize with path to struct_layouts.json file."""
        self.struct_data = {}
        self.json_path = Path(json_path)
        self._load_struct_data()
    
    def _load_struct_data(self):
        """Load struct layout data from JSON file."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Struct layouts file not found: {self.json_path}")
        
        with open(self.json_path, 'r') as f:
            self.struct_data = json.load(f)
    
    def get_struct_info(self, struct_name: str) -> Optional[StructInfo]:
        """Get struct information by name."""
        if struct_name not in self.struct_data:
            return None
        
        data = self.struct_data[struct_name]
        
        # Convert JSON data to MemberInfo objects
        members = []
        for i, member in enumerate(data.get('members', [])):
            # Calculate actual member size from layout
            if 'size' in member:
                # Use provided size if available
                member_size = member['size']
            else:
                # Calculate from offsets and struct size
                if i < len(data['members']) - 1:
                    # Size is difference to next member
                    next_offset = data['members'][i + 1]['offset']
                    member_size = next_offset - member['offset']
                else:
                    # Last member: size is struct_size - offset
                    member_size = data['size'] - member['offset']
            
            members.append(MemberInfo(
                name=member['name'],
                type_name="unknown",  # Not available in debug info
                size=member_size,
                alignment=1,  # Assume 1-byte alignment for simplicity
                offset=member['offset']
            ))
        
        return StructInfo(
            name=struct_name,
            file_path="unknown",  # Not available in debug info
            line=0,  # Not available in debug info
            members=members,
            total_size=data['size'],
            is_class=False,  # Assume struct for simplicity
            is_template=False
        )
    
    def get_type_size(self, type_name: str) -> int:
        """Get size of a type by name."""
        struct_info = self.get_struct_info(type_name)
        if struct_info:
            return struct_info.total_size
        
        # Fallback to common type sizes
        common_sizes = {
            'char': 1, 'signed char': 1, 'unsigned char': 1,
            'short': 2, 'unsigned short': 2,
            'int': 4, 'unsigned int': 4,
            'long': 8, 'unsigned long': 8,
            'long long': 8, 'unsigned long long': 8,
            'float': 4, 'double': 8, 'long double': 16,
            'bool': 1, 'void*': 8, 'size_t': 8
        }
        return common_sizes.get(type_name, 0)
    
    def has_struct(self, struct_name: str) -> bool:
        """Check if struct exists in the database."""
        return struct_name in self.struct_data
    
    def get_all_struct_names(self) -> list:
        """Get list of all available struct names."""
        return list(self.struct_data.keys())
