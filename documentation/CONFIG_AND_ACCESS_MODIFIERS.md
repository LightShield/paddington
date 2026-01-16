# Configuration & Access Modifier Requirements - Summary

**Date**: 2026-01-16  
**Changes**: Based on user feedback

---

## Key Changes to Requirements

### 1. Configuration Format: TOML (not YAML)

**File**: `paddington.toml` (not `paddington.yaml`)

**Rationale**: 
- More readable for configuration
- Better type support
- Standard in Rust/Python ecosystems

### 2. Configuration Priority Hierarchy

**Priority** (lowest to highest):
1. **Defaults**: Hardcoded in code
2. **Preset**: `paddington.toml` in project root
3. **CLI**: Command-line flags

**Example**:
```toml
# paddington.toml
[optimization]
min_savings = 8
```

```bash
# CLI overrides preset
paddington optimize build/ --min-savings 16  # Uses 16, not 8
```

**Implementation**:
```python
config = merge(defaults, load_toml("paddington.toml"), parse_cli_args())
```

### 3. Configuration Logging

**Requirement**: Log final configuration at startup (INFO level)

**Example Output**:
```
[INFO] Configuration loaded:
[INFO]   optimization.min_savings: 16 (cli override)
[INFO]   optimization.respect_access_modifiers: true (preset)
[INFO]   extraction.provider: pahole (preset)
[INFO]   transformation.provider: srcml (default)
```

**Why**: Users need to know what configuration is actually being used, especially when debugging.

---

## Access Modifier Preservation

### Problem

Original requirement: "No change to program behavior"

**Question**: Does this include access modifiers?

**Answer**: YES, by default.

### Solution

**New Configuration Option**: `respect_access_modifiers`

**Default**: `true` (preserve access modifiers)

**Behavior**:

#### When `respect_access_modifiers = true` (default):
```cpp
// Before
class Data {
public:
    char a;    // 1 byte
    int b;     // 4 bytes
private:
    char c;    // 1 byte
    double d;  // 8 bytes
};

// After: Reorder WITHIN each section
class Data {
public:
    int b;     // 4 bytes (largest in public)
    char a;    // 1 byte
private:
    double d;  // 8 bytes (largest in private)
    char c;    // 1 byte
};
```

**Padding savings**: Limited (can't move `double d` to top)

#### When `respect_access_modifiers = false`:
```cpp
// After: Reorder ACROSS all sections
class Data {
public:
    double d;  // 8 bytes (moved from private, largest overall)
    int b;     // 4 bytes
private:
    char a;    // 1 byte (moved from public)
    char c;    // 1 byte
};
```

**Padding savings**: Maximum (optimal ordering)

**Semantic change**: YES - changes encapsulation (private members become public)

### Why This Matters

**Encapsulation**: Moving private members to public section breaks encapsulation.

**ABI Compatibility**: Changing member order across access modifiers may break ABI.

**User Control**: Some projects prioritize memory over encapsulation, others don't.

### Implementation Impact

**Data Model**:
```python
@dataclass(frozen=True)
class MemberInfo:
    name: str
    type: str
    size: int
    optimized_size: Optional[int]
    offset: int
    access_modifier: str  # "public", "private", "protected", "none"
    locked: bool = False
```

**Stage 2 (Analysis)**:
```python
def get_optimal_member_order(struct: StructInfo, config: Config) -> List[MemberInfo]:
    if config.respect_access_modifiers:
        # Group by access modifier, sort within each group
        groups = group_by_access_modifier(struct.members)
        result = []
        for group in groups:
            sorted_group = sort_by_size_descending(group)
            result.extend(sorted_group)
        return result
    else:
        # Sort all members together
        return sort_by_size_descending(struct.members)
```

**Stage 4 (Transformation)**:
- srcML: Preserve access modifier sections when reordering
- Line-swap: Track access modifier boundaries, don't cross them

---

## Custom Directive Markers

### Question

Should we support custom directive markers?

Example:
```toml
[directives]
ignore_marker = "my-custom-ignore"  # Instead of "paddington-ignore"
```

### Answer

**NO, not initially.**

**Rationale**:

1. **Complexity**: Adds parsing complexity, validation, documentation burden
2. **No clear use case**: When would you need custom markers?
   - If you have existing markers? Just use paddington's markers
   - If you want different names? Why? Consistency is better
3. **Can be added later**: If users request it, add as P2 feature
4. **Standard is better**: Consistent markers across all projects using paddington

**Decision**: Use standard markers only:
- `paddington-ignore` (struct-level)
- `paddington-lock` / `paddington-unlock` (member-level)
- `paddington-off` / `paddington-on` (region-level)

These are NOT configurable in v1.0.

---

## Configuration File Structure

### Complete Example

```toml
# paddington.toml

[optimization]
min_savings = 8                    # Only optimize if saves ≥8 bytes
respect_access_modifiers = true    # Don't move members across public/private/protected

[extraction]
provider = "pahole"                # "pahole" or "dwarf"
cache_dir = ".paddington_cache"    # Cache parsed .o files
deduplicate = true                 # Skip duplicate .o files by content hash
timeout = 300                      # Timeout per file (seconds)

[transformation]
provider = "srcml"                 # "srcml" or "line-swap"
preserve_formatting = true         # Preserve whitespace/comments (srcml only)

[application]
provider = "patch"                 # "patch" or "file-writer"
patch_dir = "./patches"            # Where to write patches
create_backups = true              # Create .backup files

[reporting]
verbosity = "INFO"                 # ERROR, WARNING, INFO, DEBUG, TRACE
show_skipped = true                # Show skipped structs in summary
show_savings = true                # Show memory savings in summary
progress_bar = true                # Show progress bars for long operations

[filtering]
include = ["*/src/*.o"]            # Only process these files
exclude = ["*/test/*.o", "*/vendor/*.o"]  # Skip these files
```

### CLI Overrides

All configuration options available via CLI:

```bash
paddington optimize build/ \
  --min-savings 16 \
  --respect-access-modifiers false \
  --extractor pahole \
  --transformer srcml \
  --applicator patch \
  --patch-dir ./my-patches \
  --include "*/core/*.o" \
  --exclude "*/test/*.o" \
  -vvv
```

### Configuration Loading

```python
# 1. Load defaults
config = Config.defaults()

# 2. Load preset file (if exists)
if Path("paddington.toml").exists():
    preset = load_toml("paddington.toml")
    config = config.merge(preset)

# 3. Load CLI args
cli = parse_args()
config = config.merge(cli)

# 4. Log final config
log.info("Configuration loaded:")
for key, value in config.items():
    source = config.get_source(key)  # "default", "preset", or "cli"
    log.info(f"  {key}: {value} ({source})")
```

---

## Architecture Implications

### New Module: Configuration Manager

```python
# cli/config.py

@dataclass(frozen=True)
class Config:
    """Immutable configuration with source tracking."""
    
    # Optimization
    min_savings: int
    respect_access_modifiers: bool
    
    # Extraction
    extraction_provider: str
    cache_dir: Optional[Path]
    deduplicate: bool
    
    # Transformation
    transformation_provider: str
    preserve_formatting: bool
    
    # Application
    application_provider: str
    patch_dir: Optional[Path]
    
    # Reporting
    verbosity: str
    show_skipped: bool
    show_savings: bool
    
    # Filtering
    include_patterns: List[str]
    exclude_patterns: List[str]
    
    # Source tracking (for logging)
    _sources: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def defaults(cls) -> "Config":
        """Create config with default values."""
        return cls(
            min_savings=0,
            respect_access_modifiers=True,
            extraction_provider="pahole",
            cache_dir=None,
            deduplicate=False,
            transformation_provider="srcml",
            preserve_formatting=True,
            application_provider="patch",
            patch_dir=Path("./patches"),
            verbosity="INFO",
            show_skipped=True,
            show_savings=True,
            include_patterns=[],
            exclude_patterns=[],
            _sources={}
        )
    
    def merge(self, other: Dict[str, Any], source: str) -> "Config":
        """Merge with another config, tracking sources."""
        # Create new config with updated values
        # Track which values came from which source
        pass
    
    def get_source(self, key: str) -> str:
        """Get source of a config value (default/preset/cli)."""
        return self._sources.get(key, "default")
    
    def log(self, logger):
        """Log configuration with sources."""
        logger.info("Configuration loaded:")
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            source = self.get_source(key)
            logger.info(f"  {key}: {value} ({source})")
```

### Updated Agent Tasks

**Agent 17: CLI** (Phase 5)
- Load configuration from defaults → preset → CLI
- Log final configuration at startup
- Pass configuration to pipeline stages

**Agent 13: Analysis Stage** (Phase 4)
- Accept `respect_access_modifiers` config
- Group members by access modifier if needed
- Sort within groups or across all members

**Agent 15: Transformation Stage** (Phase 4)
- Preserve access modifier sections when reordering
- Don't cross access modifier boundaries if configured

---

## Testing Implications

### Unit Tests

```python
def test_config_priority():
    """Test configuration priority: default < preset < cli."""
    defaults = Config.defaults()
    assert defaults.min_savings == 0
    
    preset = {"min_savings": 8}
    config = defaults.merge(preset, "preset")
    assert config.min_savings == 8
    assert config.get_source("min_savings") == "preset"
    
    cli = {"min_savings": 16}
    config = config.merge(cli, "cli")
    assert config.min_savings == 16
    assert config.get_source("min_savings") == "cli"

def test_respect_access_modifiers_true():
    """Test member reordering respects access modifiers."""
    struct = StructInfo(
        name="Data",
        members=[
            MemberInfo(name="a", size=1, access_modifier="public"),
            MemberInfo(name="b", size=4, access_modifier="public"),
            MemberInfo(name="c", size=1, access_modifier="private"),
            MemberInfo(name="d", size=8, access_modifier="private"),
        ]
    )
    
    config = Config(respect_access_modifiers=True)
    optimal = get_optimal_member_order(struct, config)
    
    # Should be: [b(4), a(1)] in public, [d(8), c(1)] in private
    assert optimal[0].name == "b"
    assert optimal[1].name == "a"
    assert optimal[2].name == "d"
    assert optimal[3].name == "c"

def test_respect_access_modifiers_false():
    """Test member reordering ignores access modifiers."""
    struct = StructInfo(
        name="Data",
        members=[
            MemberInfo(name="a", size=1, access_modifier="public"),
            MemberInfo(name="b", size=4, access_modifier="public"),
            MemberInfo(name="c", size=1, access_modifier="private"),
            MemberInfo(name="d", size=8, access_modifier="private"),
        ]
    )
    
    config = Config(respect_access_modifiers=False)
    optimal = get_optimal_member_order(struct, config)
    
    # Should be: [d(8), b(4), a(1), c(1)] regardless of access
    assert optimal[0].name == "d"
    assert optimal[1].name == "b"
    assert optimal[2].name == "a"
    assert optimal[3].name == "c"
```

---

## Summary

### Changes Made

1. ✅ Configuration format: TOML (not YAML)
2. ✅ Configuration priority: default < preset < cli
3. ✅ Configuration logging: Log final values with sources
4. ✅ Access modifier preservation: Configurable via `respect_access_modifiers`
5. ✅ Custom directive markers: NOT supported (standard markers only)

### New Requirements

- FR-1.6.4: Configuration Logging (P0)
- NFR-2.4.2: Configuration priority hierarchy (P0)
- FR-1.1.2: Access modifier handling (P0)
- C-4.2.2: Clarified semantic preservation (P0)

### Data Model Changes

- `MemberInfo.access_modifier: str` (NEW)
- `Config` class with source tracking (NEW)

### Architecture Changes

- New module: `cli/config.py` (Configuration manager)
- Updated: Agent 13 (Analysis) - handle access modifiers
- Updated: Agent 15 (Transformation) - preserve access modifiers
- Updated: Agent 17 (CLI) - load and log configuration

### Priority

All changes are **P0 (Must Have)** - core functionality.
