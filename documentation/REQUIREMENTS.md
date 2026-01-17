# paddingTON: Requirements Document

**Version**: 1.0  
**Date**: 2026-01-16  
**Status**: Draft

---

## 1. Functional Requirements

### 1.1 Core Functionality

#### FR-1.1.1: Struct Padding Detection
**Description**: The system shall detect padding waste in C++ structs/classes.

**Acceptance Criteria**:
- Extract struct layout from compiled object files (`.o` with debug info)
- Calculate internal padding (gaps between members)
- Calculate trailing padding (gap at end of struct)
- Report total padding per struct
- Report potential savings if optimized

**Priority**: P0 (Must Have)

#### FR-1.1.2: Member Reordering
**Description**: The system shall reorder struct members to minimize padding.

**Acceptance Criteria**:
- Sort members by size descending (largest first)
- Preserve member names, types, and values
- Maintain C++ semantics (no behavior change)
- **Preserve access modifiers** (public, private, protected)
- Handle nested structs (optimize dependencies first)

**Access Modifier Handling**:
- **preserve**: Keep members in their original access modifier sections (default, safest)
- **split**: Reorder optimally, add access modifiers per member if needed (aggressive)
- **ignore**: Reorder across all sections, don't preserve access modifiers (most aggressive, breaks encapsulation)

**Example (access_modifier_strategy="preserve")**:
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

// After (reorder within each section)
class Data {
public:
    int b;     // Reordered within public
    char a;
private:
    double d;  // Reordered within private
    char c;
};
```

**Example (access_modifier_strategy="split")**:
```cpp
// After (optimal order, add access modifiers per member)
class Data {
private:
    double d;  // 8 bytes (largest)
public:
    int b;     // 4 bytes
private:
    char c;    // 1 byte
public:
    char a;    // 1 byte
};
// More verbose but optimal padding
```

**Example (access_modifier_strategy="ignore")**:
```cpp
// After (optimal order, all in one section - breaks encapsulation!)
class Data {
public:
    double d;  // Moved from private
    int b;
    char c;    // Moved from private
    char a;
};
```

**Priority**: P0 (Must Have)

#### FR-1.1.3: Source Code Transformation
**Description**: The system shall modify source code to apply optimizations.

**Acceptance Criteria**:
- Reorder member declarations in struct definition
- **Reorder constructor initializer lists to match new member order** (CRITICAL)
  - Members initialize in declaration order, not initializer list order
  - Initializer list must match declaration order to avoid -Wreorder warnings
  - Required for compilation with -Werror
- **Detect member dependencies in constructors** (CRITICAL)
  - If member A initialization uses member B, they have dependency
  - Example: `buffer(new char[size])` depends on `size`
  - Cannot reorder if dependencies would be violated
  - May need to skip optimization or mark members as locked
- Reorder aggregate initializations `{...}` to match (CRITICAL)
  - Aggregate init order must match declaration order
  - Compilation error if mismatched
- Reorder smart pointer arguments to match
  - `make_unique<Data>(a, b)` arguments must match constructor signature
  - Constructor signature does NOT change (would break all call sites)
- Preserve formatting, comments, and whitespace (when using srcML)
- Generate valid C++ code (syntax check)

**Critical Notes**:
- Constructor signature (parameter order) NEVER changes
- Only initializer list order changes to match new member declaration order
- Member dependencies must be detected and respected
- Violating initialization order causes undefined behavior

**Priority**: P0 (Must Have - Required for correct, compilable code)

**Test**: test_e2e_transformation_family.py (8 tests)

#### FR-1.1.5: Constructor Dependency Detection
**Description**: The system shall detect and respect member dependencies in constructor initializer lists.

**Rationale**:
- Member initialization may depend on other members
- Example: `buffer(new char[size])` depends on `size` being initialized first
- Violating dependency order causes undefined behavior
- Some optimizations may be impossible due to dependencies

**Acceptance Criteria**:
- Parse constructor initializer lists
- Detect if member A initialization references member B
- Build dependency graph for members
- Respect dependencies when reordering
- Skip optimization if dependencies prevent reordering
- Report skipped structs with reason "constructor dependencies"

**Example**:
```cpp
struct Data {
    int size;
    char* buffer;
    Data(int s) : size(s), buffer(new char[size]) {}  // buffer depends on size
};
// Cannot reorder to {buffer, size} - would break initialization
// Must skip optimization or keep size before buffer
```

**Detection Strategy**:
- Parse initializer list expressions
- Find member references in each initialization
- Build dependency graph
- Check if reordering would violate dependencies

**Priority**: P0 (Must Have - Prevents undefined behavior)

**Test**: test_e2e_constructor_dependencies.py (to be created)

#### FR-1.1.4: Dependency-Aware Optimization
**Description**: The system shall optimize structs in dependency order.

**Acceptance Criteria**:
- Build dependency graph (which structs contain other structs)
- Topological sort (leaves before parents)
- Iterative analysis (use optimized sizes of dependencies)
- Update global type table as optimization proceeds
- Handle shared dependencies (struct used by multiple parents)

**Priority**: P0 (Must Have)

---

### 1.2 User Control & Directives

#### FR-1.2.1: Opt-Out Markers (Struct-Level)
**Description**: Users shall be able to exclude specific structs from optimization.

**Syntax**:
```cpp
// paddington-ignore
struct DontTouch {
    char a;
    int b;
};
```

**Acceptance Criteria**:
- Detect `paddington-ignore` comment before struct definition
- Skip struct entirely (no analysis, no optimization)
- Report skipped struct with reason
- Support both `//` and `/* */` comment styles

**Priority**: P0 (Must Have)

#### FR-1.2.2: Opt-Out Markers (Member-Level)
**Description**: Users shall be able to lock specific members in place.

**Syntax**:
```cpp
struct Partial {
    int a;           // Can be reordered
    // paddington-lock
    char b;          // Must stay in this position
    // paddington-unlock
    double c;        // Can be reordered
};
```

**Acceptance Criteria**:
- Detect `paddington-lock` / `paddington-unlock` comments
- Treat locked members as fixed anchors
- Only reorder unlocked members around locked ones
- Report partial optimization with locked member count

**Priority**: P1 (Should Have)

#### FR-1.2.3: Opt-Out Markers (Region-Level)
**Description**: Users shall be able to disable optimization for code regions.

**Syntax**:
```cpp
// paddington-off
struct A { ... };  // Ignored
struct B { ... };  // Ignored
// paddington-on
struct C { ... };  // Analyzed
```

**Acceptance Criteria**:
- Detect `paddington-off` / `paddington-on` comments
- Skip all structs between markers
- Support nested regions (inner off/on overrides outer)
- Report skipped region with struct count

**Priority**: P2 (Nice to Have)

#### FR-1.2.4: Minimum Savings Threshold
**Description**: Users shall be able to set minimum padding savings to optimize.

**Syntax**:
```bash
paddington optimize --min-savings 8  # Only optimize if saves ≥8 bytes
```

**Acceptance Criteria**:
- Accept `--min-savings N` flag
- Skip structs with padding < N bytes
- Report skipped structs with actual padding
- Default: 0 (optimize any padding)

**Priority**: P1 (Should Have)

---

### 1.3 Output Modes

#### FR-1.3.2: Dry-Run Mode (Default)
**Description**: The system shall preview changes without applying them by default.

**Acceptance Criteria**:
- `optimize` command runs in dry-run mode by default (safe, no changes)
- Show what would be changed
- Show before/after for each struct
- Show files that would be modified
- No file modifications
- To apply changes: use `optimize --apply`

**Note**: Analysis functionality is now `optimize --dry-run` (default behavior)

**Priority**: P0 (Must Have)

#### FR-1.3.3: Direct Modification Mode
**Description**: The system shall directly modify source files when --apply flag is used.

**Acceptance Criteria**:
- Overwrite source files with optimized versions
- Create backup files (`.backup` extension)
- Report modified files
- Support rollback (restore from backup)
- Requires explicit `--apply` flag

**Priority**: P0 (Must Have)

#### FR-1.3.4: Patch Generation Mode
**Description**: The system shall generate git patches for review.

**Acceptance Criteria**:
- Generate one patch per struct (or per file)
- Generate commit message for each patch
- Generate `APPLY_ORDER.txt` with application order
- Patches are reviewable diffs
- Patches are independently applicable

**Priority**: P0 (Must Have)

---

### 1.4 Filtering & Selection

#### FR-1.4.1: File Pattern Filtering
**Description**: Users shall be able to filter which files to process.

**Syntax**:
```bash
paddington optimize build/ --include "*/core/*.o" --exclude "*/test/*.o"
```

**Acceptance Criteria**:
- Support glob patterns for include/exclude
- Multiple include/exclude patterns allowed
- Exclude takes precedence over include
- Report filtered file count

**Priority**: P0 (Must Have)

#### FR-1.4.2: Struct Name Filtering
**Description**: Users shall be able to filter which structs to optimize.

**Syntax**:
```bash
paddington optimize build/ --struct "UserData" --struct "Config*"
```

**Acceptance Criteria**:
- Support exact struct names
- Support wildcard patterns
- Multiple struct filters allowed
- Report filtered struct count

**Priority**: P1 (Should Have)

---

### 1.5 Template Handling

#### FR-1.7: Template Handling
**Description**: The system shall handle C++ templates appropriately.

**Acceptance Criteria**:
- Optimize template instantiations (concrete types)
- Skip template definitions (generic templates)
- Detect template instantiations in DWARF debug info
- Report template instantiations separately from definitions
- Handle template specializations as concrete types

**Priority**: P0 (Must Have)

---

### 1.6 Preprocessor Handling

#### FR-1.8: Preprocessor Handling
**Description**: The system shall handle preprocessor directives safely.

**Acceptance Criteria**:
- Skip structs containing `#ifdef`, `#ifndef`, `#if` directives
- Skip structs containing macro definitions
- Detect preprocessor usage in struct definitions
- Report skipped structs with preprocessor reason
- Preserve preprocessor directives in output

**Priority**: P0 (Must Have)

---

### 1.7 Complex C++ Features

#### FR-1.9: Complex C++ Features
**Description**: The system shall handle complex C++ features appropriately.

**Acceptance Criteria**:
- Handle inheritance (optimize derived classes considering base class layout)
- Skip structs with bitfields (bit-level packing)
- Skip structs with unions (overlapping memory layout)
- Skip structs with virtual tables (vtables)
- Report skipped structs with complexity reason
- Detect virtual functions and virtual inheritance

**Priority**: P0 (Must Have)

---

### 1.8 Validation & Verification

#### FR-1.8.1: Build Verification
**Description**: The system shall optionally verify changes compile.

**Syntax**:
```bash
paddington optimize build/ --verify --build-cmd "make test"
```

**Acceptance Criteria**:
- Run build command after each optimization
- Stop on first build failure
- Report which optimization broke the build
- Rollback failed optimization

**Priority**: P1 (Should Have)

#### FR-1.8.2: Syntax Validation
**Description**: The system shall validate transformed code is valid C++.

**Acceptance Criteria**:
- Check for syntax errors after transformation
- Report invalid transformations
- Skip invalid transformations
- Continue with valid transformations

**Priority**: P0 (Must Have)

---

### 1.9 Reporting & Observability

#### FR-1.9.1: Progress Reporting
**Description**: The system shall report progress for long operations.

**Acceptance Criteria**:
- Show progress bar for extraction (N/M files)
- Show progress bar for transformation (N/M structs)
- Show current operation (e.g., "Analyzing UserData...")
- Show elapsed time

**Priority**: P1 (Should Have)

#### FR-1.9.2: Summary Statistics
**Description**: The system shall report summary statistics at end.

**Acceptance Criteria**:
- Total structs analyzed
- Total structs optimized
- Total structs skipped (with breakdown by reason)
- Total padding eliminated (bytes)
- Total files modified
- Estimated memory savings (if instance count known)

**Priority**: P0 (Must Have)

#### FR-1.9.3: Verbosity Levels
**Description**: The system shall support multiple verbosity levels.

**Levels**:
- `-v`: WARNING (errors and warnings only)
- `-vv`: INFO (high-level progress)
- `-vvv`: DEBUG (detailed operations)
- `-vvvv`: TRACE (everything)

**Acceptance Criteria**:
- Each level includes all previous levels
- Default: INFO
- Logs are structured (timestamp, level, message)
- Logs are colorized (optional)

**Priority**: P0 (Must Have)

#### FR-1.9.4: Configuration Logging
**Description**: The system shall log the final configuration values used.

**Acceptance Criteria**:
- Log at INFO level at startup
- Show configuration source (default/preset/cli)
- Show final merged values
- Redact sensitive values (if any)

**Example Output**:
```
[INFO] Configuration loaded:
[INFO]   optimization.min_savings: 16 (cli override)
[INFO]   optimization.respect_access_modifiers: true (preset)
[INFO]   extraction.provider: pahole (preset)
[INFO]   transformation.provider: srcml (default)
[INFO]   reporting.verbosity: INFO (default)
```

**Priority**: P0 (Must Have)

#### FR-1.9.5: Skip Reason Reporting
**Description**: The system shall report why structs were skipped.

**Skip Reasons**:
- No padding (already optimal)
- Below minimum savings threshold
- Contains zero-size members (opaque types)
- Marked with `paddington-ignore`
- Contains preprocessor directives (#ifdef, #ifndef, #if)
- Contains macro definitions
- Template definition (not instantiation)
- Contains bitfields
- Contains unions
- Contains virtual tables (vtables)
- Has virtual functions or virtual inheritance
- No source location in DWARF
- Source file not found
- Member declarations not found in source
- Circular dependency detected

**Acceptance Criteria**:
- Each skipped struct has a reason
- Reasons are human-readable
- Reasons are grouped in summary
- Reasons include context (e.g., which member is zero-size)

**Priority**: P0 (Must Have)

---

## 2. Non-Functional Requirements

### 2.1 Performance

#### NFR-2.1.1: Extraction Speed
**Description**: The system shall extract struct info efficiently.

**Acceptance Criteria**:
- Process 1,000 object files in <10 minutes (with pahole)
- Process 1,000 object files in <2 hours (with pyelftools)
- Support caching to avoid re-extraction
- Support deduplication to skip identical files

**Priority**: P0 (Must Have)

#### NFR-2.1.2: Transformation Speed
**Description**: The system shall transform source code efficiently.

**Acceptance Criteria**:
- Transform 100 structs in <5 minutes (with srcML)
- Transform 100 structs in <1 minute (with line-swap)
- Support parallel transformation of independent files

**Priority**: P1 (Should Have)

---

### 2.2 Testability

#### NFR-2.2.1: Unit Test Coverage
**Description**: The system shall have comprehensive unit tests.

**Acceptance Criteria**:
- >90% code coverage for domain logic (struct_data, padding_analysis)
- >80% code coverage for pipeline stages
- >70% code coverage for providers
- All unit tests run in <5 minutes
- Unit tests use mocks (no I/O)
- All unit tests marked with `@pytest.mark.unit`

**Priority**: P0 (Must Have)

#### NFR-2.2.2: Integration Test Coverage
**Description**: The system shall have integration tests for real scenarios.

**Acceptance Criteria**:
- Test each provider with real tools (pahole, srcML, git)
- Test end-to-end workflows
- Test error handling and edge cases
- Integration tests run in <30 minutes
- All integration tests marked with `@pytest.mark.integration`

**Priority**: P0 (Must Have)

#### NFR-2.2.3: Test Organization
**Description**: The system shall have clear test organization.

**Acceptance Criteria**:
- Test directory structure mirrors `implementation/` structure
- One test file per implementation file: `implementation/X/Y.py` → `tests/X/test_Y.py`
- Each test file contains both unit and integration tests
- All tests explicitly marked with type: `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.e2e`
- Can run tests selectively: `pytest -m unit`, `pytest -m integration`, `pytest -m e2e`
- Pytest configuration enforces markers

**Example**:
```
implementation/pipeline/extraction/pahole.py
tests/pipeline/extraction/test_pahole.py  # Contains unit + integration tests
```

**Priority**: P0 (Must Have)

---

### 2.3 Maintainability

#### NFR-2.3.1: Code Organization
**Description**: The system shall have clear code organization.

**Acceptance Criteria**:
- Directory structure reflects intent
- Each module has single responsibility
- No circular dependencies
- Clear separation of concerns (domain, pipeline, providers)

**Priority**: P0 (Must Have)

#### NFR-2.3.2: Documentation
**Description**: The system shall be well-documented.

**Acceptance Criteria**:
- README for users
- DESIGN for developers
- KEY_INSIGHTS for decision-making
- PIPELINE_STAGES_EXPLAINED for understanding
- Docstrings for all public APIs
- Examples for common use cases

**Priority**: P0 (Must Have)

---

### 2.4 Flexibility

#### NFR-2.4.1: Provider Swappability
**Description**: The system shall support swapping implementations.

**Acceptance Criteria**:
- Extraction: pahole, pyelftools, custom
- Transformation: srcML, line-swap, custom
- Application: file-writer, patch-generator, custom
- Providers selected via config or CLI flags
- Adding new provider requires no changes to pipeline

**Priority**: P0 (Must Have)

#### NFR-2.4.2: Configuration
**Description**: The system shall be configurable via CLI flags.

**Acceptance Criteria**:
- All options available via CLI flags
- Sensible defaults for zero-config usage
- All options documented in `--help`

**Future Enhancement (P2)**:
- Support `paddington.toml` preset file
- Configuration priority: default < preset < cli
- Log final configuration values

**Priority**: P0 (Must Have for CLI, P2 for preset file)

---

### 2.5 Reliability

#### NFR-2.5.1: Error Handling
**Description**: The system shall handle errors gracefully.

**Acceptance Criteria**:
- Validate inputs at every stage
- Fail fast with clear error messages
- Provide context for debugging (file, line, struct)
- Continue processing after non-fatal errors
- Report all errors in summary

**Priority**: P0 (Must Have)

#### NFR-2.5.2: Atomicity
**Description**: The system shall apply changes atomically.

**Acceptance Criteria**:
- All modifications to a file succeed or none do
- Backup files created before modification
- Rollback on failure
- No partial modifications

**Priority**: P0 (Must Have)

---

## 3. Data Requirements

### 3.1 Input Data

#### DR-3.1.1: Object Files
**Description**: Compiled object files with DWARF debug info.

**Format**: ELF object files (`.o`) compiled with `-g` flag

**Required Information**:
- Struct/class names
- Member names, types, sizes, offsets
- Source file locations (file path, line number)

**Priority**: P0 (Must Have)

#### DR-3.1.2: Source Files
**Description**: C++ source files to be modified.

**Format**: `.cpp`, `.h`, `.hpp`, `.cc`, `.cxx` files

**Required Information**:
- Struct/class definitions
- Constructor definitions
- Aggregate initializations
- Smart pointer instantiations

**Priority**: P0 (Must Have)

---

### 3.2 Output Data

#### DR-3.2.1: Analysis Report
**Description**: Human-readable report of padding analysis.

**Format**: Text output to stdout

**Contents**:
- List of structs with padding
- Padding breakdown per struct
- Potential savings per struct
- Total potential savings
- Skipped structs with reasons

**Priority**: P0 (Must Have)

#### DR-3.2.2: Modified Source Files
**Description**: Optimized source code.

**Format**: Same as input (`.cpp`, `.h`, etc.)

**Contents**:
- Reordered struct members
- Reordered constructor initializer lists
- Reordered aggregate initializations
- Preserved formatting (with srcML)

**Priority**: P0 (Must Have)

#### DR-3.2.3: Git Patches
**Description**: Reviewable diffs for each optimization.

**Format**: Git unified diff format

**Contents**:
- One patch per struct (or per file)
- Commit message with optimization details
- `APPLY_ORDER.txt` with application order

**Priority**: P0 (Must Have)

---

## 4. Constraints

### 4.1 Technical Constraints

#### C-4.1.1: C++ Language Support
**Description**: The system shall support C++11 and later.

**Rationale**: Modern C++ features (auto, smart pointers, etc.)

**Priority**: P0 (Must Have)

#### C-4.1.2: Platform Support
**Description**: The system shall support Linux and macOS.

**Rationale**: Primary development platforms

**Priority**: P0 (Must Have)

#### C-4.1.3: Python Version
**Description**: The system shall require Python 3.8+.

**Rationale**: Modern Python features (dataclasses, type hints, etc.)

**Priority**: P0 (Must Have)

---

### 4.2 Design Constraints

#### C-4.2.1: No Constructor Signature Changes
**Description**: The system shall NOT change constructor parameter order.

**Rationale**: 
- Changing parameter order breaks all call sites
- Example: `Data(char a, int b)` → `Data(int b, char a)` breaks `Data('x', 42)`
- Would require updating every instantiation in codebase
- Too risky and invasive

**What DOES change**:
- Constructor initializer list order (to match new member declaration order)
- Example: `Data(char a, int b) : a(a), b(b) {}` → `Data(char a, int b) : b(b), a(a) {}`
- Parameters stay same, only initialization order changes

**Priority**: P0 (Must Have - Critical constraint)

#### C-4.2.2: Preserve Semantics
**Description**: The system shall NOT change program behavior.

**Rationale**: Optimization should be transparent

**Specific Guarantees**:
- No change to member types or names
- No change to member values or initialization
- No change to constructor signatures (parameter order)
- **No change to access modifiers** (public/private/protected sections)
  - Exception: If `respect_access_modifiers=false` in config
- No change to method definitions
- No change to inheritance relationships

**Priority**: P0 (Must Have)

#### C-4.2.3: Immutable Domain Models
**Description**: Domain models shall be immutable.

**Rationale**: Easier to test, easier to reason about

**Priority**: P0 (Must Have)

---

## 5. Use Cases

### UC-5.1: Analyze Codebase for Padding Waste

**Actor**: Developer

**Preconditions**: 
- Project compiled with `-g` flag
- Object files exist in build directory

**Main Flow**:
1. Developer runs `paddington optimize build/` (dry-run by default)
2. System extracts struct info from object files
3. System calculates padding for each struct
4. System reports structs with padding waste
5. System reports total potential savings

**Postconditions**: 
- No files modified (dry-run mode)
- Developer knows which structs have padding

**Note**: The `analyze` command has been removed. Analysis functionality is now the default behavior of `optimize` (dry-run mode).

**Priority**: P0

---

### UC-5.2: Optimize Single Struct

**Actor**: Developer

**Preconditions**:
- Struct has padding waste
- Source file is writable

**Main Flow**:
1. Developer runs `paddington optimize build/ --struct UserData --apply`
2. System analyzes UserData
3. System creates optimization plan
4. System transforms source code
5. System writes modified file
6. System reports success

**Postconditions**:
- UserData is optimized
- Source file is modified
- Backup file created

**Priority**: P0

---

### UC-5.3: Generate Patches for Review

**Actor**: Developer

**Preconditions**:
- Multiple structs have padding waste
- Team uses code review process

**Main Flow**:
1. Developer runs `paddington optimize build/ --patch-dir patches/`
2. System analyzes all structs
3. System creates optimization plans
4. System generates patches
5. System writes patches to directory
6. Developer reviews patches
7. Developer applies patches incrementally

**Postconditions**:
- Patches generated
- No files modified yet
- Patches are reviewable

**Priority**: P0

---

### UC-5.4: Exclude Specific Structs

**Actor**: Developer

**Preconditions**:
- Some structs should not be optimized (ABI requirements)

**Main Flow**:
1. Developer adds `// paddington-ignore` comment
2. Developer runs `paddington optimize build/ --apply`
3. System skips marked structs
4. System optimizes unmarked structs
5. System reports skipped structs

**Postconditions**:
- Marked structs unchanged
- Unmarked structs optimized

**Priority**: P0

---

### UC-5.5: Verify Changes Compile

**Actor**: Developer

**Preconditions**:
- Build system is configured
- Build command is known

**Main Flow**:
1. Developer runs `paddington optimize build/ --apply --verify --build-cmd "make test"`
2. System optimizes first struct
3. System runs build command
4. Build succeeds
5. System continues with next struct
6. (If build fails, system rolls back and reports error)

**Postconditions**:
- All optimizations compile successfully
- Or failed optimization is rolled back

**Priority**: P1

---

## 6. Architecture Implications

Based on these requirements, the architecture must support:

### 6.1 Data Model Extensions

```python
@dataclass(frozen=True)
class MemberInfo:
    name: str
    type: str
    size: int                          # Original size from DWARF
    optimized_size: Optional[int]      # Size after optimization (NEW)
    offset: int
    access_modifier: str               # "public", "private", "protected", "none" (NEW)
    locked: bool = False               # User locked this member (NEW)

@dataclass(frozen=True)
class StructInfo:
    name: str
    size: int                          # Original size
    optimized_size: Optional[int]      # Size after optimization (NEW)
    members: Tuple[MemberInfo, ...]
    file_path: Optional[str] = None
    line: Optional[int] = None
    ignore: bool = False               # User marked ignore (NEW)
    ignore_reason: Optional[str] = None  # Why ignored (NEW)
```

### 6.2 Stage 2 Extensions

Analysis stage must:
- Parse source files for directives (`paddington-ignore`, `paddington-lock`)
- Mark structs/members as locked
- Skip locked structs entirely
- Partially optimize structs with locked members
- Track original and optimized sizes separately

### 6.3 New Module: Directive Parser

```python
# domain/directive_parser.py
class DirectiveParser:
    def parse_file(self, file_path: str) -> Dict[str, DirectiveInfo]:
        """Parse paddington directives from source file."""
        pass
    
    def is_struct_ignored(self, struct_name: str) -> bool:
        """Check if struct has paddington-ignore."""
        pass
    
    def get_locked_members(self, struct_name: str) -> Set[str]:
        """Get list of locked member names."""
        pass
```

### 6.4 Configuration (CLI-First, Preset File is P2)

**Current (P0)**: CLI flags only
```bash
# Default behavior: dry-run (safe, no changes)
paddington optimize build/

# Apply changes (requires explicit flag)
paddington optimize build/ --apply \
  --min-savings 8 \
  --access-modifier-strategy preserve \
  --extractor pahole \
  --transformer srcml \
  --applicator patch \
  --include "*/src/*.o" \
  --exclude "*/test/*.o" \
  -vv
```

**Future (P2)**: Optional preset file support
```toml
# paddington.toml (optional, P2 feature)
[optimization]
min_savings = 8
access_modifier_strategy = "preserve"
```

### 6.5 Directory Structure

```
paddington/
├── __main__.py                    # Entry point
├── README.md                      # Documentation
├── REQUIREMENTS.md
├── DESIGN.md
│
├── implementation/                # All implementation code
│   ├── user_interactions/         # User-facing operations
│   │   ├── analyze.py
│   │   └── optimize.py
│   │
│   ├── struct_data/               # Data structures
│   │   ├── struct_info.py
│   │   ├── member_info.py
│   │   └── ...
│   │
│   ├── padding_analysis/          # Business logic
│   │   ├── padding_calculator.py
│   │   ├── member_reorderer.py
│   │   └── ...
│   │
│   ├── pipeline/                  # Pipeline stages + providers
│   │   ├── extraction/
│   │   │   ├── stage.py
│   │   │   ├── base.py
│   │   │   ├── pahole.py
│   │   │   └── dwarf.py
│   │   ├── transformation/
│   │   │   ├── stage.py
│   │   │   ├── srcml.py
│   │   │   └── line_swap.py
│   │   └── output/
│   │       ├── stage.py
│   │       ├── file_writer.py
│   │       └── patch_generator.py
│   │
│   └── utils/
│       ├── logger.py
│       └── file_filter.py
│
└── tests/                         # All tests (mirrors implementation/)
    ├── pytest.ini                 # Pytest configuration
    ├── conftest.py                # Shared fixtures
    │
    ├── user_interactions/
    │   ├── test_analyze.py        # Unit + integration tests
    │   └── test_optimize.py
    │
    ├── struct_data/
    │   └── test_struct_info.py
    │
    ├── padding_analysis/
    │   └── test_padding_calculator.py
    │
    ├── pipeline/
    │   ├── extraction/
    │   │   └── test_pahole.py     # Unit + integration tests
    │   ├── transformation/
    │   │   └── test_srcml.py      # Unit + integration tests
    │   └── output/
    │       └── test_file_writer.py
    │
    ├── end_to_end/
    │   └── test_optimize_workflow.py
    │
    └── fixtures/
        ├── object_files/
        └── source_files/
```

**Key Principles**:
- Clean top level (main, docs, implementation, tests)
- `implementation/` contains all code
- `tests/` mirrors `implementation/` structure exactly
- Providers co-located with their stages
- One test file per implementation file

### 6.6 Test Organization

**Structure**: Tests mirror implementation exactly
```
implementation/pipeline/extraction/pahole.py
tests/pipeline/extraction/test_pahole.py
```

**Markers**: All tests must be explicitly marked
```python
@pytest.mark.unit          # Fast, no I/O, use mocks
@pytest.mark.integration   # Slow, with I/O, use real tools
@pytest.mark.e2e           # Slowest, full workflows
```

**Pytest Configuration**:
```ini
# tests/pytest.ini
[pytest]
markers =
    unit: marks tests as unit tests (fast, no I/O, use mocks)
    integration: marks tests as integration tests (slow, with I/O)
    e2e: marks tests as end-to-end tests (slowest, full workflows)

addopts = 
    --strict-markers
```

**Running Tests**:
```bash
pytest -m unit          # Only unit tests (fast, <5 min)
pytest -m integration   # Only integration tests (<30 min)
pytest -m e2e           # Only end-to-end tests
pytest tests/           # All tests
```

---
access_modifier_strategy = "preserve"  # "preserve", "split", or "ignore"
```

---

## 7. Open Questions

1. **Q**: Should we support custom directive markers?  
   **A**: No, not initially. Standard markers are sufficient.  
   **Rationale**: 
   - Adds complexity (parsing, validation, documentation)
   - No clear use case (when would you need custom markers?)
   - Can be added later if users request it (P2 feature)
   - Standard markers are clear and consistent across projects

2. **Q**: Should locked members affect alignment calculations?  
   **A**: Yes, treat them as fixed anchors.

3. **Q**: Should we support per-file configuration?  
   **A**: P2 (Nice to Have), use global config for now.

4. **Q**: Should we support optimization profiles (aggressive, conservative)?  
   **A**: P2 (Nice to Have), use flags for now.

5. **Q**: Should we track instance counts for savings estimation?  
   **A**: P2 (Nice to Have), requires static analysis.

---

## 8. Priority Summary

**P0 (Must Have)**: 
- Core functionality (detection, reordering, transformation)
- Dependency-aware optimization
- Struct-level opt-out markers
- All output modes (analyze, dry-run, modify, patch)
- File filtering
- Validation and error handling
- Summary reporting
- Provider swappability
- Unit and integration tests

**P1 (Should Have)**:
- Member-level opt-out markers
- Minimum savings threshold
- Struct name filtering
- Build verification
- Progress reporting
- Configuration file support

**P2 (Nice to Have)**:
- Region-level opt-out markers
- Custom directive markers
- Per-file configuration
- Optimization profiles
- Instance count tracking

---

## 9. Success Criteria

The system is successful if:
1. ✅ Correctly identifies padding waste in real codebases
2. ✅ Optimizes structs without breaking compilation
3. ✅ Respects user directives (ignore, lock)
4. ✅ Handles nested structs correctly (dependency order)
5. ✅ Generates reviewable patches
6. ✅ Provides clear error messages
7. ✅ Runs efficiently on large codebases (1000+ files)
8. ✅ Is easy to test (mocks, unit tests)
9. ✅ Is easy to extend (new providers)
10. ✅ Is well-documented

---

## 10. Next Steps

1. Review and approve this requirements document
2. Update architecture based on new requirements
3. Update agent tasks based on new requirements
4. Begin implementation with Phase 1 (Foundation)
