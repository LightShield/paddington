# Requirements to Tests Mapping

**Purpose**: Map each requirement to test(s) that verify it

---

## Functional Requirements

### FR-1.1: Core Functionality

| Requirement | Test(s) | Status |
|-------------|---------|--------|
| FR-1.1.1: Struct Padding Detection | test_e2e_basic::test_simple_struct_dry_run | ✅ |
| FR-1.1.2: Member Reordering | test_e2e_basic::test_simple_struct_with_patch | ✅ |
| FR-1.1.3: Source Code Transformation | **MISSING** | ❌ |
| FR-1.1.4: Dependency-Aware Optimization | test_e2e_dependencies::test_nested_struct_two_levels | ✅ |

### FR-1.2: User Control & Directives

| Requirement | Test(s) | Status |
|-------------|---------|--------|
| FR-1.2.1: Opt-Out Markers (Struct-Level) | **MISSING** | ❌ |
| FR-1.2.2: Opt-Out Markers (Member-Level) | **MISSING** | ❌ |
| FR-1.2.3: Opt-Out Markers (Region-Level) | **MISSING** | ❌ |
| FR-1.2.4: Minimum Savings Threshold | test_e2e_basic::test_min_savings_threshold | ✅ |

### FR-1.3: Output Modes

| Requirement | Test(s) | Status |
|-------------|---------|--------|
| FR-1.3.2: Dry-Run Mode (Default) | test_e2e_basic::test_simple_struct_dry_run | ✅ |
| FR-1.3.3: Direct Modification Mode | test_e2e_basic::test_simple_struct_with_file_output | ✅ |
| FR-1.3.4: Patch Generation Mode | test_e2e_basic::test_simple_struct_with_patch | ✅ |

### FR-1.4: Filtering & Selection

| Requirement | Test(s) | Status |
|-------------|---------|--------|
| FR-1.4.1: File Pattern Filtering | **MISSING** | ❌ |
| FR-1.4.2: Struct Name Filtering | **MISSING** | ❌ |

### FR-1.7-1.9: Advanced Features

| Requirement | Test(s) | Status |
|-------------|---------|--------|
| FR-1.7: Template Handling | test_e2e_verification::test_nested_struct_with_size_propagation (partial) | ⚠️ |
| FR-1.8: Preprocessor Handling | **MISSING** | ❌ |
| FR-1.9: Complex C++ Features | test_e2e_access_modifiers (partial) | ⚠️ |

### FR-1.8-1.9: Validation & Reporting

| Requirement | Test(s) | Status |
|-------------|---------|--------|
| FR-1.8.1: Build Verification | **MISSING** | ❌ |
| FR-1.8.2: Syntax Validation | **MISSING** | ❌ |
| FR-1.9.1: Progress Reporting | **MISSING** | ❌ |
| FR-1.9.2: Summary Statistics | **MISSING** | ❌ |
| FR-1.9.3: Verbosity Levels | **MISSING** | ❌ |
| FR-1.9.4: Configuration Logging | **MISSING** | ❌ |
| FR-1.9.5: Skip Reason Reporting | **MISSING** | ❌ |

---

## Missing E2E Tests (Need to Create)

### High Priority (P0)

1. **test_e2e_directives.py** (FR-1.2.1, FR-1.2.2, FR-1.2.3)
   - test_paddington_ignore_marker
   - test_paddington_lock_marker
   - test_paddington_off_on_markers

2. **test_e2e_filtering.py** (FR-1.4.1, FR-1.4.2)
   - test_include_pattern
   - test_exclude_pattern
   - test_struct_name_filter

3. **test_e2e_transformation_verification.py** (FR-1.1.3)
   - test_member_declarations_reordered
   - test_constructor_initializer_lists_updated
   - test_aggregate_initializations_updated
   - test_smart_pointer_calls_updated

4. **test_e2e_templates_proper.py** (FR-1.7)
   - test_template_instantiation_optimized
   - test_template_definition_skipped
   - test_multiple_instantiations_independent

5. **test_e2e_preprocessor_proper.py** (FR-1.8)
   - test_ifdef_struct_skipped
   - test_macro_members_handled
   - test_pragma_pack_skipped

6. **test_e2e_complex_cpp.py** (FR-1.9)
   - test_inheritance_derived_members_only
   - test_bitfields_skipped
   - test_unions_skipped
   - test_virtual_functions_vtable_handled

7. **test_e2e_reporting.py** (FR-1.9.1-1.9.5)
   - test_progress_reporting
   - test_summary_statistics
   - test_verbosity_levels
   - test_skip_reason_reporting

8. **test_e2e_validation.py** (FR-1.8.1, FR-1.8.2)
   - test_build_verification
   - test_syntax_validation

---

## Test Annotation Format

Each test should include a docstring linking to requirements:

```python
@pytest.mark.e2e
def test_paddington_ignore_marker(self, tmp_path):
    \"\"\"Test paddington-ignore marker skips struct.
    
    Verifies: FR-1.2.1 (Opt-Out Markers - Struct Level)
    \"\"\"
    test_case = E2ETestCase(...)
```

---

## Requirements File Updates

Add test references to each requirement:

```markdown
#### FR-1.2.1: Opt-Out Markers (Struct-Level)
**Description**: Users shall be able to exclude specific structs from optimization.

**Test**: test_e2e_directives.py::test_paddington_ignore_marker

**Acceptance Criteria**:
- Detect `paddington-ignore` comment before struct definition
...
```

---

## Summary

**Current Coverage**: 13 e2e tests covering ~15 of 45 requirements (33%)  
**Missing**: ~30 requirements without e2e tests  
**Needed**: ~30 new e2e tests  

**Next**: Create 8 new test files with ~30 tests total to achieve full requirement coverage.
