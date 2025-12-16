# paddingTON

**padding Trimming Optimization eNgine**

A C++ refactoring tool that detects and eliminates redundant padding in structs/classes by analyzing compiled object files and reordering members to minimize memory waste.

## Features

- 🔍 **Post-Build Analysis** - Extract struct layout from compiled `.o` files using DWARF debug info
- ⚡ **Accurate Type Resolution** - Compiler has already resolved all types, templates, and nested structs
- 🌳 **Dependency-Aware** - Bottom-up optimization for nested structs
- 🎯 **Deduplication** - Handles multiple object files without duplicate processing
- 🎨 **Template Support** - Each template instantiation optimized separately
- 📊 **Padding Calculation** - Precise padding detection using actual member offsets

## Requirements

- Object files compiled with debug info (`-g` flag)
- `dwarfdump` tool (available on macOS/Linux by default)
- Python 3.8+

## Installation

```bash
git clone <repo>
cd paddington
pip install -r requirements-dev.txt  # For development/testing
```

## Quick Start

### 1. Compile with Debug Info

```bash
# Add -g flag to your build
g++ -g -c myfile.cpp -o myfile.o
```

### 2. Analyze Padding

```bash
python -m paddington analyze build/*.o
```

Output:
```
Processing build/myfile.o...
  Found 3 structs

Simple (size=12 bytes):
  3 bytes padding after a
  3 bytes trailing padding
  Total padding: 6 bytes

After deduplication: 3 unique structs
```

### 3. Optimize (Coming Soon)

The optimization engine will use the extracted struct info to:
- Reorder members largest-to-smallest
- Update constructors and call sites
- Generate reviewable patches

## How It Works

1. **Extract**: Parse DWARF debug info from `.o` files
   - Struct/class names and sizes
   - Member names, types, sizes, and offsets
   
2. **Analyze**: Calculate padding waste
   - Internal padding between members
   - Trailing padding at end of struct
   
3. **Order**: Identify dependencies
   - Find leaf structs (only primitive types)
   - Build bottom-up ordering for nested structs
   - Track visited structs to prevent reoptimization

4. **Optimize**: Reorder members (TODO)
   - Sort by size descending
   - Update source code
   - Verify compilation

## Example

```cpp
// Before (12 bytes with 6 bytes padding)
struct Simple {
    char a;    // 1 byte
    // 3 bytes padding
    int b;     // 4 bytes
    char c;    // 1 byte
    // 3 bytes padding
};

// After (8 bytes with 2 bytes padding)
struct Simple {
    int b;     // 4 bytes
    char a;    // 1 byte
    char c;    // 1 byte
    // 2 bytes padding
};
```

## Development

Run tests:
```bash
pytest tests/
```

## Why DWARF Instead of Clang?

The original clang-based parser had type resolution issues. DWARF extraction provides:
- ✅ Accurate type sizes (compiler resolved everything)
- ✅ Actual struct layouts with padding
- ✅ Template instantiations as concrete types
- ✅ Works with any build system
- ✅ No dependency on libclang

## License

Internal Amazon tool
