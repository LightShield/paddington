"""Planning stage - converts optimization plans to source modifications."""

import os
import re
from typing import List, Optional, Tuple, Dict, Set
from pathlib import Path
from ..stage import Stage
from ...struct_data.optimization_plan import OptimizationPlan
from ...struct_data.source_change import SourceModification, Modification, Location
from ...utils.logger import log
from ...utils.template_parser import is_template_instantiation, get_base_template_name, extract_template_types


class PlanningStage(Stage[List[OptimizationPlan], List[SourceModification]]):
    """Convert optimization plans to source modifications."""
    
    def __init__(self, access_modifier_strategy: str = "preserve"):
        self.access_modifier_strategy = access_modifier_strategy
        self._compilation_data: Dict[str, List[str]] = {}
    
    def set_compilation_data(self, compilation_data: Dict[str, List[str]]):
        """Set compilation data mapping struct names to their .cpp files."""
        self._compilation_data = compilation_data
        log.info(f"Set compilation data for {len(compilation_data)} structs")
    
    def process(self, plans: List[OptimizationPlan]) -> List[SourceModification]:
        """Create source modifications from plans."""
        modifications = []
        
        for plan in plans:
            if plan.skip_reason:
                continue
            
            if not plan.struct.file_path or not plan.struct.line:
                continue
            
            # Detect template instantiations and use base template name
            struct_name = plan.struct.name
            target_struct_name = struct_name
            
            if is_template_instantiation(struct_name):
                # Use base template name for source modifications
                target_struct_name = get_base_template_name(struct_name)
                log.info(f"Template instantiation detected: {struct_name} -> {target_struct_name}")
                
                # Extract nested types for potential optimization
                nested_types = extract_template_types(struct_name)
                if nested_types:
                    log.info(f"Extracted nested types from {struct_name}: {nested_types}")
            
            # Create modifications for both .h and .cpp files
            header_mods = self._create_header_modifications(plan, target_struct_name)
            cpp_mods = self._create_cpp_modifications(plan, target_struct_name)
            
            modifications.extend(header_mods)
            modifications.extend(cpp_mods)
        
        return modifications
    
    def _normalize_path(self, file_path: str) -> str:
        """Convert absolute path to relative path for patches.
        
        Pahole gives absolute paths like /build/snapshot/common/file.h
        We need relative paths like common/file.h for patches.
        """
        if not file_path:
            return file_path
        
        # If path contains 'snapshot/', take everything after it
        if '/snapshot/' in file_path:
            return file_path.split('/snapshot/', 1)[1]
        
        # Otherwise return as-is (might already be relative)
        return file_path
    
    def _create_header_modifications(self, plan: OptimizationPlan, target_struct_name: str = None) -> List[SourceModification]:
        """Create modifications for header file (.h) member declarations."""
        if target_struct_name is None:
            target_struct_name = plan.struct.name
            
        old_members = ", ".join(m.name for m in plan.original_order)
        new_members = ", ".join(m.name for m in plan.optimal_order)
        
        # Normalize path to relative
        file_path = self._normalize_path(plan.struct.file_path)
        
        mod = Modification(
            type="reorder",
            location=Location(
                file=file_path,
                line=plan.struct.line,
                column=0
            ),
            old_content=f"members: {old_members}",
            new_content=f"members: {new_members}",
            access_strategy=self.access_modifier_strategy
        )
        
        source_mod = SourceModification(
            file_path=file_path,
            struct_name=target_struct_name,  # Use base template name
            modifications=tuple([mod]),
            access_strategy=self.access_modifier_strategy
        )
        
        return [source_mod]
    
    def _create_cpp_modifications(self, plan: OptimizationPlan, target_struct_name: str = None) -> List[SourceModification]:
        """Create modifications for .cpp files containing constructor implementations."""
        if target_struct_name is None:
            target_struct_name = plan.struct.name
            
        cpp_files = self._get_cpp_files_for_struct(plan.struct.name, plan.struct.file_path)
        
        if not cpp_files:
            log.warning(f"No .cpp files found for struct {plan.struct.name} - skipping constructor modifications")
            return []
        
        modifications = []
        old_members = ", ".join(m.name for m in plan.original_order)
        new_members = ", ".join(m.name for m in plan.optimal_order)
        
        for cpp_file in cpp_files:
            # Normalize path
            cpp_file_normalized = self._normalize_path(cpp_file)
            
            if not os.path.exists(cpp_file):
                log.warning(f"Detected .cpp file does not exist: {cpp_file}")
                continue
            
            # Validate that this .cpp file actually contains constructors for this struct
            if not self._validate_cpp_file_has_constructors(cpp_file, target_struct_name):
                log.debug(f"Skipping {cpp_file} - no constructors found for {target_struct_name}")
                continue
            
            mod = Modification(
                type="reorder_constructors",
                location=Location(
                    file=cpp_file_normalized,
                    line=1,  # srcML will find actual constructor locations
                    column=0
                ),
                old_content=f"members: {old_members}",
                new_content=f"members: {new_members}",
                access_strategy=self.access_modifier_strategy
            )
            
            source_mod = SourceModification(
                file_path=cpp_file_normalized,
                struct_name=target_struct_name,  # Use base template name
                modifications=tuple([mod]),
                access_strategy=self.access_modifier_strategy
            )
            
            modifications.append(source_mod)
            log.debug(f"Created modification for {cpp_file}")
        
        return modifications
    
    def _get_cpp_files_for_struct(self, struct_name: str, header_path: str = None) -> List[str]:
        """Get .cpp files for a struct using compilation data or filename heuristic."""
        from pathlib import Path
        
        # First try compilation data from pahole
        cpp_files = self._compilation_data.get(struct_name, [])
        
        if cpp_files:
            log.debug(f"Found {len(cpp_files)} .cpp files for {struct_name} from compilation data")
            return cpp_files
        
        # Fallback: look for .cpp file with same base name as header
        if header_path:
            header = Path(header_path)
            # Try same directory with .cpp extension
            cpp_candidate = header.with_suffix('.cpp')
            if cpp_candidate.exists():
                log.debug(f"Found .cpp file via heuristic: {cpp_candidate}")
                return [str(cpp_candidate)]
        
        log.debug(f"No .cpp files found for {struct_name}")
        return []
    
    def _validate_cpp_file_has_constructors(self, cpp_file: str, struct_name: str) -> bool:
        """Validate that a .cpp file contains constructor definitions for the struct."""
        try:
            with open(cpp_file, 'r') as f:
                content = f.read()
            
            # Look for constructor definitions: StructName::StructName(...) or StructName(...) :
            patterns = [
                rf'{re.escape(struct_name)}::{re.escape(struct_name)}\s*\([^)]*\)\s*:',  # Qualified constructor
                rf'^{re.escape(struct_name)}\s*\([^)]*\)\s*:',  # Inline constructor
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE):
                    return True
            
            return False
        except Exception as e:
            log.debug(f"Error validating {cpp_file}: {e}")
            return False
    
    def _parse_pahole_source_locations(self, pahole_output: str) -> Dict[str, List[int]]:
        """Parse pahole -I output to extract source file locations."""
        source_files = {}
        
        # Pattern: /* <offset> /path/file.cpp:line */
        pattern = r'/\*\s*<[0-9a-f]+>\s*(.+):(\d+)\s*\*/'
        
        for match in re.finditer(pattern, pahole_output):
            file_path = match.group(1)
            line_num = int(match.group(2))
            
            if file_path not in source_files:
                source_files[file_path] = []
            source_files[file_path].append(line_num)
        
        return source_files
    
    def _build_struct_to_cpp_mapping(self, structs_with_sources: List[Dict]) -> Dict[str, List[str]]:
        """Build mapping from struct names to their .cpp implementation files."""
        mapping = {}
        
        for struct_data in structs_with_sources:
            struct_name = struct_data["name"]
            sources = struct_data.get("sources", [])
            
            # Filter to only .cpp files (exclude headers)
            cpp_files = [f for f in sources if f.endswith(('.cpp', '.cc', '.cxx', '.C'))]
            
            if cpp_files:
                mapping[struct_name] = cpp_files
        
        return mapping
    
    # For testing - allow setting compilation data directly
    def _set_compilation_data(self, data: Dict[str, List[str]]):
        """Set compilation data (for testing)."""
        self._compilation_data = data
    
    def validate_input(self, plans: List[OptimizationPlan]) -> bool:
        """Validate input plans."""
        return isinstance(plans, list) and all(isinstance(p, OptimizationPlan) for p in plans)
