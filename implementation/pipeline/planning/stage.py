"""Planning stage - converts optimization plans to source modifications."""

import os
import re
from typing import List, Optional, Tuple
from ..stage import Stage
from ...struct_data.optimization_plan import OptimizationPlan
from ...struct_data.source_change import SourceModification, Modification, Location


class PlanningStage(Stage[List[OptimizationPlan], List[SourceModification]]):
    """Convert optimization plans to source modifications."""
    
    def __init__(self, access_modifier_strategy: str = "preserve"):
        self.access_modifier_strategy = access_modifier_strategy
    
    def process(self, plans: List[OptimizationPlan]) -> List[SourceModification]:
        """Create source modifications from plans."""
        modifications = []
        
        for plan in plans:
            if plan.skip_reason:
                continue
            
            if not plan.struct.file_path or not plan.struct.line:
                continue
            
            # Create modifications for both .h and .cpp files
            header_mods = self._create_header_modifications(plan)
            cpp_mods = self._create_cpp_modifications(plan)
            
            modifications.extend(header_mods)
            modifications.extend(cpp_mods)
        
        return modifications
    
    def _create_header_modifications(self, plan: OptimizationPlan) -> List[SourceModification]:
        """Create modifications for header file (.h) member declarations."""
        old_members = ", ".join(m.name for m in plan.original_order)
        new_members = ", ".join(m.name for m in plan.optimal_order)
        
        mod = Modification(
            type="reorder",
            location=Location(
                file=plan.struct.file_path,
                line=plan.struct.line,
                column=0
            ),
            old_content=f"members: {old_members}",
            new_content=f"members: {new_members}",
            access_strategy=self.access_modifier_strategy
        )
        
        source_mod = SourceModification(
            file_path=plan.struct.file_path,
            struct_name=plan.struct.name,
            modifications=tuple([mod]),
            access_strategy=self.access_modifier_strategy
        )
        
        return [source_mod]
    
    def _create_cpp_modifications(self, plan: OptimizationPlan) -> List[SourceModification]:
        """Create modifications for corresponding .cpp file constructor initializer lists."""
        cpp_file = self._find_corresponding_cpp_file(plan.struct.file_path)
        
        if not cpp_file or not os.path.exists(cpp_file):
            return []
        
        try:
            with open(cpp_file, 'r') as f:
                content = f.read()
        except (IOError, OSError) as e:
            return []
        
        # Find constructor initializer lists for this struct
        constructor_locations = self._find_constructor_initializer_lists(
            content, plan.struct.name, plan.original_order, plan.optimal_order, cpp_file
        )
        
        if not constructor_locations:
            return []
        
        modifications = []
        for location, old_content, new_content in constructor_locations:
            mod = Modification(
                type="reorder_initializer_list",
                location=location,
                old_content=old_content,
                new_content=new_content,
                access_strategy=self.access_modifier_strategy
            )
            
            source_mod = SourceModification(
                file_path=cpp_file,
                struct_name=plan.struct.name,
                modifications=tuple([mod]),
                access_strategy=self.access_modifier_strategy
            )
            modifications.append(source_mod)
        
        return modifications
    
    def _find_corresponding_cpp_file(self, header_file: str) -> Optional[str]:
        """Find corresponding .cpp file for a .h file."""
        if not header_file.endswith('.h'):
            return None
        
        base_name = header_file[:-2]  # Remove .h extension
        cpp_file = base_name + '.cpp'
        
        if os.path.exists(cpp_file):
            return cpp_file
        
        # Try other common patterns
        alternatives = [
            base_name + '.cc',
            base_name + '.cxx',
            base_name + '.C'
        ]
        
        for alt in alternatives:
            if os.path.exists(alt):
                return alt
        
        return None
    
    def _find_constructor_initializer_lists(
        self, 
        content: str, 
        struct_name: str, 
        original_order: Tuple, 
        optimal_order: Tuple,
        cpp_file: str
    ) -> List[Tuple[Location, str, str]]:
        """Find and create modifications for constructor initializer lists."""
        results = []
        
        # Pattern to match constructor initializer lists
        # Matches: struct_name::struct_name(...) : member1(...), member2(...) {
        # Also matches: struct_name(...) : for inline constructors
        pattern = rf'(?:{re.escape(struct_name)}::)?{re.escape(struct_name)}\s*\([^)]*\)\s*:\s*([^{{]+)'
        
        lines = content.split('\n')
        matches_found = 0
        for line_num, line in enumerate(lines, 1):
            match = re.search(pattern, line)
            if match:
                matches_found += 1
                init_list = match.group(1).strip()
                
                # Parse the initializer list
                old_init_list = self._parse_and_reorder_initializer_list(
                    init_list, original_order, optimal_order
                )
                
                if old_init_list:
                    old_content, new_content = old_init_list
                    location = Location(
                        file=cpp_file,  # Set the correct file path
                        line=line_num,
                        column=match.start(1)
                    )
                    results.append((location, old_content, new_content))
        
        return results
    
    def _parse_and_reorder_initializer_list(
        self, 
        init_list: str, 
        original_order: Tuple, 
        optimal_order: Tuple
    ) -> Optional[Tuple[str, str]]:
        """Parse initializer list and reorder according to optimal order."""
        # Extract member initializations
        member_inits = self._parse_initializer_list(init_list)
        
        # Create mapping from member name to initialization
        init_map = {}
        for init in member_inits:
            match = re.match(r'(\w+)\s*\(([^)]*)\)', init.strip())
            if match:
                member_name = match.group(1)
                init_map[member_name] = init.strip()
        
        # Check if we have initializations for members in the original order
        original_names = [m.name for m in original_order]
        optimal_names = [m.name for m in optimal_order]
        
        # Only reorder if we have initializations for the members
        relevant_inits = {name: init_map[name] for name in original_names if name in init_map}
        
        if not relevant_inits:
            return None
        
        # Create old and new content
        old_content = ", ".join(relevant_inits[name] for name in original_names if name in relevant_inits)
        new_content = ", ".join(relevant_inits[name] for name in optimal_names if name in relevant_inits)
        
        if old_content == new_content:
            return None
        
        return old_content, new_content
    
    def _parse_initializer_list(self, init_list: str) -> List[str]:
        """Parse comma-separated initializer list, respecting parentheses."""
        members = []
        current = ""
        paren_depth = 0
        
        for char in init_list:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                if current.strip():
                    members.append(current.strip())
                current = ""
                continue
            current += char
        
        if current.strip():
            members.append(current.strip())
        
        return members
    
    def validate_input(self, plans: List[OptimizationPlan]) -> bool:
        """Validate input plans."""
        return isinstance(plans, list) and all(isinstance(p, OptimizationPlan) for p in plans)
