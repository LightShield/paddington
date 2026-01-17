"""Line-based struct member reordering transformer."""

import re
from typing import List, Dict, Optional
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
        
        # Find member lines and access specifiers
        member_lines = self._find_member_lines(lines, struct_start, struct_end)
        access_specifiers = self._find_access_specifiers(lines, struct_start, struct_end)
        
        if not member_lines:
            return lines
        
        # Extract new order from modifications
        new_order = self._extract_new_order(mod)
        if not new_order or len(new_order) != len(member_lines):
            return lines
        
        # Determine access modifier strategy from modification
        access_strategy = self._get_access_strategy(mod)
        
        # Apply swaps with access modifier handling
        return self._apply_swaps_with_access_modifiers(
            lines, member_lines, access_specifiers, new_order, access_strategy, struct_start, struct_end
        )
    
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
    
    def _find_access_specifiers(self, lines: List[str], start: int, end: int) -> Dict[int, str]:
        """Find access specifier lines within struct bounds."""
        access_specifiers = {}
        depth = 0
        
        for i in range(start + 1, end):
            line = lines[i].strip()
            
            # Track depth
            depth += lines[i].count('{')
            depth -= lines[i].count('}')
            
            # Only process class body level
            if depth != 0:
                continue
            
            # Check for access specifiers
            if line in ['public:', 'private:', 'protected:']:
                access_specifiers[i] = line.rstrip(':')
        
        return access_specifiers
    
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
    
    def _get_access_strategy(self, mod: SourceModification) -> str:
        """Extract access modifier strategy from modification."""
        # Use access strategy from SourceModification
        if mod.access_strategy:
            return mod.access_strategy
        
        # Look for strategy hint in modification metadata
        for modification in mod.modifications:
            if modification.access_strategy:
                return modification.access_strategy
        
        # Default to preserve if not specified
        return "preserve"
    
    def _apply_swaps_with_access_modifiers(self, lines: List[str], member_lines: Dict[str, int], 
                                         access_specifiers: Dict[int, str], new_order: List[str], 
                                         access_strategy: str, struct_start: int, struct_end: int) -> List[str]:
        """Apply line swaps with access modifier handling."""
        if len(new_order) != len(member_lines):
            return lines
        
        new_lines = lines[:]
        
        if access_strategy == "preserve":
            # Preserve existing access modifier sections
            return self._apply_preserve_strategy(new_lines, member_lines, new_order)
        elif access_strategy == "split":
            # Add per-member access modifiers
            return self._apply_split_strategy(new_lines, member_lines, access_specifiers, 
                                            new_order, struct_start, struct_end)
        elif access_strategy == "ignore":
            # Reorder across sections, remove access specifiers
            return self._apply_ignore_strategy(new_lines, member_lines, access_specifiers, 
                                             new_order, struct_start, struct_end)
        else:
            # Default to preserve
            return self._apply_preserve_strategy(new_lines, member_lines, new_order)
    
    def _apply_preserve_strategy(self, lines: List[str], member_lines: Dict[str, int], 
                               new_order: List[str]) -> List[str]:
        """Apply preserve strategy - reorder within access modifier sections."""
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
    
    def _apply_split_strategy(self, lines: List[str], member_lines: Dict[str, int], 
                            access_specifiers: Dict[int, str], new_order: List[str], 
                            struct_start: int, struct_end: int) -> List[str]:
        """Apply split strategy - add per-member access modifiers."""
        # For split strategy, we need to add access modifiers before each member
        # This is a simplified implementation that adds the access modifier inline
        new_lines = lines[:]
        
        # Get member access modifiers from original positions
        member_access = self._get_member_access_modifiers(lines, member_lines, access_specifiers, struct_start)
        
        # Apply basic reordering first
        sorted_indices = sorted(member_lines.values())
        for new_pos, member_name in enumerate(new_order):
            if member_name in member_lines:
                old_line_idx = member_lines[member_name]
                new_line_idx = sorted_indices[new_pos]
                
                # Get the original line and add access modifier comment
                original_line = lines[old_line_idx]
                access_mod = member_access.get(member_name, "public")
                
                # Add access modifier as a comment for now (full implementation would restructure)
                if not original_line.strip().startswith('//'):
                    modified_line = f"    // {access_mod}:\n{original_line}"
                    new_lines[new_line_idx] = modified_line
                else:
                    new_lines[new_line_idx] = original_line
        
        return new_lines
    
    def _apply_ignore_strategy(self, lines: List[str], member_lines: Dict[str, int], 
                             access_specifiers: Dict[int, str], new_order: List[str], 
                             struct_start: int, struct_end: int) -> List[str]:
        """Apply ignore strategy - reorder across sections, remove access specifiers."""
        new_lines = lines[:]
        
        # Remove access specifier lines
        for spec_line in access_specifiers.keys():
            new_lines[spec_line] = ""
        
        # Apply reordering
        sorted_indices = sorted(member_lines.values())
        for new_pos, member_name in enumerate(new_order):
            if member_name in member_lines:
                old_line_idx = member_lines[member_name]
                new_line_idx = sorted_indices[new_pos]
                new_lines[new_line_idx] = lines[old_line_idx]
        
        return new_lines
    
    def _get_member_access_modifiers(self, lines: List[str], member_lines: Dict[str, int], 
                                   access_specifiers: Dict[int, str], struct_start: int) -> Dict[str, str]:
        """Get access modifier for each member."""
        member_access = {}
        current_access = "public"  # Default for struct, private for class
        
        # Determine if it's a class or struct
        for i in range(max(0, struct_start - 5), struct_start + 1):
            if i < len(lines) and 'class ' in lines[i]:
                current_access = "private"
                break
        
        # Build sorted list of all relevant lines (access specifiers and members)
        all_lines = []
        for line_num, access in access_specifiers.items():
            all_lines.append((line_num, 'access', access))
        for member_name, line_num in member_lines.items():
            all_lines.append((line_num, 'member', member_name))
        
        all_lines.sort()
        
        # Assign access modifiers
        for line_num, line_type, content in all_lines:
            if line_type == 'access':
                current_access = content
            elif line_type == 'member':
                member_access[content] = current_access
        
        return member_access