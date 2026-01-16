# Refactoring Plan: Simplify CLI and Expand E2E Tests

**Date**: 2026-01-16 23:30  
**Goal**: Simplify CLI (remove analyze, make optimize default) and add comprehensive e2e tests

---

## Part 1: CLI Simplification

### Current State (Confusing)
- Two commands: `analyze` and `optimize`
- `analyze` is just dry-run optimization
- Redundant functionality

### New Design (Simple)
- Single command: `optimize` (default)
- `--dry-run` flag for analysis-only mode
- Cleaner, more intuitive

### Changes Needed

#### 1. Update Requirements
- Remove FR-1.3.1 (Analysis Mode as separate command)
- Update FR-1.3.2 (Dry-run is now default for optimize)
- Clarify that analyze = optimize --dry-run

#### 2. Update Architecture
- Remove `implementation/user_interactions/analyze.py`
- Update `implementation/user_interactions/optimize.py` to handle dry-run
- Update `__main__.py` to have optimize as default command

#### 3. Update Tests
- Remove `tests/end_to_end/test_analyze_workflow.py`
- Update `tests/end_to_end/test_optimize_workflow.py` to include dry-run tests
- Rename to `test_e2e_optimize.py`

---

## Part 2: Comprehensive E2E Test Suite

### Base E2E Test Framework

Create `tests/end_to_end/base_e2e.py`:
```python
class BaseE2ETest:
    \"\"\"Base class for e2e tests with common utilities.\"\"\"
    
    def compile_cpp(self, code: str, tmpdir: Path) -> Path:
        \"\"\"Compile C++ code to .o file.\"\"\"
        pass
    
    def run_optimize(self, obj_file: Path, **kwargs) -> subprocess.CompletedProcess:
        \"\"\"Run optimize command.\"\"\"
        pass
    
    def assert_success(self, result):
        \"\"\"Assert command succeeded.\"\"\"
        pass
```

### E2E Test Categories

#### Category 1: Basic Functionality (5 tests)
- `test_e2e_basic.py`
  - test_simple_struct_dry_run
  - test_simple_struct_with_patch
  - test_simple_struct_with_file_output
  - test_min_savings_threshold
  - test_help_documentation

#### Category 2: Access Modifiers (6 tests)
- `test_e2e_access_modifiers.py`
  - test_preserve_strategy_public_private
  - test_preserve_strategy_multiple_sections
  - test_split_strategy_optimal_ordering
  - test_split_strategy_per_member_modifiers
  - test_ignore_strategy_breaks_encapsulation
  - test_struct_only_no_class_modifiers

#### Category 3: Dependencies (5 tests)
- `test_e2e_dependencies.py`
  - test_nested_struct_two_levels
  - test_nested_struct_three_levels
  - test_shared_dependency_multiple_parents
  - test_circular_dependency_detection
  - test_size_propagation_through_chain

#### Category 4: Templates (7 tests)
- `test_e2e_templates.py`
  - test_template_with_primitive_types
  - test_template_with_struct_types
  - test_template_multiple_instantiations
  - test_template_partial_specialization
  - test_template_with_non_type_params
  - test_template_nested_in_struct
  - test_variadic_template

#### Category 5: Preprocessor & Macros (6 tests)
- `test_e2e_preprocessor.py`
  - test_ifdef_in_struct_definition
  - test_macro_defined_members
  - test_conditional_compilation
  - test_pragma_pack
  - test_attribute_aligned
  - test_mixed_preprocessor_and_code

#### Category 6: Complex Scenarios (8 tests)
- `test_e2e_complex.py`
  - test_multiple_files_same_struct
  - test_header_and_implementation_split
  - test_anonymous_struct_in_union
  - test_bitfields
  - test_inheritance_single
  - test_inheritance_multiple
  - test_virtual_functions_vtable
  - test_large_struct_many_members

#### Category 7: Edge Cases (6 tests)
- `test_e2e_edge_cases.py`
  - test_empty_struct
  - test_single_member_struct
  - test_already_optimal_struct
  - test_zero_size_members
  - test_padding_only_at_end
  - test_no_padding_possible

#### Category 8: Real World (5 tests)
- `test_e2e_real_world.py`
  - test_systemc_keywords
  - test_custom_allocators
  - test_placement_new
  - test_extern_c_structs
  - test_packed_structs

**Total: 48 e2e tests**

---

## Part 3: Requirements Updates

### New Requirements

#### FR-1.7: Template Handling
**Description**: System shall handle C++ templates appropriately.

**Strategy**:
- Optimize template instantiations (concrete types)
- Skip template definitions (T is unknown size)
- Each instantiation optimized independently

**Example**:
```cpp
template<typename T>
struct Container {
    char flag;
    T value;     // Skip - unknown size
    int count;
};

// Optimize these instantiations:
Container<int> c1;     // Optimize: int is 4 bytes
Container<double> c2;  // Optimize: double is 8 bytes
```

#### FR-1.8: Preprocessor Handling
**Description**: System shall handle preprocessor directives safely.

**Strategy**:
- Skip structs with #ifdef/#ifndef in member definitions
- Skip structs with macro-defined members
- Report skipped structs with reason

#### FR-1.9: Complex C++ Features
**Description**: System shall handle or skip complex C++ features.

**Handle**:
- Inheritance (optimize derived class members only)
- Multiple files (same struct in header + implementation)

**Skip**:
- Bitfields (complex alignment rules)
- Unions (overlapping members)
- Anonymous structs (hard to identify)
- Virtual functions (vtable affects layout)

---

## Agent Tasks

### Agent 20: Update Requirements
- Update REQUIREMENTS.md with CLI simplification
- Add template handling requirements
- Add preprocessor handling requirements
- Add complex C++ feature requirements

### Agent 21: Update Architecture Docs
- Update PIPELINE_STAGES_EXPLAINED.md
- Update FINAL_DIRECTORY_STRUCTURE.md
- Update REFACTORING_PLAN_V2.md

### Agent 22: Simplify CLI
- Remove analyze.py
- Update optimize.py to handle --dry-run (default: true)
- Update __main__.py to have optimize as default
- Update help text

### Agent 23: Update E2E Tests
- Create base_e2e.py with BaseE2ETest
- Update test_optimize_workflow.py to use base class
- Add dry-run tests

### Agent 24-31: Create New E2E Test Suites (Parallel)
- Agent 24: test_e2e_basic.py (5 tests)
- Agent 25: test_e2e_access_modifiers.py (6 tests)
- Agent 26: test_e2e_dependencies.py (5 tests)
- Agent 27: test_e2e_templates.py (7 tests)
- Agent 28: test_e2e_preprocessor.py (6 tests)
- Agent 29: test_e2e_complex.py (8 tests)
- Agent 30: test_e2e_edge_cases.py (6 tests)
- Agent 31: test_e2e_real_world.py (5 tests)

**Total new e2e tests: 48**

---

## Execution Plan

1. **Verify current state** ✅ (done)
2. **Update documentation** (Agents 20-21)
3. **Simplify CLI** (Agent 22)
4. **Update existing e2e** (Agent 23)
5. **Create new e2e suites** (Agents 24-31, parallel)
6. **Run all tests** and verify 100% passing
7. **Commit each agent separately**

---

## Expected Final State

- **CLI**: Single `optimize` command with `--dry-run` flag
- **E2E Tests**: 55 tests (7 existing + 48 new)
- **Total Tests**: 246 tests (198 unit + 48 e2e)
- **Documentation**: Updated with new requirements
- **All tests passing**: 100%
