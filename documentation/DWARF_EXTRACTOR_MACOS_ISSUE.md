# DwarfExtractor Platform Limitation

## Issue

DwarfExtractor returns 0 structs on macOS.

## Root Cause

- **pyelftools** only supports ELF format (Linux)
- **macOS uses Mach-O format** (different binary format)
- DwarfExtractor catches ELFError and returns empty list

## Evidence

```python
with open(objfile, 'rb') as f:
    elf = ELFFile(f)  # Raises: ELFError: Magic number does not match
```

macOS .o files start with Mach-O magic number, not ELF magic number.

## Solution Options

### Option 1: Use pahole (Linux only)
- pahole works on Linux with ELF files
- Requires Docker on macOS
- Already have Dockerfile

### Option 2: Add Mach-O support
- Use `macholib` or similar for macOS
- Separate extractor for Mach-O format
- More complex

### Option 3: Document platform limitation
- DwarfExtractor: Linux only (ELF)
- PaholeExtractor: Linux only (via Docker on macOS)
- Tests skip on macOS (expected)

## Current Behavior

### On Linux
- ✅ DwarfExtractor works
- ✅ All e2e tests pass

### On macOS
- ⚠️ DwarfExtractor returns empty (ELF format not supported)
- ⚠️ E2E tests skip (expected behavior)
- ✅ Unit tests pass (don't need real extraction)

## Recommendation

**Document the platform limitation** and update tests to skip on macOS with clear message:

```python
@pytest.mark.skipif(
    sys.platform == 'darwin',
    reason="DwarfExtractor requires ELF format (Linux). Use Docker for testing on macOS."
)
```

This is **not a bug** - it's a platform limitation of pyelftools.

## For Production Use

Users on macOS should:
1. Use Docker for pahole extraction
2. Or test on Linux
3. Or add Mach-O support (future enhancement)

The architecture is correct, the implementation works on Linux, it's just a platform-specific limitation.
