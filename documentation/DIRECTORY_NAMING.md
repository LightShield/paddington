# Directory Naming Clarification

**Date**: 2026-01-16  
**Issue**: "domain" and "application" are too generic

---

## Current Names (Unclear)

```
paddington/
├── domain/          # What domain? Business logic? Data structures?
├── application/     # Application of what? The whole thing is an application!
```

## Proposed Names (Clear Intent)

```
paddington/
├── struct_data/              # Struct and member data structures
│   ├── struct_info.py        # StructInfo dataclass
│   ├── member_info.py        # MemberInfo dataclass
│   ├── optimization_plan.py  # OptimizationPlan dataclass
│   └── source_change.py      # SourceModification, TransformedSource dataclasses
│
├── padding_analysis/         # Padding calculation and optimization logic
│   ├── padding_calculator.py # Calculate padding from members
│   ├── member_reorderer.py   # Reorder members by size
│   ├── dependency_graph.py   # Build and sort dependency graph
│   └── size_calculator.py    # Calculate struct size from members
│
├── pipeline/                 # Pipeline orchestration (unchanged)
│   ├── stage.py
│   ├── pipeline.py
│   ├── extraction_stage.py
│   ├── analysis_stage.py
│   ├── planning_stage.py
│   ├── transformation_stage.py
│   └── output_stage.py       # Renamed from application_stage.py
│
├── providers/                # Swappable implementations (unchanged)
│   ├── extraction/
│   ├── transformation/
│   └── output/               # Renamed from application/
│       ├── base.py
│       ├── file_writer.py
│       ├── patch_generator.py
│       └── mock.py
│
├── cli/                      # CLI interface (unchanged)
│   ├── main.py
│   ├── analyze_command.py
│   └── optimize_command.py
│
├── utils/                    # Pure utilities (unchanged)
│   ├── logger.py
│   ├── file_filter.py
│   └── validation.py
│
└── tests/                    # All tests (unchanged)
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## Rationale for Changes

### 1. `domain/` → `struct_data/` + `padding_analysis/`

**Problem**: "domain" is too generic. Domain of what?

**Solution**: Split into two clear purposes:
- `struct_data/`: Data structures (StructInfo, MemberInfo, etc.)
- `padding_analysis/`: Business logic (padding calculation, reordering, etc.)

**Benefits**:
- Clear what each module contains
- Easy to find data structures vs logic
- Follows "data vs behavior" separation

### 2. `application/` → `output/`

**Problem**: "application" is ambiguous. The whole tool is an application!

**Solution**: Rename to `output/` - clearly about writing output

**Benefits**:
- Clear intent: "how do we output the results?"
- Matches the stage name better (output_stage)
- Parallel with `extraction/` and `transformation/`

### 3. `application_stage.py` → `output_stage.py`

**Problem**: Inconsistent with provider directory name

**Solution**: Rename to match provider directory

**Benefits**:
- Consistency: `output/` provider → `output_stage.py`
- Clear intent: "stage that outputs results"

---

## Updated Pipeline Stages

```
1. EXTRACTION     → providers/extraction/
2. ANALYSIS       → (uses padding_analysis/)
3. PLANNING       → (uses padding_analysis/)
4. TRANSFORMATION → providers/transformation/
5. OUTPUT         → providers/output/
```

---

## File Organization

### struct_data/ (Pure Data)

```python
# struct_data/struct_info.py
@dataclass(frozen=True)
class StructInfo:
    name: str
    size: int
    optimized_size: Optional[int]
    members: Tuple[MemberInfo, ...]
    file_path: Optional[str]
    line: Optional[int]
    ignore: bool = False
```

```python
# struct_data/member_info.py
@dataclass(frozen=True)
class MemberInfo:
    name: str
    type: str
    size: int
    optimized_size: Optional[int]
    offset: int
    access_modifier: str
    locked: bool = False
```

```python
# struct_data/optimization_plan.py
@dataclass(frozen=True)
class OptimizationPlan:
    struct: StructInfo
    original_order: Tuple[MemberInfo, ...]
    optimal_order: Tuple[MemberInfo, ...]
    padding_saved: int
    skip_reason: Optional[str] = None
```

```python
# struct_data/source_change.py
@dataclass(frozen=True)
class SourceModification:
    file_path: str
    struct_name: str
    modifications: Tuple[Modification, ...]

@dataclass(frozen=True)
class TransformedSource:
    file_path: str
    original_content: str
    new_content: str
    modifications: Tuple[SourceModification, ...]
```

### padding_analysis/ (Pure Logic)

```python
# padding_analysis/padding_calculator.py
def calculate_padding(members: List[MemberInfo], total_size: int) -> int:
    """Calculate total padding in struct."""
    pass

def calculate_internal_padding(members: List[MemberInfo]) -> int:
    """Calculate padding between members."""
    pass

def calculate_trailing_padding(members: List[MemberInfo], total_size: int) -> int:
    """Calculate padding at end of struct."""
    pass
```

```python
# padding_analysis/member_reorderer.py
def reorder_by_size(members: List[MemberInfo]) -> List[MemberInfo]:
    """Reorder members by size descending."""
    pass

def reorder_within_access_modifiers(members: List[MemberInfo]) -> List[MemberInfo]:
    """Reorder members within each access modifier section."""
    pass

def reorder_with_split_access_modifiers(members: List[MemberInfo]) -> List[MemberInfo]:
    """Reorder optimally, add access modifiers per member."""
    pass
```

```python
# padding_analysis/dependency_graph.py
def build_dependency_graph(structs: List[StructInfo]) -> Dict[str, Set[str]]:
    """Build graph of struct dependencies."""
    pass

def topological_sort(graph: Dict[str, Set[str]]) -> List[str]:
    """Sort structs in dependency order (leaves first)."""
    pass
```

```python
# padding_analysis/size_calculator.py
def calculate_struct_size(members: List[MemberInfo]) -> int:
    """Calculate struct size with alignment."""
    pass

def calculate_optimal_size(members: List[MemberInfo]) -> int:
    """Calculate size if members were optimally ordered."""
    pass
```

---

## Import Examples

### Before (Unclear)
```python
from paddington.domain.models import StructInfo, MemberInfo
from paddington.domain.padding_calculator import calculate_padding
from paddington.providers.application.file_writer import FileWriter
from paddington.pipeline.application_stage import ApplicationStage
```

### After (Clear)
```python
from paddington.struct_data.struct_info import StructInfo
from paddington.struct_data.member_info import MemberInfo
from paddington.padding_analysis.padding_calculator import calculate_padding
from paddington.providers.output.file_writer import FileWriter
from paddington.pipeline.output_stage import OutputStage
```

**Benefits**:
- Immediately clear what each import is for
- Easy to find where things are defined
- Self-documenting code

---

## Updated Agent Tasks

### Agent 1: Data Structures
**Task**: Create pure data structures  
**Files**: 
- `struct_data/struct_info.py`
- `struct_data/member_info.py`
- `struct_data/optimization_plan.py`
- `struct_data/source_change.py`

**Tests**: `tests/unit/test_struct_data/`

### Agent 2: Padding Analysis Logic
**Task**: Create pure padding analysis functions  
**Files**:
- `padding_analysis/padding_calculator.py`
- `padding_analysis/member_reorderer.py`
- `padding_analysis/dependency_graph.py`
- `padding_analysis/size_calculator.py`

**Tests**: `tests/unit/test_padding_analysis/`

### Agent 5: Output Provider Interface
**Task**: Define IOutputWriter interface + mock  
**Files**: 
- `providers/output/base.py`
- `providers/output/mock.py`

**Tests**: `tests/unit/test_providers/test_output_mock.py`

### Agent 10: File Writer
**Task**: Implement DirectFileWriter  
**Files**: `providers/output/file_writer.py`  
**Tests**: `tests/unit/test_providers/test_file_writer.py`

### Agent 11: Patch Generator
**Task**: Implement GitPatchGenerator  
**Files**: `providers/output/patch_generator.py`  
**Tests**: `tests/unit/test_providers/test_patch_generator.py`

### Agent 16: Output Stage
**Task**: Implement OutputStage  
**Files**: `pipeline/output_stage.py`  
**Tests**: `tests/unit/test_pipeline/test_output_stage.py`

---

## Summary

### Changes

1. ✅ `domain/` → `struct_data/` + `padding_analysis/`
2. ✅ `providers/application/` → `providers/output/`
3. ✅ `application_stage.py` → `output_stage.py`

### Benefits

- **Clarity**: Names reflect intent
- **Discoverability**: Easy to find what you need
- **Maintainability**: Clear separation of concerns
- **Self-documenting**: Code explains itself

### Migration

- Update all imports
- Update agent task descriptions
- Update documentation
- No logic changes, just renaming
