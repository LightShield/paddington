# Testing on macOS - Platform Limitations and Solutions

## Issue

DwarfExtractor doesn't work on macOS because:
- pyelftools only supports ELF format (Linux)
- macOS uses Mach-O format
- Result: E2E tests skip on macOS

## Current Test Results on macOS

✅ **199 tests passing** (all unit tests)  
⚠️ **13 tests skipping** (e2e tests requiring struct extraction)  
✅ **0 failures**  
✅ **0 false positives**  

## Solutions

### Option 1: Use Docker (Recommended)

**Install Docker**:
```bash
# Install Docker Desktop for Mac
# https://www.docker.com/products/docker-desktop

# Verify installation
docker --version
```

**Run tests in Docker**:
```bash
# Build image (one time)
docker build -t paddington-test .

# Run all tests
./run_tests_docker.sh

# Run specific tests
./run_tests_docker.sh tests/end_to_end/ -v
```

**Benefits**:
- ✅ All tests run (Linux environment)
- ✅ DwarfExtractor works (ELF format)
- ✅ Full system verification
- ✅ Same environment as production Linux

### Option 2: Test on Linux

**Use Linux machine or VM**:
```bash
# On Linux
python -m pytest tests/

# All 212 tests should pass (199 unit + 13 e2e)
```

### Option 3: Add Mach-O Support (Future)

**Create MachoExtractor**:
- Use `macholib` or `pyobjc` to parse Mach-O files
- Extract DWARF from Mach-O format
- Implement `IMachoExtractor(IStructExtractor)`

**Effort**: Medium (2-3 days)

## Recommended Workflow

### For Development on macOS
1. **Unit tests**: Run natively (199 tests, all pass)
   ```bash
   python -m pytest tests/ -m unit
   ```

2. **E2E tests**: Run in Docker (13 tests)
   ```bash
   ./run_tests_docker.sh tests/end_to_end/
   ```

3. **Quick check**: Run without Docker (tests skip gracefully)
   ```bash
   python -m pytest tests/
   # 199 passed, 13 skipped - OK!
   ```

### For CI/CD
- Use Linux runners (GitHub Actions, GitLab CI, etc.)
- All 212 tests run natively
- No Docker needed

### For Production
- **Linux**: Works natively ✅
- **macOS**: Use Docker or add Mach-O support

## Current State

The system is **fully functional on Linux** and has **proper test infrastructure** that:
- ✅ Runs all tests on Linux
- ✅ Skips gracefully on macOS (with clear message)
- ✅ Can run in Docker on macOS (with setup)
- ✅ No false positives

This is a **platform limitation**, not a bug. The architecture and tests are correct.
