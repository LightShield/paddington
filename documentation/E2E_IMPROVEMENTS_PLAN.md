# E2E Test Improvements Plan

**Issue**: Current e2e tests only verify commands don't crash, not that optimization actually works correctly.

---

## What's Missing

### 1. Verification of Optimization Results
Current:
```python
result = self.run_optimize(obj_file)
self.assert_success(result)  # Only checks exit code!
```

Should verify:
- Struct size before vs after
- Member order changed correctly
- Padding actually reduced
- Source code modified correctly

### 2. Multi-File Scenarios
Missing tests for:
- Header (.h) + Implementation (.cpp) split
- Struct definition in .h, usage in .cpp
- Constructor in .h, implementation in .cpp
- Multiple .cpp files using same struct

### 3. Source Code Verification
Missing verification for:
- Member declarations reordered
- Constructor initializer lists reordered
- Aggregate initializations reordered
- Smart pointer calls updated
- Access modifiers preserved/split/ignored correctly

---

## Enhanced BaseE2ETest

Add methods:
```python
def get_struct_size_from_dwarf(self, obj_file, struct_name) -> int:
    \"\"\"Extract struct size from DWARF info.\"\"\"
    pass

def verify_member_order(self, source_file, struct_name, expected_order):
    \"\"\"Verify members are in expected order.\"\"\"
    pass

def verify_padding_reduced(self, obj_before, obj_after, struct_name):
    \"\"\"Verify padding was actually reduced.\"\"\"
    pass

def compile_and_get_size(self, code, struct_name) -> int:
    \"\"\"Compile code and return struct size.\"\"\"
    pass
```

---

## New E2E Test Categories

### Category 1: Verification Tests (test_e2e_verification.py)
1. test_verify_size_reduction - Measure before/after size
2. test_verify_member_reordering - Check member order changed
3. test_verify_padding_calculation - Verify padding reduced
4. test_verify_no_change_when_optimal - Already optimal struct unchanged
5. test_verify_access_modifiers_preserved - Access sections maintained

### Category 2: Multi-File Tests (test_e2e_multi_file.py)
1. test_header_and_cpp_split - Struct in .h, usage in .cpp
2. test_multiple_cpp_files - Multiple .cpp using same struct
3. test_constructor_in_header - Constructor defined in .h
4. test_constructor_in_cpp - Constructor implemented in .cpp
5. test_inline_vs_outline_methods - Inline in .h, outline in .cpp

### Category 3: Source Transformation Tests (test_e2e_transformation.py)
1. test_member_declaration_reordering - Verify declarations reordered
2. test_constructor_initializer_list_reordering - Verify init lists updated
3. test_aggregate_initialization_reordering - Verify {a, b, c} updated
4. test_smart_pointer_argument_reordering - Verify make_unique args updated
5. test_access_modifier_preservation - Verify public/private sections maintained
6. test_access_modifier_splitting - Verify per-member modifiers added

---

## Implementation Plan

### Agent 32: Enhance BaseE2ETest
- Add verification methods
- Add size extraction from DWARF
- Add source code parsing utilities
- Add before/after comparison

### Agent 33: Create Verification E2E Tests
- test_e2e_verification.py with 5 tests
- Verify actual optimization results
- Measure size reduction
- Check member order

### Agent 34: Create Multi-File E2E Tests
- test_e2e_multi_file.py with 5 tests
- Test .h + .cpp scenarios
- Test multiple files
- Test constructor split

### Agent 35: Create Transformation E2E Tests
- test_e2e_transformation.py with 6 tests
- Verify source code changes
- Check initializer lists
- Check aggregate initializations

---

## Expected Outcome

**Total E2E Tests**: 68 (52 existing + 16 new)
**Total Tests**: 266 (198 unit + 68 e2e)

All tests verify actual behavior, not just "doesn't crash".
