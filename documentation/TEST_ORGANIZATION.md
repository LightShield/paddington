# Test Organization Philosophies

**Question**: Should tests be separate or co-located with source code?

---

## Option 1: Separate Tests Directory (Current)

```
paddington/
├── implementation/
│   ├── user_interactions/
│   │   └── analyze.py
│   └── pipeline/
│       └── extraction/
│           └── pahole.py
└── tests/
    ├── unit/
    │   ├── user_interactions/
    │   │   └── test_analyze.py
    │   └── pipeline/
    │       └── extraction/
    │           └── test_pahole.py
    └── integration/
        └── pipeline/
            └── extraction/
                └── test_pahole_integration.py
```

**Pros**:
- Clear separation (code vs tests)
- Standard Python practice
- Easy to exclude tests from package distribution
- Can run all tests with `pytest tests/`

**Cons**:
- Duplicate directory structure
- Tests are "far" from code (different directory tree)
- Need to navigate between directories

---

## Option 2: Co-Located Tests (Next to Source)

```
paddington/
├── implementation/
│   ├── user_interactions/
│   │   ├── analyze.py
│   │   ├── test_analyze.py              # Unit test
│   │   └── test_analyze_integration.py  # Integration test
│   └── pipeline/
│       └── extraction/
│           ├── pahole.py
│           ├── test_pahole.py              # Unit test
│           └── test_pahole_integration.py  # Integration test
```

**Pros**:
- Tests right next to code (easy to find)
- No duplicate directory structure
- Easy to see what's tested (files side-by-side)
- Common in Go, Rust communities

**Cons**:
- Tests mixed with source code
- Harder to exclude tests from package
- Less common in Python

---

## Option 3: Hybrid - Tests Subdirectory in Each Module

```
paddington/
├── implementation/
│   ├── user_interactions/
│   │   ├── analyze.py
│   │   └── tests/
│   │       ├── test_analyze.py
│   │       └── test_analyze_integration.py
│   └── pipeline/
│       └── extraction/
│           ├── pahole.py
│           └── tests/
│               ├── test_pahole.py
│               └── test_pahole_integration.py
```

**Pros**:
- Tests close to code (same parent directory)
- Clear separation (in `tests/` subdirectory)
- No duplicate top-level structure

**Cons**:
- Many small `tests/` directories
- Harder to run all tests at once
- Less standard in Python

---

## Option 4: Flat Tests (No Unit/Integration Split)

```
paddington/
├── implementation/
│   ├── user_interactions/
│   │   └── analyze.py
│   └── pipeline/
│       └── extraction/
│           └── pahole.py
└── tests/
    ├── user_interactions/
    │   ├── test_analyze.py              # All tests for analyze
    │   └── test_analyze_integration.py  # (or just one file with both)
    └── pipeline/
        └── extraction/
            ├── test_pahole.py
            └── test_pahole_integration.py
```

**Pros**:
- Simpler structure (no unit/integration split at top)
- Tests still mirror implementation
- Easy to find tests

**Cons**:
- Can't easily run "only unit tests" or "only integration tests"
- Less clear which tests are fast vs slow

---

## Recommendation: Option 4 (Flat Tests)

**Structure**:
```
paddington/
├── __main__.py
├── README.md
│
├── implementation/
│   ├── user_interactions/
│   │   ├── analyze.py
│   │   └── optimize.py
│   ├── struct_data/
│   │   ├── struct_info.py
│   │   └── member_info.py
│   ├── padding_analysis/
│   │   ├── padding_calculator.py
│   │   └── member_reorderer.py
│   ├── pipeline/
│   │   ├── extraction/
│   │   │   ├── stage.py
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
│   └── utils/
│       ├── logger.py
│       └── file_filter.py
│
└── tests/                         # Mirrors implementation/
    ├── user_interactions/
    │   ├── test_analyze.py        # All tests (unit + integration)
    │   └── test_optimize.py
    ├── struct_data/
    │   ├── test_struct_info.py
    │   └── test_member_info.py
    ├── padding_analysis/
    │   ├── test_padding_calculator.py
    │   └── test_member_reorderer.py
    ├── pipeline/
    │   ├── extraction/
    │   │   ├── test_stage.py
    │   │   ├── test_pahole.py
    │   │   └── test_dwarf.py
    │   ├── transformation/
    │   │   ├── test_stage.py
    │   │   ├── test_srcml.py
    │   │   └── test_line_swap.py
    │   └── output/
    │       ├── test_stage.py
    │       ├── test_file_writer.py
    │       └── test_patch_generator.py
    ├── utils/
    │   ├── test_logger.py
    │   └── test_file_filter.py
    │
    ├── end_to_end/                # Only end-to-end tests separate
    │   ├── test_analyze_workflow.py
    │   └── test_optimize_workflow.py
    │
    └── fixtures/                  # Test data
        ├── object_files/
        ├── source_files/
        └── expected_outputs/
```

---

## Why This Works

### 1. One-to-One Mapping
```
implementation/pipeline/extraction/pahole.py
tests/pipeline/extraction/test_pahole.py
```
Easy to find: just replace `implementation/` with `tests/` and add `test_` prefix.

### 2. Test Organization Within File
```python
# tests/pipeline/extraction/test_pahole.py

import pytest
from paddington.implementation.pipeline.extraction.pahole import PaholeExtractor

# Unit tests (fast, no I/O)
class TestPaholeExtractorUnit:
    def test_parse_output(self):
        """Test parsing pahole output (no subprocess)."""
        pass
    
    def test_struct_deduplication(self):
        """Test deduplication logic."""
        pass

# Integration tests (with I/O)
class TestPaholeExtractorIntegration:
    @pytest.mark.integration
    def test_extract_from_real_file(self):
        """Test extraction from real .o file."""
        pass
    
    @pytest.mark.integration
    def test_pahole_not_installed(self):
        """Test error handling when pahole missing."""
        pass
```

### 3. Run Tests Selectively
```bash
# Run all tests
pytest tests/

# Run only unit tests (fast)
pytest tests/ -m "not integration"

# Run only integration tests
pytest tests/ -m integration

# Run tests for specific module
pytest tests/pipeline/extraction/

# Run tests for specific file
pytest tests/pipeline/extraction/test_pahole.py
```

### 4. No Duplicate Structure
Only one `tests/` directory that mirrors `implementation/`.

---

## Comparison

### Current (Separate Unit/Integration)
```
tests/
├── unit/
│   └── pipeline/
│       └── extraction/
│           └── test_pahole.py
└── integration/
    └── pipeline/
        └── extraction/
            └── test_pahole_integration.py
```
**Problem**: `pipeline/extraction/` appears twice!

### Recommended (Flat)
```
tests/
└── pipeline/
    └── extraction/
        └── test_pahole.py  # Contains both unit and integration tests
```
**Benefit**: `pipeline/extraction/` appears once!

---

## pytest Configuration

```ini
# pytest.ini
[pytest]
markers =
    integration: marks tests as integration tests (slow, with I/O)
    unit: marks tests as unit tests (fast, no I/O)

# Default: run all tests
# To run only unit tests: pytest -m "not integration"
# To run only integration tests: pytest -m integration
```

---

## Test File Template

```python
# tests/pipeline/extraction/test_pahole.py
"""Tests for PaholeExtractor."""

import pytest
from paddington.implementation.pipeline.extraction.pahole import PaholeExtractor

# ============================================================================
# Unit Tests (Fast, No I/O)
# ============================================================================

class TestPaholeExtractorUnit:
    """Unit tests for PaholeExtractor (no I/O)."""
    
    def test_parse_struct_name(self):
        """Test parsing struct name from pahole output."""
        pass
    
    def test_parse_member_info(self):
        """Test parsing member information."""
        pass
    
    def test_calculate_padding(self):
        """Test padding calculation logic."""
        pass

# ============================================================================
# Integration Tests (Slow, With I/O)
# ============================================================================

class TestPaholeExtractorIntegration:
    """Integration tests for PaholeExtractor (with I/O)."""
    
    @pytest.mark.integration
    def test_extract_from_simple_struct(self, tmp_path):
        """Test extraction from real object file with simple struct."""
        pass
    
    @pytest.mark.integration
    def test_extract_from_nested_struct(self, tmp_path):
        """Test extraction from real object file with nested structs."""
        pass
    
    @pytest.mark.integration
    def test_pahole_command_not_found(self):
        """Test error handling when pahole is not installed."""
        pass
```

---

## Summary

### Recommendation: Flat Tests Structure

**Structure**:
- `tests/` mirrors `implementation/` (one-to-one)
- Each test file contains both unit and integration tests
- Use pytest markers to distinguish: `@pytest.mark.integration`
- Only `end_to_end/` tests are separate (they test multiple modules)

**Benefits**:
- ✅ No duplicate directory structure
- ✅ Easy to find tests (just mirror the path)
- ✅ Can still run unit/integration separately (pytest markers)
- ✅ Simpler overall structure
- ✅ Standard Python practice (with markers)

**Run tests**:
```bash
pytest tests/                    # All tests
pytest tests/ -m "not integration"  # Only unit tests (fast)
pytest tests/ -m integration     # Only integration tests
pytest tests/pipeline/extraction/  # Tests for specific module
```

This is the best of both worlds: simple structure + selective test running.
