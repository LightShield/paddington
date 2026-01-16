# paddingTON Refactoring Plan - FINAL

**Date**: 2026-01-16  
**Version**: 2.0 (Updated based on requirements)  
**Goal**: Refactor paddingTON to be testable, maintainable, and implementation-agnostic

---

## Executive Summary

Refactor paddingTON from a monolithic architecture to a clean, pipeline-based architecture with:
1. **Clear separation of concerns** via 5 pipeline stages
2. **Implementation-agnostic interfaces** (swap pahole for X, swap line-rewriter for srcML)
3. **100% unit testable** components with explicit markers
4. **Parallelizable work** for agent delegation
5. **Intuitive directory structure** reflecting intent

---

## Final Architecture

### Directory Structure

```
paddington/
├── __main__.py                    # Entry point
├── README.md                      # User documentation
├── documentation/                 # Design docs
├── implementation/                # All code
│   ├── user_interactions/         # User operations
│   ├── struct_data/               # Data structures
│   ├── padding_analysis/          # Business logic
│   ├── pipeline/                  # Stages + providers
│   │   ├── extraction/
│   │   ├── analysis/
│   │   ├── planning/
│   │   ├── transformation/
│   │   └── output/
│   └── utils/
└── tests/                         # Mirrors implementation/
    ├── user_interactions/
    ├── struct_data/
    ├── padding_analysis/
    ├── pipeline/
    ├── end_to_end/
    └── fixtures/
```

### Pipeline Stages

```
Input (.o files) 
  ↓
Stage 1: EXTRACTION → List[StructInfo]
  ↓
Stage 2: ANALYSIS (iterative) → List[OptimizationPlan]
  ↓
Stage 3: PLANNING → List[SourceModification]
  ↓
Stage 4: TRANSFORMATION → List[TransformedSource]
  ↓
Stage 5: OUTPUT → List[AppliedChange]
  ↓
Output (patches or modified files)
```

---

## Data Models

```python
# implementation/struct_data/member_info.py
@dataclass(frozen=True)
class MemberInfo:
    name: str
    type: str
    size: int                          # Original size from DWARF
    optimized_size: Optional[int]      # Size after optimization
    offset: int
    access_modifier: str               # "public", "private", "protected", "none"
    locked: bool = False               # User marked with paddington-lock

# implementation/struct_data/struct_info.py
@dataclass(frozen=True)
class StructInfo:
    name: str
    size: int                          # Original size
    optimized_size: Optional[int]      # Size after optimization
    members: Tuple[MemberInfo, ...]
    file_path: Optional[str] = None
    line: Optional[int] = None
    ignore: bool = False               # User marked with paddington-ignore
    ignore_reason: Optional[str] = None

# implementation/struct_data/optimization_plan.py
@dataclass(frozen=True)
class OptimizationPlan:
    struct: StructInfo
    original_order: Tuple[MemberInfo, ...]
    optimal_order: Tuple[MemberInfo, ...]
    padding_saved: int
    skip_reason: Optional[str] = None

# implementation/struct_data/source_change.py
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

---

## Work Breakdown for Parallel Agent Execution

### Phase 1: Foundation (Sequential - Must Complete First)

#### Agent 1: Data Structures
**Task**: Create immutable data structures  
**Files**: 
- `implementation/struct_data/struct_info.py`
- `implementation/struct_data/member_info.py`
- `implementation/struct_data/optimization_plan.py`
- `implementation/struct_data/source_change.py`

**Tests**: 
- `tests/struct_data/test_struct_info.py` (mark with `@pytest.mark.unit`)
- `tests/struct_data/test_member_info.py`
- `tests/struct_data/test_optimization_plan.py`
- `tests/struct_data/test_source_change.py`

**Dependencies**: None  
**Deliverable**: Immutable dataclasses with all required fields

**Key Requirements**:
- All dataclasses must be `frozen=True`
- Use `Tuple` not `List` for collections
- Include `optimized_size` and `access_modifier` fields
- Include `ignore` and `locked` fields

---

#### Agent 2: Padding Analysis Logic
**Task**: Create pure padding analysis functions  
**Files**: 
- `implementation/padding_analysis/padding_calculator.py`
- `implementation/padding_analysis/member_reorderer.py`
- `implementation/padding_analysis/dependency_graph.py`
- `implementation/padding_analysis/size_calculator.py`

**Tests**: 
- `tests/padding_analysis/test_padding_calculator.py` (mark with `@pytest.mark.unit`)
- `tests/padding_analysis/test_member_reorderer.py`
- `tests/padding_analysis/test_dependency_graph.py`
- `tests/padding_analysis/test_size_calculator.py`

**Dependencies**: Agent 1 (data structures)  
**Deliverable**: Pure functions for padding calculation, member reordering, dependency analysis

**Key Requirements**:
- `member_reorderer.py` must support three access modifier strategies:
  - `preserve`: Reorder within sections
  - `split`: Optimal order with per-member access modifiers
  - `ignore`: Reorder across all sections
- All functions are pure (no I/O, no side effects)
- Comprehensive unit tests

---

#### Agent 3: Pipeline Infrastructure
**Task**: Create pipeline base classes  
**Files**: 
- `implementation/pipeline/stage.py`
- `implementation/pipeline/pipeline.py`

**Tests**: 
- `tests/pipeline/test_stage.py` (mark with `@pytest.mark.unit`)
- `tests/pipeline/test_pipeline.py`

**Dependencies**: Agent 1 (models)  
**Deliverable**: Generic pipeline runner with stage interface

**Key Requirements**:
- `Stage` is generic: `Stage[TInput, TOutput]`
- `Pipeline` chains stages together
- Validates input/output between stages
- Supports logging and error handling

---

### Phase 2: Provider Interfaces (Parallel)

#### Agent 4: Extraction Provider Interface
**Task**: Define IStructExtractor interface + mock  
**Files**: 
- `implementation/pipeline/extraction/base.py`
- `implementation/pipeline/extraction/mock.py`

**Tests**: 
- `tests/pipeline/extraction/test_mock.py` (mark with `@pytest.mark.unit`)

**Dependencies**: Agent 1  
**Deliverable**: Interface + mock for testing

---

#### Agent 5: Transformation Provider Interface
**Task**: Define ISourceTransformer interface + mock  
**Files**: 
- `implementation/pipeline/transformation/base.py`
- `implementation/pipeline/transformation/mock.py`

**Tests**: 
- `tests/pipeline/transformation/test_mock.py` (mark with `@pytest.mark.unit`)

**Dependencies**: Agent 1  
**Deliverable**: Interface + mock for testing

---

#### Agent 6: Output Provider Interface
**Task**: Define IOutputWriter interface + mock  
**Files**: 
- `implementation/pipeline/output/base.py`
- `implementation/pipeline/output/mock.py`

**Tests**: 
- `tests/pipeline/output/test_mock.py` (mark with `@pytest.mark.unit`)

**Dependencies**: Agent 1  
**Deliverable**: Interface + mock for testing

---

### Phase 3: Concrete Providers (Parallel)

#### Agent 7: Pahole Extractor
**Task**: Implement PaholeExtractor  
**Files**: `implementation/pipeline/extraction/pahole.py`  
**Tests**: `tests/pipeline/extraction/test_pahole.py` (mark unit tests with `@pytest.mark.unit`, integration with `@pytest.mark.integration`)  
**Dependencies**: Agent 4  
**Deliverable**: Working pahole-based extractor

---

#### Agent 8: DWARF Extractor
**Task**: Implement DwarfExtractor (pyelftools)  
**Files**: `implementation/pipeline/extraction/dwarf.py`  
**Tests**: `tests/pipeline/extraction/test_dwarf.py` (mark appropriately)  
**Dependencies**: Agent 4  
**Deliverable**: Working pyelftools-based extractor

---

#### Agent 9: srcML Transformer
**Task**: Implement SrcMLTransformer  
**Files**: `implementation/pipeline/transformation/srcml.py`  
**Tests**: `tests/pipeline/transformation/test_srcml.py` (mark appropriately)  
**Dependencies**: Agent 5  
**Deliverable**: Working srcML-based transformer

**Key Requirements**:
- Convert source → srcML XML
- Manipulate XML to reorder members
- Preserve access modifier sections (based on strategy)
- Convert XML → source
- Preserve formatting

---

#### Agent 10: Line Swap Transformer
**Task**: Implement LineSwapTransformer (migrate current code)  
**Files**: `implementation/pipeline/transformation/line_swap.py`  
**Tests**: `tests/pipeline/transformation/test_line_swap.py` (mark appropriately)  
**Dependencies**: Agent 5  
**Deliverable**: Working line-swap transformer

---

#### Agent 11: File Writer
**Task**: Implement DirectFileWriter  
**Files**: `implementation/pipeline/output/file_writer.py`  
**Tests**: `tests/pipeline/output/test_file_writer.py` (mark appropriately)  
**Dependencies**: Agent 6  
**Deliverable**: Direct file modification with backups

---

#### Agent 12: Patch Generator
**Task**: Implement GitPatchGenerator  
**Files**: `implementation/pipeline/output/patch_generator.py`  
**Tests**: `tests/pipeline/output/test_patch_generator.py` (mark appropriately)  
**Dependencies**: Agent 6  
**Deliverable**: Git patch generation with commit messages

---

### Phase 4: Pipeline Stages (Parallel)

#### Agent 13: Extraction Stage
**Task**: Implement ExtractionStage  
**Files**: `implementation/pipeline/extraction/stage.py`  
**Tests**: `tests/pipeline/extraction/test_stage.py` (mark with `@pytest.mark.unit`)  
**Dependencies**: Agent 3, Agent 4  
**Deliverable**: Stage that uses IStructExtractor

---

#### Agent 14: Analysis Stage
**Task**: Implement AnalysisStage with iterative size propagation  
**Files**: `implementation/pipeline/analysis/stage.py`  
**Tests**: `tests/pipeline/analysis/test_stage.py` (mark with `@pytest.mark.unit`)  
**Dependencies**: Agent 2, Agent 3  
**Deliverable**: Iterative analysis that updates member sizes based on optimized dependencies

**Critical Implementation Details**:
1. Build dependency graph (one-time)
2. Topological sort to get bottom-up order (one-time)
3. **Iterative loop** over structs in dependency order:
   - Update member sizes from global type table
   - Recalculate struct size with updated member sizes
   - Calculate padding with updated sizes
   - Determine if optimization is beneficial
   - Create optimization plan
   - **Update global type table** with new size
4. Return plans in dependency order
5. Support three access modifier strategies: preserve, split, ignore

**Test Cases**:
- Simple struct (no dependencies)
- Nested struct (Inner → Outer)
- Multi-level nesting (A → B → C)
- Circular dependencies (should detect and skip)
- Struct becomes optimal after dependency optimization
- Access modifier strategy: preserve
- Access modifier strategy: split
- Access modifier strategy: ignore

---

#### Agent 15: Planning Stage
**Task**: Implement PlanningStage  
**Files**: `implementation/pipeline/planning/stage.py`  
**Tests**: `tests/pipeline/planning/test_stage.py` (mark with `@pytest.mark.unit`)  
**Dependencies**: Agent 2, Agent 3  
**Deliverable**: Generate source modification instructions

**Key Requirements**:
- Identify all locations that need changes:
  - Struct definition
  - Constructor initializer lists
  - Aggregate initializations
  - Smart pointer calls
- Group modifications by file
- Preserve access modifier sections

---

#### Agent 16: Transformation Stage
**Task**: Implement TransformationStage  
**Files**: `implementation/pipeline/transformation/stage.py`  
**Tests**: `tests/pipeline/transformation/test_stage.py` (mark with `@pytest.mark.unit`)  
**Dependencies**: Agent 3, Agent 5  
**Deliverable**: Stage that uses ISourceTransformer

---

#### Agent 17: Output Stage
**Task**: Implement OutputStage  
**Files**: `implementation/pipeline/output/stage.py`  
**Tests**: `tests/pipeline/output/test_stage.py` (mark with `@pytest.mark.unit`)  
**Dependencies**: Agent 3, Agent 6  
**Deliverable**: Stage that uses IOutputWriter

---

### Phase 5: User Interactions & Integration (Sequential)

#### Agent 18: User Interactions
**Task**: Implement analyze and optimize operations  
**Files**: 
- `__main__.py` (entry point with arg parsing)
- `implementation/user_interactions/analyze.py`
- `implementation/user_interactions/optimize.py`

**Tests**: 
- `tests/user_interactions/test_analyze.py` (mark appropriately)
- `tests/user_interactions/test_optimize.py`

**Dependencies**: All previous agents  
**Deliverable**: Working CLI with provider selection

**Key Requirements**:
- Parse CLI arguments
- Select providers based on flags
- Build pipeline with selected providers
- Run pipeline
- Report results
- Handle errors gracefully

---

#### Agent 19: End-to-End Tests
**Task**: Create comprehensive E2E tests  
**Files**: 
- `tests/end_to_end/test_analyze_workflow.py` (mark with `@pytest.mark.e2e`)
- `tests/end_to_end/test_optimize_workflow.py`
- `tests/end_to_end/test_full_pipeline.py`

**Tests**: Multiple scenarios with different provider combinations  
**Dependencies**: All previous agents  
**Deliverable**: Full pipeline validation

**Test Scenarios**:
- Analyze with pahole extractor
- Analyze with dwarf extractor
- Optimize with srcML transformer + patch output
- Optimize with line-swap transformer + file output
- Optimize with access modifier strategy: preserve
- Optimize with access modifier strategy: split
- Optimize with access modifier strategy: ignore
- Optimize with user directives (paddington-ignore)
- Optimize nested structs (dependency ordering)

---

## Testing Requirements

### All Tests Must Be Marked

```python
@pytest.mark.unit          # Fast, no I/O, use mocks
@pytest.mark.integration   # Slow, with I/O, use real tools
@pytest.mark.e2e           # Slowest, full workflows
```

### Pytest Configuration

```ini
# tests/pytest.ini
[pytest]
markers =
    unit: marks tests as unit tests (fast, no I/O, use mocks)
    integration: marks tests as integration tests (slow, with I/O)
    e2e: marks tests as end-to-end tests (slowest, full workflows)

addopts = 
    --strict-markers
    --tb=short
```

### Running Tests

```bash
pytest -m unit          # Only unit tests (<5 min)
pytest -m integration   # Only integration tests (<30 min)
pytest -m e2e           # Only end-to-end tests
pytest tests/           # All tests
```

---

## Key Requirements Summary

### P0 (Must Have)

**Functional**:
- Struct padding detection and optimization
- Dependency-aware optimization (iterative analysis)
- Three access modifier strategies (preserve/split/ignore)
- User directives (paddington-ignore, paddington-lock)
- Multiple output modes (analyze, dry-run, modify, patch)
- File filtering (include/exclude patterns)

**Non-Functional**:
- >90% test coverage for core logic
- All tests explicitly marked
- Tests mirror implementation structure
- Provider swappability
- CLI-first configuration
- Clear directory structure

### P1 (Should Have)
- Minimum savings threshold
- Build verification
- Progress reporting

### P2 (Nice to Have)
- Configuration preset file (paddington.toml)
- Region-level directives (paddington-off/on)
- Custom directive markers

---

## Timeline Estimate

- **Phase 1**: 3 agents × 2 days = 6 agent-days (sequential)
- **Phase 2**: 3 agents × 1 day = 3 agent-days (parallel)
- **Phase 3**: 6 agents × 3 days = 18 agent-days (parallel)
- **Phase 4**: 5 agents × 2 days = 10 agent-days (parallel)
- **Phase 5**: 2 agents × 3 days = 6 agent-days (sequential)

**Total**: 43 agent-days  
**Wall time** (with parallelization): ~13 days

---

## Success Criteria

### Testability
- [x] 100% of data structures have unit tests
- [x] 100% of business logic has unit tests
- [x] All providers have integration tests
- [x] E2E tests cover main workflows
- [x] All tests explicitly marked
- [x] Tests run in <5 minutes (unit), <30 minutes (integration)

### Maintainability
- [x] Clear separation of concerns
- [x] Each module has single responsibility
- [x] Directory structure reflects intent
- [x] Tests mirror implementation
- [x] Documentation for each component

### Flexibility
- [x] Can swap extraction provider (pahole/dwarf)
- [x] Can swap transformation provider (srcML/line-swap)
- [x] Can swap output provider (patch/file-writer)
- [x] Can add new providers by implementing interface
- [x] CLI-driven configuration

### Parallelizability
- [x] Agents can work independently
- [x] No circular dependencies
- [x] Clear interfaces enable parallel development
- [x] Integration happens at well-defined boundaries

---

## Next Steps

1. **Review and approve** this plan
2. **Create project structure** (empty directories and __init__.py files)
3. **Assign agents** to Phase 1 tasks
4. **Begin implementation** with data structures and padding analysis
5. **Iterate through phases** with regular integration checkpoints
