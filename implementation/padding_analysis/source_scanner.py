"""One-time source code scanner for all struct-related checks."""

import re
import json
import hashlib
from pathlib import Path
from typing import Set, Dict, Tuple, List
import fnmatch


def _is_trivial_preprocessor_case(struct_body: str) -> bool:
    """Check if preprocessor directives are trivial (safe to optimize).
    
    Trivial cases:
    - Only methods affected (no data members in #ifdef)
    - Only comments in #ifdef
    
    Returns:
        True if safe to optimize despite preprocessor
    """
    # Find all #ifdef...#endif blocks
    ifdef_blocks = []
    lines = struct_body.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r'#\s*(?:ifdef|ifndef|if\s)', line):
            # Start of block
            block_start = i
            depth = 1
            i += 1
            while i < len(lines) and depth > 0:
                if re.match(r'#\s*(?:ifdef|ifndef|if\s)', lines[i].strip()):
                    depth += 1
                elif re.match(r'#\s*endif', lines[i].strip()):
                    depth -= 1
                i += 1
            ifdef_blocks.append((block_start, i))
        else:
            i += 1
    
    # Check each block for data members
    for start, end in ifdef_blocks:
        block_lines = lines[start:end]
        for line in block_lines:
            line = line.strip()
            # Skip preprocessor lines, comments, empty lines
            if line.startswith('#') or line.startswith('//') or line.startswith('/*') or not line:
                continue
            # Check if it's a data member (has semicolon, no parentheses = not a method)
            if ';' in line and '(' not in line:
                # Likely a data member
                return False
    
    # No data members in #ifdef blocks - safe
    return True


def _scan_single_file(file_path: Path) -> Tuple[Set[str], Set[str], Dict[str, Dict[str, Set[str]]], Set[str], Dict[str, list]]:
    """Scan a single file for patterns (for multiprocessing).
    
    Returns:
        Tuple of (agg_init_structs, preprocessor_structs, constructor_deps, static_const_structs, nested_types)
        where:
        - constructor_deps is {struct_name: {member: {dependencies}}}
        - nested_types is {struct_name: [list of typedef/using/nested struct names]}
    """
    agg_structs = set()
    prep_structs = set()
    constructor_deps = {}
    static_const_structs = set()  # Structs with static const members
    nested_types_map = {}  # Structs with nested types
    
    try:
        content = file_path.read_text()
    except:
        return agg_structs, prep_structs, constructor_deps, static_const_structs, nested_types_map
    
    # Check for aggregate initialization patterns
    # Pattern: TypeName varname = {val1, val2, ...} or TypeName varname{val1, val2, ...}
    agg_init_pattern = r'\b([A-Za-z_]\w+)\s+\w+\s*=?\s*\{.+?,.+?\}'
    for match in re.finditer(agg_init_pattern, content):
        struct_name = match.group(1)
        # Skip C++ keywords
        if struct_name not in ['struct', 'class', 'union', 'enum', 'if', 'for', 'while', 'switch', 'return']:
            agg_structs.add(struct_name)
    
    # Check for preprocessor directives in struct definitions
    struct_pattern = r'(?:struct|class)\s+(\w+)\s*[:{]'
    for match in re.finditer(struct_pattern, content):
        struct_name = match.group(1)
        start_pos = match.end()
        brace_count = 1
        pos = start_pos
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        struct_body = content[start_pos:pos]
        
        # Check for static const members (data members only, not methods)
        # Match: static const Type name = value; or static const Type name;
        # Don't match: static Type method(...);
        if re.search(r'\bstatic\s+const\s+\w+[^(]*?[;=]|constexpr\s+\w+[^(]*?[;=]', struct_body):
            static_const_structs.add(struct_name)
        
        # Check for nested types (typedef, using, nested struct/class/enum)
        # Note: Enums are safe and don't affect member layout
        nested_types = []
        if re.search(r'\btypedef\s+', struct_body):
            nested_types.append('typedef')
        if re.search(r'\busing\s+\w+\s*=', struct_body):
            nested_types.append('using')
        # Only flag nested struct/class, not enum (enums are safe)
        if re.search(r'\b(?:struct|class)\s+\w+\s*[:{]', struct_body):
            nested_types.append('nested_struct')
        if nested_types:
            nested_types_map[struct_name] = nested_types
        
        # Check for preprocessor directives
        if re.search(r'#\s*(?:if|ifdef|ifndef|elif|else|endif)', struct_body):
            # Has preprocessor - check if it's a trivial safe case
            is_trivial_safe = _is_trivial_preprocessor_case(struct_body)
            if not is_trivial_safe:
                prep_structs.add(struct_name)
            # If trivial safe, don't add to prep_structs (allow optimization)
    
    # Check for constructor dependencies
    # Find all struct/class definitions and their members
    struct_members_map = _extract_all_struct_members(content)
    
    # Find constructor initializer lists
    for struct_name, members in struct_members_map.items():
        deps = _find_constructor_dependencies(content, struct_name, members)
        if deps:
            constructor_deps[struct_name] = deps
    
    return agg_structs, prep_structs, constructor_deps, static_const_structs, nested_types_map


def _extract_all_struct_members(content: str) -> Dict[str, Set[str]]:
    """Extract member names for all structs in the file."""
    struct_members = {}
    
    # Find all struct/class definitions
    struct_pattern = r'(?:struct|class)\s+(\w+)\s*[:{]([^}]+)\}'
    for match in re.finditer(struct_pattern, content, re.MULTILINE | re.DOTALL):
        struct_name = match.group(1)
        struct_body = match.group(2)
        
        members = set()
        # Split by semicolons
        declarations = struct_body.split(';')
        
        for decl in declarations:
            decl = decl.strip()
            if not decl or '//' in decl or '/*' in decl:
                continue
            
            # Skip constructor/destructor/function declarations
            if '(' in decl or decl.startswith('~') or decl.startswith(struct_name):
                continue
            
            # Extract member name
            tokens = decl.split()
            if len(tokens) >= 2:
                member_name = tokens[-1].strip('*&')
                if member_name.isidentifier():
                    members.add(member_name)
        
        if members:
            struct_members[struct_name] = members
    
    return struct_members


def _find_constructor_dependencies(content: str, struct_name: str, members: Set[str]) -> Dict[str, Set[str]]:
    """Find constructor initializer list dependencies for a struct."""
    dependencies = {}
    
    # Pattern: struct_name(...) : member1(...), member2(...) { ... }
    pattern = rf'{re.escape(struct_name)}\s*\([^)]*\)\s*:\s*([^{{]+)'
    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
    
    for init_list in matches:
        # Parse initializer list
        member_inits = _parse_initializer_list(init_list)
        
        for member_init in member_inits:
            # Extract member name and initialization expression
            member_match = re.match(r'(\w+)\s*\(([^)]*)\)', member_init.strip())
            if member_match:
                member_name = member_match.group(1)
                init_expr = member_match.group(2)
                
                # Find references to other members
                referenced = _find_member_references(init_expr, members)
                if referenced:
                    if member_name not in dependencies:
                        dependencies[member_name] = set()
                    dependencies[member_name].update(referenced)
    
    return dependencies


def _parse_initializer_list(init_list: str) -> List[str]:
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


def _find_member_references(expr: str, struct_members: Set[str]) -> Set[str]:
    """Find member variable references in an expression."""
    identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
    return {ident for ident in identifiers if ident in struct_members}


class SourceScanner:
    """Scan source files once and cache all struct-related information."""
    
    def __init__(self, source_root: str, exclude_patterns: List[str] = None, workspace_dir: str = None):
        self.source_root = Path(source_root)
        self.exclude_patterns = exclude_patterns or []
        
        # Cached results
        self.structs_with_aggregate_init: Set[str] = set()
        self.structs_with_preprocessor: Set[str] = set()
        self.constructor_dependencies: Dict[str, Dict[str, Set[str]]] = {}
        self.structs_with_static_const: Set[str] = set()
        self.structs_with_nested_types: Dict[str, list] = {}  # struct_name -> [nested type names]
        self._scanned = False
        
        # Workspace directory structure
        if workspace_dir:
            self.workspace_dir = Path(workspace_dir)
        else:
            self.workspace_dir = Path.cwd() / '.paddington_workspace'
        
        # Create workspace structure
        self.scan_cache_dir = self.workspace_dir / 'scan_cache'
        self.extraction_cache_dir = self.workspace_dir / 'extraction_cache'
        
        # Cache file location (moved to workspace)
        self.cache_file = self.scan_cache_dir / '.paddington_scan_cache.json'
    
    def _ensure_cache_directories(self):
        """Create cache directories if they don't exist."""
        self.scan_cache_dir.mkdir(parents=True, exist_ok=True)
        self.extraction_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded based on patterns."""
        from ..utils.path_exclusion import should_exclude_path
        return should_exclude_path(file_path, self.exclude_patterns, self.source_root)
    
    def scan(self):
        """Scan all source files once and populate caches."""
        if self._scanned:
            return
        
        from ..utils.logger import log
        
        # Ensure cache directories exist
        self._ensure_cache_directories()
        
        # Try to load from cache first
        if self._load_from_cache():
            log.info(f"Loaded scan results from cache: {self.cache_file}")
            self._scanned = True
            return
        
        log.info(f"Scanning source tree once: {self.source_root}")
        
        # Collect all files using os.walk to skip excluded directories
        import os
        from ..utils.path_exclusion import should_exclude_directory
        
        extensions = {'.cpp', '.cc', '.cxx', '.h', '.hpp', '.C'}
        all_files = []
        
        for root, dirs, files in os.walk(self.source_root):
            root_path = Path(root)
            
            # Filter out excluded directories before descending
            dirs[:] = [d for d in dirs if not should_exclude_directory(root_path / d, self.exclude_patterns, self.source_root)]
            
            # Process files in current directory
            for file in files:
                file_path = root_path / file
                if file_path.suffix in extensions and not self._should_exclude(file_path):
                    all_files.append(file_path)
        
        file_count = len(all_files)
        log.info(f"Found {file_count} source files to scan (after exclusions)")
        
        # Parallel scan for large file sets
        if file_count > 100:
            from multiprocessing import Pool, cpu_count
            import time
            
            num_workers = max(1, int(cpu_count() * 0.8))
            log.info(f"Scanning with {num_workers} workers")
            
            start_time = time.time()
            last_progress = 0
            
            with Pool(num_workers) as pool:
                # Use imap_unordered for progress tracking
                results_iter = pool.imap_unordered(_scan_single_file, all_files, chunksize=50)
                
                for i, (agg_structs, prep_structs, ctor_deps, static_structs, nested_types) in enumerate(results_iter, 1):
                    self.structs_with_aggregate_init.update(agg_structs)
                    self.structs_with_preprocessor.update(prep_structs)
                    self.structs_with_static_const.update(static_structs)
                    # Merge nested types
                    for struct_name, types_list in nested_types.items():
                        if struct_name not in self.structs_with_nested_types:
                            self.structs_with_nested_types[struct_name] = []
                        self.structs_with_nested_types[struct_name].extend(types_list)
                    # Merge constructor dependencies
                    for struct_name, deps in ctor_deps.items():
                        if struct_name not in self.constructor_dependencies:
                            self.constructor_dependencies[struct_name] = {}
                        for member, member_deps in deps.items():
                            if member not in self.constructor_dependencies[struct_name]:
                                self.constructor_dependencies[struct_name][member] = set()
                            self.constructor_dependencies[struct_name][member].update(member_deps)
                    
                    # Progress every 1000 files or 10 seconds
                    if i % 1000 == 0 or (time.time() - last_progress) > 10:
                        elapsed = time.time() - start_time
                        rate = i / elapsed if elapsed > 0 else 0
                        eta = (file_count - i) / rate if rate > 0 else 0
                        log.info(f"  Scanned {i}/{file_count} files ({rate:.0f} files/sec, ETA: {eta:.0f}s)")
                        last_progress = time.time()
        else:
            # Serial scan for small sets
            for i, file_path in enumerate(all_files, 1):
                if i % 100 == 0:
                    log.debug(f"  Scanned {i}/{file_count} files...")
                agg_structs, prep_structs, ctor_deps, static_structs, nested_types = _scan_single_file(file_path)
                self.structs_with_aggregate_init.update(agg_structs)
                self.structs_with_preprocessor.update(prep_structs)
                self.structs_with_static_const.update(static_structs)
                # Merge nested types
                for struct_name, types_list in nested_types.items():
                    if struct_name not in self.structs_with_nested_types:
                        self.structs_with_nested_types[struct_name] = []
                    self.structs_with_nested_types[struct_name].extend(types_list)
                # Merge constructor dependencies
                for struct_name, deps in ctor_deps.items():
                    if struct_name not in self.constructor_dependencies:
                        self.constructor_dependencies[struct_name] = {}
                    for member, member_deps in deps.items():
                        if member not in self.constructor_dependencies[struct_name]:
                            self.constructor_dependencies[struct_name][member] = set()
                        self.constructor_dependencies[struct_name][member].update(member_deps)
        
        log.info(f"Scanned {file_count} files")
        log.info(f"Found {len(self.structs_with_aggregate_init)} structs with aggregate init")
        log.info(f"Found {len(self.structs_with_preprocessor)} structs with preprocessor directives")
        log.info(f"Found {len(self.constructor_dependencies)} structs with constructor dependencies")
        log.info(f"Found {len(self.structs_with_static_const)} structs with static const members")
        
        # Save to cache
        self._save_to_cache()
        log.info(f"Saved scan results to cache: {self.cache_file}")
        
        self._scanned = True
    
    def _compute_cache_key(self, all_files: List[Path]) -> str:
        """Compute cache key based on file mtimes and exclusions."""
        # Hash: file paths + mtimes + exclusions
        hasher = hashlib.md5()
        for f in sorted(all_files):
            hasher.update(str(f).encode())
            hasher.update(str(f.stat().st_mtime).encode())
        hasher.update(str(sorted(self.exclude_patterns)).encode())
        return hasher.hexdigest()
    
    def _load_from_cache(self) -> bool:
        """Load scan results from cache if valid."""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            # Verify cache is still valid (check file mtimes)
            import os
            from ..utils.path_exclusion import should_exclude_directory
            
            extensions = {'.cpp', '.cc', '.cxx', '.h', '.hpp', '.C'}
            all_files = []
            
            for root, dirs, files in os.walk(self.source_root):
                root_path = Path(root)
                
                # Filter out excluded directories before descending
                dirs[:] = [d for d in dirs if not should_exclude_directory(root_path / d, self.exclude_patterns, self.source_root)]
                
                # Process files in current directory
                for file in files:
                    file_path = root_path / file
                    if file_path.suffix in extensions and not self._should_exclude(file_path):
                        all_files.append(file_path)
            
            cache_key = self._compute_cache_key(all_files)
            if data.get('cache_key') != cache_key:
                return False  # Cache invalid
            
            # Load cached results
            self.structs_with_aggregate_init = set(data.get('aggregate_init', []))
            self.structs_with_preprocessor = set(data.get('preprocessor', []))
            self.structs_with_static_const = set(data.get('static_const', []))
            # Convert constructor deps back to nested dicts with sets
            ctor_deps_raw = data.get('constructor_deps', {})
            self.constructor_dependencies = {
                struct: {member: set(deps) for member, deps in member_deps.items()}
                for struct, member_deps in ctor_deps_raw.items()
            }
            return True
        except:
            return False
    
    def _save_to_cache(self):
        """Save scan results to cache."""
        try:
            # Ensure cache directories exist
            self._ensure_cache_directories()
            
            # Collect all files for cache key
            import os
            from ..utils.path_exclusion import should_exclude_directory
            
            extensions = {'.cpp', '.cc', '.cxx', '.h', '.hpp', '.C'}
            all_files = []
            
            for root, dirs, files in os.walk(self.source_root):
                root_path = Path(root)
                
                # Filter out excluded directories before descending
                dirs[:] = [d for d in dirs if not should_exclude_directory(root_path / d, self.exclude_patterns, self.source_root)]
                
                # Process files in current directory
                for file in files:
                    file_path = root_path / file
                    if file_path.suffix in extensions and not self._should_exclude(file_path):
                        all_files.append(file_path)
            
            cache_key = self._compute_cache_key(all_files)
            
            # Convert sets to lists for JSON
            data = {
                'cache_key': cache_key,
                'aggregate_init': list(self.structs_with_aggregate_init),
                'preprocessor': list(self.structs_with_preprocessor),
                'static_const': list(self.structs_with_static_const),
                'constructor_deps': {
                    struct: {member: list(deps) for member, deps in member_deps.items()}
                    for struct, member_deps in self.constructor_dependencies.items()
                }
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass  # Don't fail if caching fails
    
    def has_aggregate_initialization(self, struct_name: str) -> bool:
        """Check if struct has aggregate initialization."""
        if not self._scanned:
            self.scan()
        return struct_name in self.structs_with_aggregate_init
    
    def has_preprocessor_directives(self, struct_name: str) -> bool:
        """Check if struct has preprocessor directives."""
        if not self._scanned:
            self.scan()
        return struct_name in self.structs_with_preprocessor
    
    def get_constructor_dependencies(self, struct_name: str) -> Dict[str, Set[str]]:
        """Get constructor dependencies for a struct.
        
        Returns:
            Dict mapping member_name -> set of members it depends on
            Empty dict if no dependencies found
        """
        if not self._scanned:
            self.scan()
        return self.constructor_dependencies.get(struct_name, {})
    
    def has_static_const_members(self, struct_name: str) -> bool:
        """Check if struct has static const members.
        
        Returns:
            True if struct has static const or constexpr members
        """
        if not self._scanned:
            self.scan()
        return struct_name in self.structs_with_static_const
