#!/usr/bin/env python3
import subprocess
import re
import json
import sys
from pathlib import Path

def extract_struct_info(object_file):
    """Extract struct information from DWARF debug info"""
    try:
        # Try newer objdump first, fallback to system objdump
        objdump_paths = [
            '/tools/apps/x86_64/amazon/2/binutils/2.35.2/bin/objdump',
            'objdump'
        ]
        
        result = None
        for objdump_path in objdump_paths:
            try:
                result = subprocess.run([objdump_path, '-Wi', object_file], 
                                      capture_output=True, text=True, check=True)
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if result is None:
            return {}
    except subprocess.CalledProcessError:
        return {}
    
    structs = {}
    current_struct = None
    
    for line in result.stdout.split('\n'):
        # Start of struct
        if 'DW_TAG_structure_type' in line:
            current_struct = {'members': []}
            
        # Struct name
        elif current_struct is not None and 'DW_AT_name' in line and 'name' not in current_struct:
            match = re.search(r': (?:\([^)]+\): )?(.+)$', line.strip())
            if match:
                current_struct['name'] = match.group(1)
                
        # Struct size
        elif current_struct is not None and 'DW_AT_byte_size' in line:
            match = re.search(r': (\d+)', line)
            if match:
                current_struct['size'] = int(match.group(1))
                
        # Member info
        elif current_struct is not None and 'DW_TAG_member' in line:
            current_struct['_parsing_member'] = True
            
        elif current_struct is not None and current_struct.get('_parsing_member'):
            if 'DW_AT_name' in line:
                match = re.search(r': (?:\([^)]+\): )?(.+)$', line.strip())
                if match:
                    current_struct['_member_name'] = match.group(1)
            elif 'DW_AT_data_member_location' in line:
                match = re.search(r': (\d+)', line)
                if match and '_member_name' in current_struct:
                    offset = int(match.group(1))
                    current_struct['members'].append({
                        'name': current_struct['_member_name'],
                        'offset': offset
                    })
                    del current_struct['_member_name']
                    current_struct['_parsing_member'] = False
                    
        # End of struct
        elif current_struct is not None and 'DW_TAG_' in line and 'DW_TAG_member' not in line:
            if 'name' in current_struct and 'size' in current_struct:
                structs[current_struct['name']] = {
                    'size': current_struct['size'],
                    'members': current_struct['members']
                }
            current_struct = None
            
    return structs

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_struct_info.py <object_files...>")
        sys.exit(1)
        
    all_structs = {}
    
    for obj_file in sys.argv[1:]:
        if not Path(obj_file).exists():
            print(f"Warning: {obj_file} not found")
            continue
            
        structs = extract_struct_info(obj_file)
        all_structs.update(structs)
        
    print(json.dumps(all_structs, indent=2))

if __name__ == '__main__':
    main()
