# paddingTON

**padding Trimming Optimization eNgine**

A C++ refactoring tool that detects and eliminates redundant padding in structs/classes by reordering members from largest to smallest, while automatically updating constructors and all call sites.

## Features

- 🔍 **Analysis** - Detect padding waste in structs/classes
- ⚡ **Optimization** - Reorder members to minimize padding
- 🔄 **Smart Updates** - Automatically update constructors and initializations
- 🌳 **Dependency-Aware** - Bottom-up optimization for nested structs
- 🎯 **Safe by Default** - Dry-run mode, build verification, validation
- 📦 **Patch Generation** - Generate reviewable git patches
- 🎨 **Template Support** - Handle template definitions
- 🧬 **Inheritance Support** - Preserve base class relationships

## Installation

```bash
# Clone repository
git clone https://github.com/LightShield/paddington.git
cd paddington

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## Quick Start

### Analyze

Find structs with padding waste:

```bash
python -m paddington analyze src/
```

Output:
```
[PADDING] struct UserData: 24 bytes (10 bytes padding, 8 bytes savable)

Total: 1 struct(s)/class(es) analyzed, 1 can be optimized
Total padding: 10 bytes
Potential savings: 8 bytes
```

### Optimize

Preview changes (dry-run):
```bash
python -m paddington optimize src/
```

Apply changes:
```bash
python -m paddington optimize src/ --apply
```

Generate patches for review:
```bash
python -m paddington optimize src/ --patch-dir patches/
```

## Usage

### Commands

#### analyze

Analyze C++ files for padding waste:

```bash
python -m paddington analyze <path> [options]
```

**Options:**
- `-v, -vv, -vvv` - Increase verbosity (WARNING/INFO/DEBUG)

**Examples:**
```bash
# Analyze single file
python -m paddington analyze src/user.cpp

# Analyze directory
python -m paddington analyze src/

# Verbose output
python -m paddington analyze src/ -vv
```

#### optimize

Optimize struct padding:

```bash
python -m paddington optimize <path> [options]
```

**Options:**
- `--apply` - Apply changes (default: dry-run)
- `--force` - Reorder even if no size savings
- `--patch-dir <dir>` - Generate git patches
- `--build-command <cmd>` - Verify build after each optimization
- `--update-signatures` - Update constructor signatures (future)
- `-v, -vv, -vvv` - Increase verbosity

**Examples:**
```bash
# Dry-run (preview changes)
python -m paddington optimize src/

# Apply changes
python -m paddington optimize src/ --apply

# Force reordering for consistency
python -m paddington optimize src/ --apply --force

# Generate patches
python -m paddington optimize src/ --patch-dir patches/

# Verify build after changes
python -m paddington optimize src/ --apply --build-command "make test"

# Combine options
python -m paddington optimize src/ --patch-dir patches/ --build-command "make" -vv
```

## How It Works

### Member Reordering

paddingTON reorders struct members from largest to smallest to minimize padding:

**Before:**
```cpp
struct UserData {
    char flag;        // 1 byte
    int id;           // 4 bytes (3 bytes padding before)
    char status;      // 1 byte
    double score;     // 8 bytes (7 bytes padding before)
};
// Total: 24 bytes (10 bytes padding)
```

**After:**
```cpp
struct UserData {
    double score;     // 8 bytes
    int id;           // 4 bytes
    char flag;        // 1 byte
    char status;      // 1 byte
};
// Total: 16 bytes (2 bytes padding at end)
// Saved: 8 bytes per instance
```

### What Gets Updated

1. **Struct/class member declarations** - Reordered by size
2. **Constructor initializer lists** - Reordered to match members
3. **Aggregate initializations** - Values reordered to match members
4. **Access specifiers** - Preserved (members grouped by access level)

### What Stays Unchanged

1. **Constructor signatures** - Parameter order unchanged (safe by default)
2. **Constructor bodies** - Assignment order doesn't matter
3. **Smart pointer calls** - Work with unchanged constructor signatures
4. **Comments** - Preserved as-is

### Dependency Handling

Nested structs are optimized bottom-up:

```cpp
struct Inner {
    char a;
    double b;
};

struct Outer {
    char x;
    Inner inner;  // Optimized first
    int y;
};
```

Optimization order: Inner → Outer (leaves first)

## Advanced Features

### Opt-Out

Skip specific structs with annotation:

```cpp
// paddington-ignore
struct DontTouch {
    char a;
    int b;  // Keep original order
};
```

### Templates

Templates require `--force` flag:

```bash
python -m paddington optimize src/ --apply --force
```

```cpp
template<typename T>
struct Container {
    int count;    // Known size first
    char flag;
    T value;      // Template param last
};
```

### Inheritance

Base class members are preserved, only derived class members reordered:

```cpp
struct Base {
    char a;
    int b;
};

struct Derived : Base {
    double d;     // Reordered
    int e;
    char c;
};
```

### Patch Generation

Generate reviewable patches:

```bash
python -m paddington optimize src/ --patch-dir patches/
```

Output:
```
patches/
├── APPLY_ORDER.txt
├── tree_000_01_Inner.patch
├── tree_000_01_Inner.msg
├── tree_000_02_Outer.patch
├── tree_000_02_Outer.msg
├── tree_001_01_Config.patch
└── tree_001_01_Config.msg
```

Apply patches:
```bash
cd patches/
git apply tree_000_01_Inner.patch
git commit -F tree_000_01_Inner.msg
```

### Build Verification

Verify changes don't break builds:

```bash
python -m paddington optimize src/ --apply --build-command "make test"
```

Stops on first build failure and reports error.

## Limitations

### Automatically Skipped

- Structs with `paddington-ignore` annotation
- Structs with preprocessor directives (`#ifdef`, `#ifndef`)
- Structs with circular dependencies
- Forward declarations (not definitions)

### Not Yet Supported

- Constructor signature reordering (use `--update-signatures` when available)
- Cross-file optimization (header + implementation)
- Bitfields
- Unions
- Anonymous structs

## Dependencies

- Python 3.7+
- libclang (Python bindings)
- [logger_python](https://github.com/LightShield/logger_python) - Structured logging
- git (for patch generation)

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linter
ruff check paddington

# Run formatter
black paddington

# Run type checker
mypy paddington --ignore-missing-imports
```

## Design

See [DESIGN.md](DESIGN.md) for detailed design documentation.

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## Troubleshooting

### "Path does not exist"
Ensure the path is correct and accessible.

### "No C++ files found"
Check that directory contains .cpp, .h, or similar files.

### "Not in a git repository"
For patch generation, initialize git: `git init`

### "Failed to import libclang"
Install libclang: `pip install libclang`

### Build verification fails
Check that build command works manually first.
