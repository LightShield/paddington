# Compilation Database Guide

## What is compile_commands.json?

A JSON file that describes exactly how each source file in your project is compiled. It contains:
- Which files are compiled
- What compiler flags are used
- Where include directories are located
- What preprocessor defines are active

## Why Use It?

**Without compilation database:**
- paddingTON guesses include paths
- May fail to parse headers
- Doesn't know about preprocessor defines
- Can't verify compilation

**With compilation database:**
- Uses exact build configuration
- Parses files correctly with all includes
- Respects preprocessor state
- Can verify each file compiles after optimization

## Format

```json
[
  {
    "directory": "/path/to/project",
    "command": "clang++ -std=c++17 -Iinclude -DDEBUG -c src/main.cpp -o main.o",
    "file": "src/main.cpp"
  }
]
```

**Fields:**
- `directory`: Working directory for the command
- `command`: Full compilation command (string)
- `arguments`: Alternative to command (array of strings)
- `file`: Source file being compiled

## How to Generate

### CMake

Add to your CMakeLists.txt or command line:

```bash
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON .
```

Or in CMakeLists.txt:
```cmake
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```

This creates `compile_commands.json` in your build directory.

### Make

Use [Bear](https://github.com/rizsotto/Bear) to intercept make commands:

```bash
# Install Bear
# macOS: brew install bear
# Linux: apt-get install bear

# Generate compilation database
bear -- make

# Or for clean build
bear -- make clean all
```

### Ninja

Ninja has built-in support:

```bash
ninja -t compdb > compile_commands.json
```

### Other Build Systems

**Bazel:**
```bash
# Use bazel-compilation-database
# https://github.com/grailbio/bazel-compilation-database
```

**SCons:**
```bash
# Use compilation_db tool
scons --compilation-db=compile_commands.json
```

**Manual:**
For simple projects, you can write it manually:
```json
[
  {
    "directory": "/path/to/project",
    "command": "g++ -std=c++17 -Iinclude -c src/file.cpp",
    "file": "src/file.cpp"
  }
]
```

## Using with paddingTON

Once you have `compile_commands.json`:

```bash
# Analyze (auto-detects compilation database)
paddington analyze .

# Optimize with verification
paddington optimize . --apply --verify

# With filtering
paddington optimize . --apply --verify --exclude '*/third_party/*'
```

paddingTON will:
1. Find `compile_commands.json` (searches up to 5 parent directories)
2. Extract file list
3. Use compile flags for accurate parsing
4. Use compile commands for verification (with --verify)

## What paddingTON Extracts

From each compilation entry:

**For parsing:**
- `-std=c++XX` - C++ standard
- `-I<path>` - Include directories (resolved to absolute paths)
- `-D<define>` - Preprocessor defines
- `-isystem <path>` - System include paths

**For verification:**
- Full compile command (with --verify flag)

**Ignored:**
- `-O2`, `-g` - Optimization/debug flags
- `-o <output>` - Output file
- `-c` - Compile-only flag
- Linker flags

## Troubleshooting

### compile_commands.json not found

Make sure it's in your project root or a parent directory. paddingTON searches up to 5 levels.

### Files not being analyzed

Check that files are in `compile_commands.json`:
```bash
cat compile_commands.json | grep "your_file.cpp"
```

### Headers not parsing

Headers often need to be compiled as part of a translation unit. Ensure your compilation database includes them, or they'll be parsed when included by .cpp files.

### Relative paths not working

paddingTON resolves relative paths using the `directory` field. Ensure your compilation database has correct directory entries.

## Example Workflow

```bash
# 1. Generate compilation database
cd my_project
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON build/
cd build && make
cp compile_commands.json ..

# 2. Analyze your code
cd ..
paddington analyze . --exclude '*/test/*'

# 3. Optimize with verification
paddington optimize . --apply --verify --exclude '*/test/*'

# 4. Or generate patches for review
paddington optimize . --patch-dir patches/ --exclude '*/test/*'
```

## References

- [Clang Compilation Database Specification](https://clang.llvm.org/docs/JSONCompilationDatabase.html)
- [CMake Documentation](https://cmake.org/cmake/help/latest/variable/CMAKE_EXPORT_COMPILE_COMMANDS.html)
- [Bear - Build EAR](https://github.com/rizsotto/Bear)
