# paddingTON Refactoring Plan

**Date**: 2026-01-16  
**Goal**: Refactor paddingTON to be testable, maintainable, and implementation-agnostic

---

## Executive Summary

Refactor paddingTON from a monolithic, tightly-coupled architecture to a clean, pipeline-based architecture with:
1. **Clear separation of concerns** via pipeline stages
2. **Implementation-agnostic interfaces** (swap pahole for X, swap line-rewriter for srcML)
3. **100% unit testable** components
4. **Parallelizable work** for agent delegation
5. **Intuitive directory structure** reflecting intent

---

## Current Problems

### 1. Tight Coupling
- `optimize.py` directly imports `pahole_parser` and `dwarf_extractor`
- Rewriters are scattered (`rewriter.py`, `rewriter_minimal.py`, `rewriter_simple.py`)
- No clear abstraction between "what to do" and "how to do it"

### 2. Poor Testability
- Hard to mock DWARF extraction
- Hard to test rewriters without real files
- No clear interfaces to test against

### 3. Unclear Directory Structure
```
paddington/
├── core/          # Mix of parsing, models, and integration
├── analysis/      # Just reporting
├── optimization/  # Mix of orchestration and rewriting
└── utils/         # Grab bag
```

### 4. Non-Parallelizable
- Sequential processing in `optimize.py`
- No clear boundaries for parallel work

---

## New Architecture: Pipeline-Based

### Core Concept: Stages

```
Input → Stage1 → Stage2 → Stage3 → Output
         ↓        ↓        ↓
      Provider  Provider Provider
```

Each stage:
- Has a **clear interface** (input/output types)
- Uses a **provider** (swappable implementation)
- Is **independently testable**
- Can be **parallelized** if stateless

### Pipeline Stages

```
1. EXTRACTION
   Input: List[Path] (object files)
   Output: List[StructInfo]
   Provider: PaholeExtractor | DwarfExtractor | CustomExtractor

2. ANALYSIS
   Input: List[StructInfo]
   Output: List[OptimizationPlan]
   Provider: PaddingAnalyzer

3. PLANNING
   Input: List[OptimizationPlan]
   Output: List[SourceModification]
   Provider: MemberReorderer

4. TRANSFORMATION
   Input: List[SourceModification]
   Output: List[TransformedSource]
   Provider: SrcMLTransformer | LineSwapTransformer

5. APPLICATION
   Input: List[TransformedSource]
   Output: List[AppliedChange]
   Provider: FileWriter | PatchGenerator
```

---

## New Directory Structure

```
paddington/
├── __main__.py                    # Entry point (python -m paddington)
│
├── README.md                      # User documentation
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Development dependencies
├── .gitignore
│
├── documentation/                 # All design documentation
│   ├── REQUIREMENTS.md
│   ├── KEY_INSIGHTS.md
│   ├── PIPELINE_STAGES_EXPLAINED.md
│   ├── FINAL_DIRECTORY_STRUCTURE.md
│   └── REFACTORING_PLAN.md
│
├── implementation/                # All implementation code
│   │
│   ├── user_interactions/         # User-facing operations
│   │   ├── __init__.py
│   │   ├── analyze.py             # analyze operation
│   │   └── optimize.py            # optimize operation
│   │
│   ├── struct_data/               # Data structures
│   │   ├── __init__.py
│   │   ├── struct_info.py         # StructInfo dataclass
│   │   ├── member_info.py         # MemberInfo dataclass
│   │   ├── optimization_plan.py   # OptimizationPlan dataclass
│   │   └── source_change.py       # SourceModification, TransformedSource
│   │
│   ├── padding_analysis/          # Business logic
│   │   ├── __init__.py
│   │   ├── padding_calculator.py  # Calculate padding from members
│   │   ├── member_reorderer.py    # Reorder members by size
│   │   ├── dependency_graph.py    # Build and sort dependency graph
│   │   └── size_calculator.py     # Calculate struct size from members
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
│   │   │   └── mock.py            # MockExtractor (for tests)
│   │   │
│   │   ├── analysis/              # Stage 2: Analysis
│   │   │   ├── __init__.py
│   │   │   └── stage.py           # AnalysisStage (iterative)
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
│   │   │   └── mock.py            # MockTransformer (for tests)
│   │   │
│   │   └── output/                # Stage 5: Output
│   │       ├── __init__.py
│   │       ├── stage.py           # OutputStage
│   │       ├── base.py            # IOutputWriter interface
│   │       ├── file_writer.py     # DirectFileWriter
│   │       ├── patch_generator.py # GitPatchGenerator
│   │       └── mock.py            # MockOutputWriter (for tests)
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── logger.py              # Structured logging
│       ├── file_filter.py         # File filtering (include/exclude)
│       └── validation.py          # Input validation
│
└── tests/                         # All tests (mirrors implementation/)
    ├── __init__.py
    ├── pytest.ini                 # Pytest configuration
    ├── conftest.py                # Shared fixtures
    │
    ├── user_interactions/
    │   ├── test_analyze.py        # Unit + integration tests
    │   └── test_optimize.py
    │
    ├── struct_data/
    │   ├── test_struct_info.py
    │   ├── test_member_info.py
    │   ├── test_optimization_plan.py
    │   └── test_source_change.py
    │
    ├── padding_analysis/
    │   ├── test_padding_calculator.py
    │   ├── test_member_reorderer.py
    │   ├── test_dependency_graph.py
    │   └── test_size_calculator.py
    │
    ├── pipeline/
    │   ├── test_stage.py
    │   ├── test_pipeline.py
    │   │
    │   ├── extraction/
    │   │   ├── test_stage.py
    │   │   ├── test_pahole.py
    │   │   ├── test_dwarf.py
    │   │   └── test_mock.py
    │   │
    │   ├── analysis/
    │   │   └── test_stage.py
    │   │
    │   ├── planning/
    │   │   └── test_stage.py
    │   │
    │   ├── transformation/
    │   │   ├── test_stage.py
    │   │   ├── test_srcml.py
    │   │   ├── test_line_swap.py
    │   │   └── test_mock.py
    │   │
    │   └── output/
    │       ├── test_stage.py
    │       ├── test_file_writer.py
    │       ├── test_patch_generator.py
    │       └── test_mock.py
    │
    ├── utils/
    │   ├── test_logger.py
    │   ├── test_file_filter.py
    │   └── test_validation.py
    │
    ├── end_to_end/                # End-to-end workflow tests
    │   ├── test_analyze_workflow.py
    │   ├── test_optimize_workflow.py
    │   └── test_full_pipeline.py
    │
    └── fixtures/                  # Test data
        ├── object_files/
        ├── source_files/
        └── expected_outputs/
```

---

## Detailed Component Design

### 1. Domain Models (Pure Data)

```python
# domain/models.py
@dataclass(frozen=True)  # Immutable
class MemberInfo:
    name: str
    type: str
    size: int
    offset: int

@dataclass(frozen=True)
class StructInfo:
    name: str
    size: int
    members: Tuple[MemberInfo, ...]  # Immutable
    file_path: Optional[str] = None
    line: Optional[int] = None

@dataclass(frozen=True)
class OptimizationPlan:
    struct: StructInfo
    original_order: Tuple[MemberInfo, ...]
    optimal_order: Tuple[MemberInfo, ...]
    padding_saved: int
    skip_reason: Optional[str] = None

@dataclass(frozen=True)
class SourceModification:
    file_path: str
    struct_name: str
    modifications: Tuple[Modification, ...]  # Line changes, etc.

@dataclass(frozen=True)
class TransformedSource:
    file_path: str
    original_content: str
    new_content: str
    modifications: Tuple[SourceModification, ...]
```

### 2. Pipeline Stages (Interfaces)

```python
# pipeline/stage.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')

class Stage(ABC, Generic[TInput, TOutput]):
    """Base class for pipeline stages."""
    
    @abstractmethod
    def process(self, input_data: TInput) -> TOutput:
        """Process input and return output."""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: TInput) -> bool:
        """Validate input before processing."""
        pass
```

```python
# pipeline/extraction_stage.py
class ExtractionStage(Stage[List[Path], List[StructInfo]]):
    def __init__(self, extractor: IStructExtractor):
        self.extractor = extractor
    
    def process(self, objfiles: List[Path]) -> List[StructInfo]:
        return self.extractor.extract(objfiles)
```

### 3. Provider Interfaces

```python
# providers/extraction/base.py
class IStructExtractor(ABC):
    @abstractmethod
    def extract(self, objfiles: List[Path]) -> List[StructInfo]:
        """Extract struct information from object files."""
        pass
    
    @abstractmethod
    def supports_caching(self) -> bool:
        """Whether this extractor supports caching."""
        pass
```

```python
# providers/transformation/base.py
class ISourceTransformer(ABC):
    @abstractmethod
    def transform(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        """Transform source code based on modifications."""
        pass
    
    @abstractmethod
    def can_handle_file(self, file_path: str) -> bool:
        """Check if this transformer can handle the file type."""
        pass
```

### 4. srcML Transformer (New)

```python
# providers/transformation/srcml.py
import subprocess
import xml.etree.ElementTree as ET

class SrcMLTransformer(ISourceTransformer):
    """Transform C++ source using srcML."""
    
    def transform(self, modifications: List[SourceModification]) -> List[TransformedSource]:
        results = []
        for mod in modifications:
            # 1. Convert source to srcML
            srcml_xml = self._source_to_srcml(mod.file_path)
            
            # 2. Parse XML
            tree = ET.parse(srcml_xml)
            
            # 3. Find struct node
            struct_node = self._find_struct(tree, mod.struct_name)
            
            # 4. Reorder member nodes
            self._reorder_members(struct_node, mod.modifications)
            
            # 5. Convert back to source
            new_content = self._srcml_to_source(tree)
            
            results.append(TransformedSource(
                file_path=mod.file_path,
                original_content=self._read_file(mod.file_path),
                new_content=new_content,
                modifications=(mod,)
            ))
        
        return results
    
    def _source_to_srcml(self, file_path: str) -> str:
        """Convert C++ source to srcML XML."""
        result = subprocess.run(
            ['srcml', file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    
    def _srcml_to_source(self, tree: ET.ElementTree) -> str:
        """Convert srcML XML back to C++ source."""
        # Write XML to temp file
        temp_xml = '/tmp/temp.xml'
        tree.write(temp_xml)
        
        # Convert back
        result = subprocess.run(
            ['srcml', temp_xml],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    
    def _find_struct(self, tree: ET.ElementTree, struct_name: str) -> ET.Element:
        """Find struct/class node in srcML tree."""
        # srcML uses namespaces
        ns = {'src': 'http://www.srcML.org/srcML/src'}
        
        # Find all struct/class declarations
        for struct in tree.findall('.//src:struct', ns):
            name_elem = struct.find('.//src:name', ns)
            if name_elem is not None and name_elem.text == struct_name:
                return struct
        
        raise ValueError(f"Struct {struct_name} not found")
    
    def _reorder_members(self, struct_node: ET.Element, modifications: Tuple[Modification, ...]):
        """Reorder member declaration nodes."""
        ns = {'src': 'http://www.srcML.org/srcML/src'}
        
        # Find block (struct body)
        block = struct_node.find('.//src:block', ns)
        if block is None:
            return
        
        # Extract member declarations
        members = []
        for decl in block.findall('.//src:decl_stmt', ns):
            members.append(decl)
        
        # Remove all members
        for member in members:
            block.remove(member)
        
        # Re-add in new order based on modifications
        for mod in modifications:
            if mod.type == 'reorder_member':
                # Find member by name and re-add
                for member in members:
                    name_elem = member.find('.//src:name', ns)
                    if name_elem is not None and name_elem.text == mod.member_name:
                        block.append(member)
                        break
    
    def can_handle_file(self, file_path: str) -> bool:
        return file_path.endswith(('.cpp', '.h', '.hpp', '.cc', '.cxx'))
```

---

## Work Breakdown for Parallel Agent Execution

### Phase 1: Foundation (Sequential - Must Complete First)

#### Agent 1: Domain Models
**Task**: Create pure domain models  
**Files**: `domain/models.py`, `domain/padding_calculator.py`  
**Tests**: `tests/unit/test_domain/test_models.py`, `tests/unit/test_domain/test_padding_calculator.py`  
**Dependencies**: None  
**Deliverable**: Immutable data classes with pure functions

#### Agent 2: Pipeline Infrastructure
**Task**: Create pipeline base classes  
**Files**: `pipeline/stage.py`, `pipeline/pipeline.py`  
**Tests**: `tests/unit/test_pipeline/test_stage.py`, `tests/unit/test_pipeline/test_pipeline.py`  
**Dependencies**: Agent 1 (models)  
**Deliverable**: Generic pipeline runner with stage interface

### Phase 2: Provider Interfaces (Parallel)

#### Agent 3: Extraction Provider Interface
**Task**: Define IStructExtractor interface + mock  
**Files**: `providers/extraction/base.py`, `providers/extraction/mock.py`  
**Tests**: `tests/unit/test_providers/test_extraction_mock.py`  
**Dependencies**: Agent 1  
**Deliverable**: Interface + mock for testing

#### Agent 4: Transformation Provider Interface
**Task**: Define ISourceTransformer interface + mock  
**Files**: `providers/transformation/base.py`, `providers/transformation/mock.py`  
**Tests**: `tests/unit/test_providers/test_transformation_mock.py`  
**Dependencies**: Agent 1  
**Deliverable**: Interface + mock for testing

#### Agent 5: Application Provider Interface
**Task**: Define IChangeApplicator interface + mock  
**Files**: `providers/application/base.py`, `providers/application/mock.py`  
**Tests**: `tests/unit/test_providers/test_application_mock.py`  
**Dependencies**: Agent 1  
**Deliverable**: Interface + mock for testing

### Phase 3: Concrete Providers (Parallel)

#### Agent 6: Pahole Extractor
**Task**: Implement PaholeExtractor  
**Files**: `providers/extraction/pahole.py`  
**Tests**: `tests/integration/test_extraction/test_pahole.py`  
**Dependencies**: Agent 3  
**Deliverable**: Working pahole-based extractor

#### Agent 7: DWARF Extractor
**Task**: Implement DwarfExtractor (pyelftools)  
**Files**: `providers/extraction/dwarf.py`  
**Tests**: `tests/integration/test_extraction/test_dwarf.py`  
**Dependencies**: Agent 3  
**Deliverable**: Working pyelftools-based extractor

#### Agent 8: srcML Transformer
**Task**: Implement SrcMLTransformer  
**Files**: `providers/transformation/srcml.py`  
**Tests**: `tests/integration/test_transformation/test_srcml.py`  
**Dependencies**: Agent 4  
**Deliverable**: Working srcML-based transformer

#### Agent 9: Line Swap Transformer
**Task**: Implement LineSwapTransformer (migrate current code)  
**Files**: `providers/transformation/line_swap.py`  
**Tests**: `tests/integration/test_transformation/test_line_swap.py`  
**Dependencies**: Agent 4  
**Deliverable**: Working line-swap transformer

#### Agent 10: File Writer
**Task**: Implement DirectFileWriter  
**Files**: `providers/application/file_writer.py`  
**Tests**: `tests/unit/test_providers/test_file_writer.py`  
**Dependencies**: Agent 5  
**Deliverable**: Direct file modification

#### Agent 11: Patch Generator
**Task**: Implement GitPatchGenerator  
**Files**: `providers/application/patch_generator.py`  
**Tests**: `tests/unit/test_providers/test_patch_generator.py`  
**Dependencies**: Agent 5  
**Deliverable**: Git patch generation

### Phase 4: Pipeline Stages (Parallel)

#### Agent 12: Extraction Stage
**Task**: Implement ExtractionStage  
**Files**: `pipeline/extraction_stage.py`  
**Tests**: `tests/unit/test_pipeline/test_extraction_stage.py`  
**Dependencies**: Agent 2, Agent 3  
**Deliverable**: Stage that uses IStructExtractor

#### Agent 13: Analysis Stage
**Task**: Implement AnalysisStage with iterative size propagation  
**Files**: `pipeline/analysis_stage.py`, `domain/dependency_graph.py`, `domain/size_calculator.py`  
**Tests**: `tests/unit/test_pipeline/test_analysis_stage.py`, `tests/unit/test_domain/test_size_calculator.py`  
**Dependencies**: Agent 2, Agent 1  
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

**Key Insight**: Each struct's analysis uses the optimized sizes of its dependencies. This is NOT a single-pass analysis.

**Test Cases**:
- Simple struct (no dependencies)
- Nested struct (Inner → Outer)
- Multi-level nesting (A → B → C)
- Circular dependencies (should detect and skip)
- Struct becomes optimal after dependency optimization

#### Agent 14: Planning Stage
**Task**: Implement PlanningStage  
**Files**: `pipeline/planning_stage.py`, `domain/member_reorderer.py`  
**Tests**: `tests/unit/test_pipeline/test_planning_stage.py`  
**Dependencies**: Agent 2, Agent 1  
**Deliverable**: Generate optimization plans

#### Agent 15: Transformation Stage
**Task**: Implement TransformationStage  
**Files**: `pipeline/transformation_stage.py`  
**Tests**: `tests/unit/test_pipeline/test_transformation_stage.py`  
**Dependencies**: Agent 2, Agent 4  
**Deliverable**: Stage that uses ISourceTransformer

#### Agent 16: Application Stage
**Task**: Implement ApplicationStage  
**Files**: `pipeline/application_stage.py`  
**Tests**: `tests/unit/test_pipeline/test_application_stage.py`  
**Dependencies**: Agent 2, Agent 5  
**Deliverable**: Stage that uses IChangeApplicator

### Phase 5: CLI & Integration (Sequential)

#### Agent 17: CLI
**Task**: Implement CLI commands  
**Files**: `cli/main.py`, `cli/analyze_command.py`, `cli/optimize_command.py`  
**Tests**: `tests/integration/test_cli.py`  
**Dependencies**: All previous agents  
**Deliverable**: Working CLI with provider selection

#### Agent 18: End-to-End Tests
**Task**: Create comprehensive E2E tests  
**Files**: `tests/integration/test_end_to_end/`  
**Tests**: Multiple scenarios with different provider combinations  
**Dependencies**: All previous agents  
**Deliverable**: Full pipeline validation

---

## Testing Strategy

### Unit Tests (Fast, No I/O)
- Test domain logic in isolation
- Use mock providers
- Test each stage independently
- Target: <100ms per test, >90% coverage

### Integration Tests (With I/O)
- Test real providers (pahole, srcML)
- Use fixture files
- Test stage combinations
- Target: <5s per test

### End-to-End Tests (Full Pipeline)
- Test complete workflows
- Use real C++ projects
- Validate output correctness
- Target: <30s per test

---

## Migration Strategy

### Step 1: Create New Structure (Parallel)
- Agents 1-16 work in parallel on new code
- No changes to existing code
- New code lives alongside old code

### Step 2: Migrate CLI (Sequential)
- Agent 17 creates new CLI
- Old CLI remains functional
- Both CLIs coexist

### Step 3: Deprecate Old Code (Sequential)
- Mark old modules as deprecated
- Update documentation
- Remove old code after validation

---

## Provider Configuration

### Configuration File (YAML)

```yaml
# paddington.yaml
pipeline:
  extraction:
    provider: pahole  # or: dwarf, custom
    options:
      cache_dir: .paddington_cache
      timeout: 300
  
  transformation:
    provider: srcml  # or: line_swap, custom
    options:
      preserve_formatting: true
  
  application:
    provider: patch  # or: file_writer, custom
    options:
      patch_dir: ./patches
      commit_message_template: |
        refactor: Optimize padding for {struct_name}
        
        Reorder members from largest to smallest.
        Saves {padding_saved} bytes per instance.
```

### CLI Usage

```bash
# Use default providers (from config)
python -m paddington optimize build/

# Override extraction provider
python -m paddington optimize build/ --extractor pahole

# Override transformation provider
python -m paddington optimize build/ --transformer srcml

# Override application provider
python -m paddington optimize build/ --applicator file-writer

# Use all custom providers
python -m paddington optimize build/ \
  --extractor pahole \
  --transformer srcml \
  --applicator patch
```

---

## Success Criteria

### Testability
- [ ] 100% of domain logic has unit tests
- [ ] All providers have integration tests
- [ ] E2E tests cover main workflows
- [ ] Tests run in <5 minutes total

### Maintainability
- [ ] Clear separation of concerns
- [ ] Each module has single responsibility
- [ ] Directory structure reflects intent
- [ ] Documentation for each component

### Flexibility
- [ ] Can swap extraction provider without code changes
- [ ] Can swap transformation provider without code changes
- [ ] Can add new providers by implementing interface
- [ ] Configuration-driven provider selection

### Parallelizability
- [ ] Agents can work independently on different components
- [ ] No circular dependencies between agents
- [ ] Clear interfaces enable parallel development
- [ ] Integration happens at well-defined boundaries

---

## Timeline Estimate

- **Phase 1**: 2 agents × 2 days = 4 agent-days
- **Phase 2**: 3 agents × 1 day = 3 agent-days (parallel)
- **Phase 3**: 6 agents × 3 days = 18 agent-days (parallel)
- **Phase 4**: 5 agents × 2 days = 10 agent-days (parallel)
- **Phase 5**: 2 agents × 3 days = 6 agent-days (sequential)

**Total**: 41 agent-days  
**Wall time** (with parallelization): ~12 days

---

## Next Steps

1. **Review this plan** - Validate approach and architecture
2. **Set up project structure** - Create new directory layout
3. **Assign agents** - Distribute work based on dependencies
4. **Create tracking board** - Monitor progress per agent
5. **Begin Phase 1** - Start with foundation work
