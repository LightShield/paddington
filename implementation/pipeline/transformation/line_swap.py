"""Line-based struct member reordering transformer."""

import re
from typing import List, Dict
from pathlib import Path
from .base import ISourceTransformer
from ...struct_data import SourceModification, TransformedSource


class LineSwapTransformer(ISourceTransformer):
    """Simple line-swapping transformer for struct member reordering."""
    
    def transform(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        """Transform source files by swapping member declaration lines."""
        results = []
        
        for mod in modifications:
            try:
                with open(mod.file_path, 'r') as f:
                    lines = f.readlines()
                
                original_content = ''.join(lines)
                new_lines = self._swap_lines(lines, mod)
                new_content = ''.join(new_lines)
                
                results.append(TransformedSource(
                    file_path=mod.file_path,
                    original_content=original_content,
                    new_content=new_content,
                    modifications=(mod,)
                ))
            except Exception:
                # Skip files that can't be processed
                continue
                
        return results
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if file is a C++ source/header file."""
        ext = Path(file_path).suffix.lower()
        return ext in {'.cpp', '.h', '.hpp', '.cc', '.cxx'}
    
    def _swap_lines(self, lines: List[str], mod: SourceModification) -> List[str]:
        """Swap member declaration lines according to modifications."""
        # Find struct boundaries
        struct_start, struct_end = self._find_struct_bounds(lines, mod.struct_name)
        if struct_start == -1 or struct_end == -1:
            return lines
        
        # Find member lines
        member_lines = self._find_member_lines(lines, struct_start, struct_end)
        if not member_lines:
            return lines
        
        # Extract new order from modifications
        new_order = self._extract_new_order(mod)
        if not new_order or len(new_order) != len(member_lines):
            return lines
        
        # Swap lines
        return self._apply_swaps(lines, member_lines, new_order)
    
    def _find_struct_bounds(self, lines: List[str], struct_name: str) -> tuple:
        """Find opening and closing braces of struct."""
        # Find struct declaration
        struct_line = -1
        for i, line in enumerate(lines):
            if re.search(rf'\b(struct|class)\s+{re.escape(struct_name)}\b', line):
                struct_line = i
                break
        
        if struct_line == -1:
            return -1, -1
        
        # Find opening brace
        brace_line = struct_line
        while brace_line < len(lines) and '{' not in lines[brace_line]:
            brace_line += 1
        
        if brace_line >= len(lines):
            return -1, -1
        
        # Find closing brace
        depth = 0
        for i in range(brace_line, len(lines)):
            depth += lines[i].count('{')
            depth -= lines[i].count('}')
            if depth == 0:
                return brace_line, i
        
        return -1, -1
    
    def _find_member_lines(self, lines: List[str], start: int, end: int) -> Dict[str, int]:
        """Find member declaration lines within struct bounds."""
        member_lines = {}
        depth = 0
        
        for i in range(start + 1, end):
            line = lines[i].strip()
            
            # Track depth
            depth += lines[i].count('{')
            depth -= lines[i].count('}')
            
            # Only process class body level
            if depth != 0:
                continue
            
            # Skip empty lines, comments, access specifiers
            if not line or line.startswith('//') or line in ['public:', 'private:', 'protected:']:
                continue
            
            # Must have semicolon
            if ';' not in line:
                continue
            
            # Skip method declarations (have parentheses before semicolon)
            semicolon_pos = line.find(';')
            if '(' in line[:semicolon_pos]:
                continue
            
            # Extract member name (last identifier before semicolon)
            before_semi = line[:semicolon_pos].strip()
            tokens = before_semi.split()
            if tokens:
                member_name = tokens[-1].rstrip('[]')  # Handle arrays
                member_lines[member_name] = i
        
        return member_lines
    
    def _extract_new_order(self, mod: SourceModification) -> List[str]:
        """Extract new member order from modifications."""
        # Simple approach: extract from modification content
        new_order = []
        for modification in mod.modifications:
            if modification.type == 'reorder':
                # Parse new content for member names
                content = modification.new_content
                for line in content.split('\n'):
                    line = line.strip()
                    if ';' in line and '(' not in line[:line.find(';')]:
                        tokens = line[:line.find(';')].split()
                        if tokens:
                            member_name = tokens[-1].rstrip('[]')
                            if member_name not in new_order:
                                new_order.append(member_name)
        return new_order
    
    def _apply_swaps(self, lines: List[str], member_lines: Dict[str, int], new_order: List[str]) -> List[str]:
        """Apply line swaps according to new order."""
        if len(new_order) != len(member_lines):
            return lines
        
        # Get sorted line indices
        sorted_indices = sorted(member_lines.values())
        
        # Create mapping: new_position -> old_line_content
        new_lines = lines[:]
        for new_pos, member_name in enumerate(new_order):
            if member_name in member_lines:
                old_line_idx = member_lines[member_name]
                new_line_idx = sorted_indices[new_pos]
                new_lines[new_line_idx] = lines[old_line_idx]
        
        return new_lines