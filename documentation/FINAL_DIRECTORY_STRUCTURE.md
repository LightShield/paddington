# Final Directory Structure

**Date**: 2026-01-16  
**Concept**: Clean top-level with implementation details nested

---

## Top-Level Structure (Clean & Clear)

```
paddington/                        # Repository root
│
├── __main__.py                    # Entry point (python -m paddington)
│
├── README.md                      # User documentation
├── REQUIREMENTS.md                # Requirements specification
├── DESIGN.md                      # Design documentation
├── KEY_INSIGHTS.md                # Design decisions
├── PIPELINE_STAGES_EXPLAINED.md  # Pipeline documentation
│
├── implementation/                # All implementation code
│   ├── user_interactions/         # User-facing operations
│   ├── struct_data/               # Data structures
│   ├── padding_analysis/          # Business logic
│   ├── pipeline/                  # Pipeline stages + providers
│   └── utils/                     # Utilities
│
└── tests/                         # All tests
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## Detailed Structure

```
paddington/
│
├── __main__.py                    # Entry point
│
├── README.md                      # Documentation
├── REQUIREMENTS.md
├── DESIGN.md
├── KEY_INSIGHTS.md
├── PIPELINE_STAGES_EXPLAINED.md
├── requirements.txt               # Python dependencies
├── requirements-dev.txt
├── pytest.ini
├── .gitignore
│
├── implementation/                # All implementation code
│   │
│   ├── __init__.py
│   │
│   ├── user_interactions/         # User-facing operations
│   │   ├── __init__.py
│   │   └── optimize.py            # optimize operation (default: dry-run, --apply to modify)
│   │
│   ├── struct_data/               # Data structures
│   │   ├── __init__.py
│   │   ├── struct_info.py
│   │   ├── member_info.py
│   │   ├── optimization_plan.py
│   │   └── source_change.py
│   │
│   ├── padding_analysis/          # Business logic
│   │   ├── __init__.py
│   │   ├── padding_calculator.py
│   │   ├── member_reorderer.py
│   │   ├── dependency_graph.py
│   │   └── size_calculator.py
│   │
│   ├── pipeline/                  # Pipeline stages + providers
│   │   ├── __init__.py
│   │   ├── stage.py               # Base Stage interface
│   │   ├── pipeline.py            # Pipeline runner
│   │   │
│   │   ├── extraction/            # Stage 1: Extraction
│   │   │   ├── __init__.py
│   │   │   ├── stage.py           # ExtractionStage
│   │   │   ├── base.py            # IStructExtractor interface
│   │   │   ├── pahole.py          # PaholeExtractor
│   │   │   ├── dwarf.py           # DwarfExtractor
│   │   │   └── mock.py            # MockExtractor
│   │   │
│   │   ├── analysis/              # Stage 2: Analysis
│   │   │   ├── __init__.py
│   │   │   └── stage.py           # AnalysisStage
│   │   │
│   │   ├── planning/              # Stage 3: Planning
│   │   │   ├── __init__.py
│   │   │   └── stage.py           # PlanningStage
│   │   │
│   │   ├── transformation/        # Stage 4: Transformation
│   │   │   ├── __init__.py
│   │   │   ├── stage.py           # TransformationStage
│   │   │   ├── base.py            # ISourceTransformer interface
│   │   │   ├── srcml.py           # SrcMLTransformer
│   │   │   ├── line_swap.py       # LineSwapTransformer
│   │   │   └── mock.py            # MockTransformer
│   │   │
│   │   └── output/                # Stage 5: Output
│   │       ├── __init__.py
│   │       ├── stage.py           # OutputStage
│   │       ├── base.py            # IOutputWriter interface
│   │       ├── file_writer.py     # DirectFileWriter
│   │       ├── patch_generator.py # GitPatchGenerator
│   │       └── mock.py            # MockOutputWriter
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── file_filter.py
│       └── validation.py
│
└── tests/                         # All tests (mirrors implementation/)
    ├── __init__.py
    ├── conftest.py                # Shared pytest fixtures
    ├── pytest.ini                 # Pytest configuration
    │
    ├── user_interactions/         # Tests for user_interactions/
    │   └── test_optimize.py       # Unit + integration tests
    │
    ├── struct_data/               # Tests for struct_data/
    │   ├── test_struct_info.py
    │   ├── test_member_info.py
    │   ├── test_optimization_plan.py
    │   └── test_source_change.py
    │
    ├── padding_analysis/          # Tests for padding_analysis/
    │   ├── test_padding_calculator.py
    │   ├── test_member_reorderer.py
    │   ├── test_dependency_graph.py
    │   └── test_size_calculator.py
    │
    ├── pipeline/                  # Tests for pipeline/
    │   ├── test_stage.py
    │   ├── test_pipeline.py
    │   │
    │   ├── extraction/
    │   │   ├── test_stage.py      # Unit + integration tests
    │   │   ├── test_pahole.py     # Unit + integration tests
    │   │   ├── test_dwarf.py      # Unit + integration tests
    │   │   └── test_mock.py       # Unit tests only
    │   │
    │   ├── analysis/
    │   │   └── test_stage.py      # Unit tests
    │   │
    │   ├── planning/
    │   │   └── test_stage.py      # Unit tests
    │   │
    │   ├── transformation/
    │   │   ├── test_stage.py      # Unit + integration tests
    │   │   ├── test_srcml.py      # Unit + integration tests
    │   │   ├── test_line_swap.py  # Unit + integration tests
    │   │   └── test_mock.py       # Unit tests only
    │   │
    │   └── output/
    │       ├── test_stage.py           # Unit + integration tests
    │       ├── test_file_writer.py     # Unit + integration tests
    │       ├── test_patch_generator.py # Unit + integration tests
    │       └── test_mock.py            # Unit tests only
    │
    ├── utils/                     # Tests for utils/
    │   ├── test_logger.py
    │   ├── test_file_filter.py
    │   └── test_validation.py
    │
    ├── end_to_end/                # End-to-end workflow tests
    │   ├── test_optimize_workflow.py
    │   └── test_full_pipeline.py
    │
    └── fixtures/                  # Test data
        ├── object_files/
        │   ├── simple.o
        │   ├── nested.o
        │   └── template.o
        ├── source_files/
        │   ├── simple.cpp
        │   ├── nested.cpp
        │   └── template.cpp
        └── expected_outputs/
            ├── simple_optimized.cpp
            ├── nested_optimized.cpp
            └── template_optimized.cpp
```

---

## Benefits of This Structure

### 1. Clean Top Level
```
paddington/
├── __main__.py          # Entry point
├── README.md            # Documentation
├── implementation/      # All code
└── tests/               # All tests
```

**Why**:
- Immediately clear what's what
- Documentation at top level (easy to find)
- Implementation details nested (not cluttering top level)
- Tests separate (standard practice)

### 2. Clear Intent
- `implementation/` = "This is how it works"
- `user_interactions/` = "This is what users can do"
- `struct_data/` = "This is the data we work with"
- `padding_analysis/` = "This is the core logic"
- `pipeline/` = "This is how we process data"

### 3. Scalability
Easy to add new components:
```
implementation/
├── user_interactions/
│   ├── analyze.py
│   ├── optimize.py
│   ├── validate.py      # New operation
│   └── report.py        # New operation
```

### 4. Standard Python Package
```python
# Import from implementation
from paddington.implementation.user_interactions import analyze
from paddington.implementation.struct_data import StructInfo
from paddington.implementation.pipeline.extraction import PaholeExtractor
```

---

## `__main__.py` (Entry Point)

```python
"""Entry point for paddington CLI."""
import argparse
from pathlib import Path
from paddington.implementation.user_interactions import optimize

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="paddingTON - C++ struct padding optimizer"
    )
    
    # optimize command (single command, no subparsers needed)
    parser.add_argument("path", type=Path, help="Path to object files")
    parser.add_argument("--apply", action="store_true",
                         help="Apply changes (default: dry-run)")
    parser.add_argument("--min-savings", type=int, default=0,
                         help="Minimum bytes to optimize")
    parser.add_argument("--access-modifier-strategy",
                         choices=["preserve", "split", "ignore"],
                         default="preserve",
                         help="How to handle access modifiers")
    parser.add_argument("--extractor", choices=["pahole", "dwarf"],
                         default="pahole", help="Extraction method")
    parser.add_argument("--transformer", choices=["srcml", "line-swap"],
                         default="srcml", help="Transformation method")
    parser.add_argument("--output", choices=["patch", "file"],
                         default="patch", help="Output method")
    parser.add_argument("--patch-dir", type=Path, default=Path("./patches"),
                         help="Directory for patches")
    parser.add_argument("--include", action="append", help="Include pattern")
    parser.add_argument("--exclude", action="append", help="Exclude pattern")
    parser.add_argument("-v", "--verbose", action="count", default=1,
                         help="Increase verbosity")
    
    args = parser.parse_args()
    
    # Run optimize operation
    optimize.run(args)

if __name__ == "__main__":
    main()
```

---

## Import Examples

```python
# From user_interactions
from paddington.implementation.user_interactions.optimize import run as run_optimize

# From struct_data
from paddington.implementation.struct_data.struct_info import StructInfo
from paddington.implementation.struct_data.member_info import MemberInfo

# From padding_analysis
from paddington.implementation.padding_analysis.padding_calculator import calculate_padding
from paddington.implementation.padding_analysis.member_reorderer import reorder_by_size

# From pipeline
from paddington.implementation.pipeline import Pipeline
from paddington.implementation.pipeline.extraction import ExtractionStage, PaholeExtractor
from paddington.implementation.pipeline.transformation import TransformationStage, SrcMLTransformer
from paddington.implementation.pipeline.output import OutputStage, PatchGenerator
```

---

## Comparison

### Before (Cluttered Top Level)
```
paddington/
├── __main__.py
├── analyze.py
├── optimize.py
├── struct_data/
├── padding_analysis/
├── pipeline/
├── utils/
├── tests/
├── README.md
├── REQUIREMENTS.md
├── DESIGN.md
└── ... (many files)
```

### After (Clean Top Level)
```
paddington/
├── __main__.py          # Entry point
├── README.md            # Documentation
├── implementation/      # All code (nested)
└── tests/               # All tests
```

---

## Agent Task Updates

All agent file paths now start with `implementation/`:

### Agent 1: Data Structures
**Files**: `implementation/struct_data/*.py`

### Agent 2: Padding Analysis
**Files**: `implementation/padding_analysis/*.py`

### Agent 3-11: Providers
**Files**: `implementation/pipeline/{extraction,transformation,output}/*.py`

### Agent 12-16: Stages
**Files**: `implementation/pipeline/{extraction,analysis,planning,transformation,output}/stage.py`

### Agent 17: User Interactions
**Files**: 
- `__main__.py`
- `implementation/user_interactions/optimize.py`

---

## Summary

### Top Level (4 items)
1. `__main__.py` - Entry point
2. `*.md` files - Documentation
3. `implementation/` - All code
4. `tests/` - All tests

### Implementation (5 subdirectories)
1. `user_interactions/` - What users can do
2. `struct_data/` - Data structures
3. `padding_analysis/` - Core logic
4. `pipeline/` - Processing stages
5. `utils/` - Utilities

### Benefits
- ✅ Clean top level
- ✅ Clear intent
- ✅ Easy to navigate
- ✅ Scalable
- ✅ Standard Python package structure

This structure makes it immediately clear:
- **What** the tool does (documentation at top)
- **How** to run it (`__main__.py`)
- **How** it works (`implementation/`)
- **How** to test it (`tests/`)


---

## Test Organization

### Flat Structure with Pytest Markers

Tests mirror the `implementation/` structure exactly. Each test file contains both unit and integration tests, distinguished by pytest markers.

**Example test file**:
```python
# tests/pipeline/extraction/test_pahole.py
"""Tests for PaholeExtractor."""

import pytest
from paddington.implementation.pipeline.extraction.pahole import PaholeExtractor

# ============================================================================
# Unit Tests (Fast, No I/O) - Mark with @pytest.mark.unit
# ============================================================================

class TestPaholeExtractorUnit:
    """Unit tests for PaholeExtractor (no I/O, use mocks)."""
    
    @pytest.mark.unit
    def test_parse_struct_name(self):
        """Test parsing struct name from pahole output."""
        output = "struct UserData {\n..."
        extractor = PaholeExtractor()
        result = extractor._parse_struct_name(output)
        assert result == "UserData"
    
    @pytest.mark.unit
    def test_calculate_padding(self):
        """Test padding calculation logic."""
        members = [...]
        padding = PaholeExtractor._calculate_padding(members)
        assert padding == 8

# ============================================================================
# Integration Tests (Slow, With I/O) - Mark with @pytest.mark.integration
# ============================================================================

class TestPaholeExtractorIntegration:
    """Integration tests for PaholeExtractor (with real I/O)."""
    
    @pytest.mark.integration
    def test_extract_from_real_file(self, tmp_path):
        """Test extraction from real object file."""
        # Compile test file
        source = tmp_path / "test.cpp"
        source.write_text("struct Simple { char a; int b; };")
        obj = tmp_path / "test.o"
        subprocess.run(["g++", "-g", "-c", str(source), "-o", str(obj)])
        
        # Extract
        extractor = PaholeExtractor()
        structs = extractor.extract([obj])
        
        assert len(structs) == 1
        assert structs[0].name == "Simple"
    
    @pytest.mark.integration
    def test_pahole_not_installed(self, monkeypatch):
        """Test error handling when pahole is not installed."""
        monkeypatch.setenv("PATH", "")
        extractor = PaholeExtractor()
        
        with pytest.raises(FileNotFoundError):
            extractor.extract([Path("test.o")])
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run only unit tests (fast, no I/O)
pytest tests/ -m "not integration"

# Run only integration tests (slow, with I/O)
pytest tests/ -m integration

# Run tests for specific module
pytest tests/pipeline/extraction/

# Run specific test file
pytest tests/pipeline/extraction/test_pahole.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=paddington.implementation
```

### Pytest Configuration

```ini
# tests/pytest.ini
[pytest]
# Test markers (ALL tests must be marked)
markers =
    unit: marks tests as unit tests (fast, no I/O, use mocks)
    integration: marks tests as integration tests (slow, with I/O, use real tools)
    e2e: marks tests as end-to-end tests (slowest, full workflows)

# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output
addopts = 
    -ra
    --strict-markers
    --tb=short
    
# Require all tests to have a marker
[pytest:mark]
required_markers = unit, integration, e2e
```

### Marking Tests (ALL tests MUST be marked)

**Unit tests**:
```python
@pytest.mark.unit
def test_parse_struct_name():
    """Unit test - fast, no I/O."""
    pass
```

**Integration tests**:
```python
@pytest.mark.integration
def test_extract_from_real_file():
    """Integration test - slow, with I/O."""
    pass
```

**End-to-end tests**:
```python
@pytest.mark.e2e
def test_full_optimize_workflow():
    """End-to-end test - slowest, full workflow."""
    pass
```

### Running Tests by Type

```bash
# Run only unit tests (fast)
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run only end-to-end tests
pytest tests/ -m e2e

# Run unit + integration (exclude e2e)
pytest tests/ -m "unit or integration"

# Run all tests
pytest tests/
```

### Benefits of Explicit Marking

1. **Clear intent**: Every test declares what it is
2. **Easy selection**: `pytest -m unit` (not `pytest -m "not integration and not e2e"`)
3. **Self-documenting**: Code is explicit about test type
4. **Enforced**: pytest can warn about unmarked tests

### Benefits

1. **No duplicate structure**: `pipeline/extraction/` appears once in `tests/`, not in both `tests/unit/` and `tests/integration/`
2. **Easy to find tests**: `implementation/pipeline/extraction/pahole.py` → `tests/pipeline/extraction/test_pahole.py`
3. **Selective test running**: Use pytest markers to run only unit or integration tests
4. **Standard practice**: Common pattern in Python projects
