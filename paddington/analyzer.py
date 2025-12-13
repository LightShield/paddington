from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import clang.cindex as clang

@dataclass
class MemberInfo:
    name: str
    type_name: str
    size: int
    alignment: int
    offset: int

@dataclass
class StructInfo:
    name: str
    file_path: str
    line: int
    members: List[MemberInfo]
    total_size: int
    
    def calculate_padding(self) -> int:
        """Calculate total padding bytes in struct."""
        if not self.members:
            return 0
        
        padding = 0
        for i, member in enumerate(self.members):
            if i == 0:
                # Padding before first member (should be 0)
                padding += member.offset
            else:
                # Padding between this and previous member
                prev = self.members[i-1]
                expected_offset = prev.offset + prev.size
                actual_offset = member.offset
                padding += actual_offset - expected_offset
        
        # Padding at end
        last_member = self.members[-1]
        data_end = last_member.offset + last_member.size
        padding += self.total_size - data_end
        
        return padding
    
    def calculate_optimal_size(self) -> int:
        """Calculate size if members were optimally ordered (largest to smallest)."""
        if not self.members:
            return 0
        
        # Sort by size descending, then by alignment
        sorted_members = sorted(self.members, key=lambda m: (m.size, m.alignment), reverse=True)
        
        offset = 0
        max_align = max(m.alignment for m in sorted_members)
        
        for member in sorted_members:
            # Align offset to member's alignment
            if offset % member.alignment != 0:
                offset += member.alignment - (offset % member.alignment)
            offset += member.size
        
        # Align total size to struct alignment
        if offset % max_align != 0:
            offset += max_align - (offset % max_align)
        
        return offset

def find_cpp_files(path: Path) -> List[Path]:
    """Find all C++ files in path."""
    if path.is_file():
        return [path]
    
    extensions = {'.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx'}
    return [f for f in path.rglob('*') if f.suffix in extensions]

def parse_struct(cursor: clang.Cursor) -> Optional[StructInfo]:
    """Parse a struct/class cursor into StructInfo."""
    if cursor.kind not in [clang.CursorKind.STRUCT_DECL, clang.CursorKind.CLASS_DECL]:
        return None
    
    # Skip forward declarations
    if not cursor.is_definition():
        return None
    
    # Check for paddington-ignore annotation
    if has_ignore_annotation(cursor):
        return None
    
    members = []
    for child in cursor.get_children():
        if child.kind == clang.CursorKind.FIELD_DECL:
            member_type = child.type
            members.append(MemberInfo(
                name=child.spelling,
                type_name=member_type.spelling,
                size=member_type.get_size(),
                alignment=member_type.get_align(),
                offset=cursor.type.get_offset(child.spelling) // 8  # bits to bytes
            ))
    
    if not members:
        return None
    
    return StructInfo(
        name=cursor.spelling,
        file_path=str(cursor.location.file),
        line=cursor.location.line,
        members=members,
        total_size=cursor.type.get_size()
    )

def has_ignore_annotation(cursor: clang.Cursor) -> bool:
    """Check if cursor has paddington-ignore annotation in preceding comment."""
    # Check raw comment
    comment = cursor.raw_comment
    if comment and 'paddington-ignore' in comment:
        return True
    
    # Check tokens before cursor for comment
    file = cursor.location.file
    if not file:
        return False
    
    try:
        with open(file.name, 'r') as f:
            lines = f.readlines()
            if cursor.location.line > 1:
                prev_line = lines[cursor.location.line - 2].strip()
                if 'paddington-ignore' in prev_line:
                    return True
    except:
        pass
    
    return False

def find_structs(translation_unit: clang.TranslationUnit) -> List[StructInfo]:
    """Find all struct definitions in translation unit."""
    structs = []
    
    def visit(cursor):
        struct_info = parse_struct(cursor)
        if struct_info:
            structs.append(struct_info)
        
        for child in cursor.get_children():
            visit(child)
    
    visit(translation_unit.cursor)
    return structs

def analyze_files(path: Path, verbosity: int = 1):
    """Analyze C++ files for struct padding."""
    files = find_cpp_files(path)
    
    if not files:
        print(f"No C++ files found in {path}")
        return
    
    # Initialize libclang
    clang.Config.set_library_file('/Library/Developer/CommandLineTools/usr/lib/libclang.dylib')
    index = clang.Index.create()
    
    all_structs = []
    
    for file in files:
        try:
            # Add file's directory to include path for header resolution
            include_dir = f"-I{file.parent}"
            tu = index.parse(str(file), args=['-std=c++17', include_dir])
            
            # Check for parse errors
            if tu.diagnostics:
                errors = [d for d in tu.diagnostics if d.severity >= clang.Diagnostic.Error]
                if errors:
                    continue
            
            structs = find_structs(tu)
            all_structs.extend(structs)
        except Exception as e:
            if verbosity >= 3:
                print(f"Error parsing {file}: {e}")
    
    # Report findings
    total_padding = 0
    total_savings = 0
    optimizable_count = 0
    
    for struct in all_structs:
        padding = struct.calculate_padding()
        optimal_size = struct.calculate_optimal_size()
        savings = struct.total_size - optimal_size
        
        total_padding += padding
        
        if savings > 0:
            optimizable_count += 1
            total_savings += savings
            
            if verbosity >= 1:
                print(f"[PADDING] struct {struct.name}: {struct.total_size} bytes "
                      f"({padding} bytes padding, {savings} bytes savable)")
            
            if verbosity >= 2:
                print(f"  Location: {struct.file_path}:{struct.line}")
                print(f"  Optimal size: {optimal_size} bytes")
                print(f"  Members: {', '.join(m.name for m in struct.members)}")
        elif verbosity >= 3:
            print(f"[OK] struct {struct.name}: {struct.total_size} bytes (already optimal)")
    
    print(f"\nTotal: {len(all_structs)} structs analyzed, {optimizable_count} can be optimized")
    print(f"Total padding: {total_padding} bytes")
    print(f"Potential savings: {total_savings} bytes")
