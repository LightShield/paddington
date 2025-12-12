# paddingTON Design Document

**padding Trimming Optimization eNgine**

## Overview

A C++ refactoring tool that detects and eliminates redundant padding in structs/classes by reordering members from largest to smallest, while automatically updating constructors and all call sites.

## Name

**paddingTON** = **padding T**rimming **O**ptimization e**N**gine

Inspired by Paddington Bear, the tool tidies up your structs.

## Technology Stack

- **Parser:** libclang (Python bindings)
- **Language:** Python for rapid development
- **Analysis:** Uses Clang's AST and type information

### Why libclang?

- Full C++ parsing with proper AST
- Handles templates, macros, complex C++
- Can calculate actual struct layout and padding
- Compiler-agnostic: analyzes source code regardless of actual build compiler (GCC/MSVC/Clang)
- Provides `Type.get_size()`, `Type.get_align()`, `Cursor.get_offset()` for layout calculation
- Industry standard (clang-tidy, clang-format use it)

## Core Algorithm

### Bottom-Up Optimization

Structs/classes form a dependency tree where complex types contain simpler types. Optimization must proceed from leaves to root.

**Why bottom-up?**
```cpp
struct Inner {
    char a;    // 1 byte
    int b;     // 4 bytes
    // 3 bytes padding
};

struct Outer {
    char x;      // 1 byte
    Inner inner; // Size depends on Inner's optimization
    int y;       // 4 bytes
};
```

If `Outer` is optimized before `Inner`, calculations use unoptimized `Inner` size. After optimizing `Inner`, `Outer` may need re-optimization.

**Algorithm steps:**

1. **Build dependency graph:** For each struct/class, identify member types (native vs composite)
2. **Topological sort:** Order structs so leaves (only native types) come first
3. **Optimize bottom-up:**
   - Start with leaves
   - Calculate padding, reorder members (largest to smallest)
   - Update constructors to match new member order
   - Update all call sites (direct and indirect, including smart pointers)
   - Move up dependency tree using optimized sizes
4. **Verify:** Run build command after each struct optimization

### Edge Cases

- **Circular dependencies:** Pointers don't require full type optimization (forward declarations)
- **Templates:** Handle instantiations, may have different layouts per instantiation
- **Inheritance:** Base class layout affects derived class padding
- **Alignment requirements:** Respect platform-specific and explicit alignment

## Commands

### analyze

Analyzes codebase and reports potential optimizations without modifying files.

```bash
paddington analyze <path> [options]
```

**Output:**
- List of structs with padding waste
- Bytes saved per struct
- Total potential savings
- Dependency trees identified
- Skipped structs with reasons

### optimize

Performs actual refactoring with various output modes.

```bash
paddington optimize <path> [options]
```

## Configuration Options

### Output Modes

- `--dry-run`: Print report only, no modifications
- `--apply`: Modify source files in-place
- `--diff`: Generate unified diff output
- `--patch-dir <dir>`: Generate individual patch files per struct

### Optimization Granularity

Critical for reviewability and verification:

- `--mode single-struct`: One struct per commit/patch (finest granularity)
- `--mode dependency-tree`: One independent tree per commit/patch (recommended)
- `--mode depth-level`: All depth-N structs per commit/patch
- `--mode all`: Everything at once (not recommended for large codebases)

### Build Verification

- `--build-command <cmd>`: Run command after each change (e.g., "make test")
- `--verify`: Compile before/after, ensure no breakage

### Filtering

- `--include <pattern>`: Only process matching files/structs
- `--exclude <pattern>`: Skip matching files/structs

## Opt-Out Mechanism

Users can mark structs/members to skip optimization:

```cpp
// paddington-ignore
struct DontTouch {
    char a;
    int b;
};

// Granular control:
struct Partial {
    char a;
    int b;  // paddington-ignore: ABI compatibility required
    char c;
};
```

**Common reasons to ignore:**
- ABI compatibility requirements
- Serialization format dependencies
- Memory-mapped structures
- External API contracts

## Reporting

### Success Report
```
[OPTIMIZED] struct UserData: 24 bytes -> 16 bytes (8 bytes saved)
  - Reordered 5 members
  - Updated 3 constructors
  - Updated 12 call sites
```

### Skip Report
```
[SKIPPED] struct CircularRef: Circular dependency detected (A->B->A)
[SKIPPED] struct ExternABI: Marked with paddington-ignore (ABI compatibility)
[WARNING] struct TemplateInstantiation: Multiple instantiations with different layouts
```

## Incremental Optimization Strategy

**Key principle:** Each optimization step must leave code in a compilable, correct state.

1. Optimize one struct (leaf node)
2. Update all its constructors
3. Update all call sites (including indirect via smart pointers)
4. Run build verification
5. Generate commit/patch
6. Move to next struct

This approach:
- Produces reviewable changes
- Enables easy debugging
- Allows partial adoption
- Maintains bisectable history

## Change Management

### Git Integration

Each optimization unit (struct/tree/depth-level) generates:
- Individual patch file
- Suggested commit message following Conventional Commits

```bash
# Generate patches
paddington optimize src/ --mode dependency-tree --patch-dir patches/

# Apply incrementally
git apply patches/tree_001.patch
make test
git commit -am "refactor: Optimize padding for UserData dependency tree

Reorder members in UserData, UserProfile, UserSettings from largest
to smallest. Reduces memory footprint by 48 bytes per instance.

- UserData: 24->16 bytes (8 saved)
- UserProfile: 32->24 bytes (8 saved)  
- UserSettings: 64->32 bytes (32 saved)"
```

## Development Approach

### Test-Driven Development

Create `test_cases/` directory with mock examples:

```
test_cases/
  simple_struct/
    input.cpp
    expected.cpp
    build.sh
  nested_struct/
    input.cpp
    expected.cpp
    build.sh
  templates/
    input.cpp
    expected.cpp
    build.sh
```

Each test case:
1. Has input C++ code with padding issues
2. Has expected output after optimization
3. Has build script to verify compilation
4. Tests specific edge cases

### Verification Strategy

For each optimization:
1. Parse input with libclang
2. Calculate padding
3. Generate optimized output
4. Compare with expected output
5. Run build command
6. Verify compilation succeeds

## Implementation Phases

### Phase 1: Analysis Only
- Parse C++ files with libclang
- Build dependency graph
- Calculate padding for each struct
- Generate report (no modifications)

### Phase 2: Simple Optimization
- Optimize leaf structs (only native types)
- Update constructors
- Update direct call sites
- Generate patches

### Phase 3: Complex Optimization
- Handle nested structs (bottom-up)
- Handle templates
- Handle inheritance
- Handle indirect call sites (smart pointers)

### Phase 4: Production Ready
- Comprehensive error handling
- Performance optimization
- Documentation
- CI/CD integration

## Open Questions

1. How to handle platform-specific alignment differences?
2. Should we support custom alignment attributes (`alignas`)?
3. How to detect ABI boundaries automatically?
4. Should we generate before/after memory layout visualizations?
5. Integration with existing refactoring tools (clang-tidy)?

## Future Enhancements

- IDE integration (VS Code extension)
- CI/CD checks (fail if padding waste exceeds threshold)
- Memory layout visualization
- Performance impact estimation
- Support for C structs (not just C++)
