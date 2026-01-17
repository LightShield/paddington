# Plan: Complete Requirements Test Coverage

**Goal**: Create e2e tests for all 45 requirements (currently 15/45 covered)

---

## Agent Tasks (8 agents, parallel execution)

### Agent 36: Directives Tests (FR-1.2.1, FR-1.2.2, FR-1.2.3)
**File**: tests/end_to_end/test_e2e_directives.py
**Tests**: 3 tests
1. test_paddington_ignore_marker - Struct with `// paddington-ignore` is skipped
2. test_paddington_lock_marker - Member with `// paddington-lock` stays in place
3. test_paddington_off_on_markers - Region between markers is skipped

### Agent 37: Filtering Tests (FR-1.4.1, FR-1.4.2)
**File**: tests/end_to_end/test_e2e_filtering.py
**Tests**: 3 tests
1. test_include_pattern - Only process files matching --include pattern
2. test_exclude_pattern - Skip files matching --exclude pattern
3. test_struct_name_filter - Only optimize specific struct names

### Agent 38: Transformation Verification (FR-1.1.3)
**File**: tests/end_to_end/test_e2e_transformation_verification.py
**Tests**: 4 tests
1. test_member_declarations_reordered - Verify struct definition changed
2. test_constructor_initializer_lists_updated - Verify init lists reordered
3. test_aggregate_initializations_updated - Verify {a,b,c} reordered
4. test_smart_pointer_calls_updated - Verify make_unique args reordered

### Agent 39: Templates Proper (FR-1.7)
**File**: tests/end_to_end/test_e2e_templates_proper.py
**Tests**: 4 tests
1. test_template_instantiation_optimized - Container<int> is optimized
2. test_template_definition_skipped - template<typename T> is skipped
3. test_multiple_instantiations_independent - Each instantiation optimized separately
4. test_template_with_different_sizes - Container<char> vs Container<double>

### Agent 40: Preprocessor Proper (FR-1.8)
**File**: tests/end_to_end/test_e2e_preprocessor_proper.py
**Tests**: 4 tests
1. test_ifdef_struct_skipped - Struct with #ifdef is skipped
2. test_macro_members_handled - Macro-defined members handled
3. test_pragma_pack_skipped - #pragma pack structs skipped
4. test_conditional_compilation - #if/#elif handled

### Agent 41: Complex C++ Proper (FR-1.9)
**File**: tests/end_to_end/test_e2e_complex_cpp_proper.py
**Tests**: 5 tests
1. test_inheritance_derived_members_only - Only derived members reordered
2. test_bitfields_skipped - Bitfield structs skipped
3. test_unions_skipped - Unions skipped
4. test_virtual_functions_vtable - Vtable pointer handled
5. test_anonymous_struct_skipped - Anonymous structs skipped

### Agent 42: Reporting Tests (FR-1.9.1-1.9.5)
**File**: tests/end_to_end/test_e2e_reporting.py
**Tests**: 5 tests
1. test_progress_reporting - Progress shown during processing
2. test_summary_statistics - Summary at end (structs analyzed, optimized, skipped)
3. test_verbosity_levels - -v, -vv, -vvv output different levels
4. test_skip_reason_reporting - Skipped structs show reasons
5. test_output_format - Output is parseable

### Agent 43: Validation Tests (FR-1.8.1, FR-1.8.2)
**File**: tests/end_to_end/test_e2e_validation.py
**Tests**: 3 tests
1. test_build_verification - --verify flag runs build after optimization
2. test_syntax_validation - Invalid C++ is detected
3. test_file_permissions - Read-only files are skipped

---

## Test Format

All tests must:
1. Use E2ETestCase with StructExpectation
2. Include docstring with requirement reference
3. Mark with @pytest.mark.e2e
4. Inherit from BaseE2ETest

Example:
```python
@pytest.mark.e2e
def test_paddington_ignore_marker(self, tmp_path):
    \"\"\"Test paddington-ignore marker skips struct.
    
    Verifies: FR-1.2.1 (Opt-Out Markers - Struct Level)
    \"\"\"
    test_case = E2ETestCase(
        name="paddington_ignore",
        cpp_code=\"\"\"
        // paddington-ignore
        struct DontTouch {
            char a;
            int b;
        };
        int main() { DontTouch d; return 0; }
        \"\"\",
        flags={'extractor': 'dwarf'},
        expected_structs=[
            StructExpectation(
                name="DontTouch",
                size_before=8,
                size_after=8,
                member_order_before=['a', 'b'],
                member_order_after=['a', 'b'],
                padding_saved=0,
                should_optimize=False,
                skip_reason="marked ignore"
            )
        ],
        should_succeed=True,
        expected_output_contains=["DRY-RUN", "skipped"]
    )
    self.run_test_case(test_case, tmp_path)
```

---

## Expected Outcome

- **30 new e2e tests** (8 files × ~4 tests each)
- **Total: 43 e2e tests** (13 existing + 30 new)
- **Total: 242 tests** (199 unit + 43 e2e)
- **100% requirement coverage**

---

## Agent Instructions

Each agent should:
1. Create test file in tests/end_to_end/
2. Inherit from BaseE2ETest
3. Use E2ETestCase format
4. Add requirement reference in docstring
5. Ensure structs are used in main() (for DWARF)
6. Run tests (may fail if feature not implemented - that's OK for TDD)
7. Do NOT commit

Tests may fail - that's expected for TDD. We're creating tests first, then implementing features.
