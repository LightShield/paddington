# Test Family Expansion Plan

**Current**: 40 e2e tests (1-2 per requirement)  
**Target**: 150+ e2e tests (3-10 per requirement)  
**Gap**: 110 tests needed

---

## Requirements Needing Test Families

### FR-1.1.2: Member Reordering (Currently: 1 test, Need: 10 tests)

**Current**:
- test_simple_struct_with_patch

**Needed**:
1. test_reorder_two_members - Minimal case
2. test_reorder_three_members - Basic case
3. test_reorder_ten_members - Many members
4. test_reorder_same_size_members - Stable sort
5. test_reorder_with_arrays - Array members
6. test_reorder_with_pointers - Pointer members
7. test_reorder_preserve_strategy - Within sections
8. test_reorder_split_strategy - Per-member modifiers
9. test_reorder_ignore_strategy - Across sections
10. test_reorder_already_optimal - No change

### FR-1.1.3: Source Code Transformation (Currently: 1 test, Need: 8 tests)

**Current**:
- test_simple_struct_with_file_output

**Needed**:
1. test_transform_struct_definition - Member declarations
2. test_transform_constructor_init_list - Initializer lists
3. test_transform_aggregate_init - {a, b, c}
4. test_transform_smart_pointer - make_unique args
5. test_transform_multiple_constructors - All constructors updated
6. test_transform_inline_constructor - In-class constructor
7. test_transform_outline_constructor - Out-of-class constructor
8. test_transform_preserves_comments - Comments maintained

### FR-1.1.4: Dependency-Aware Optimization (Currently: 2 tests, Need: 8 tests)

**Current**:
- test_nested_struct_two_levels
- test_shared_dependency

**Needed**:
1. test_dependency_three_levels - A → B → C
2. test_dependency_four_levels - Deep nesting
3. test_dependency_diamond - A → B,C → D
4. test_dependency_size_propagation - Verify sizes update
5. test_dependency_circular_pointers - A ↔ B via pointers
6. test_dependency_self_reference - Struct contains pointer to self
7. test_dependency_mutual_recursion - A → B → A
8. test_dependency_optimization_order - Leaves first

### FR-1.2.1: Opt-Out Markers Struct (Currently: 1 test, Need: 5 tests)

**Current**:
- test_paddington_ignore_marker

**Needed**:
1. test_ignore_single_struct - One struct ignored
2. test_ignore_multiple_structs - Multiple ignored
3. test_ignore_with_comment_style - // vs /* */
4. test_ignore_case_insensitive - PADDINGTON-IGNORE
5. test_ignore_with_whitespace - Spaces around marker

### FR-1.7: Template Handling (Currently: 4 tests, Need: 12 tests)

**Current**:
- test_template_instantiation_optimized
- test_template_definition_skipped
- test_multiple_instantiations_independent
- test_template_with_different_sizes

**Needed**:
1. test_template_with_primitive_types - int, char, double
2. test_template_with_struct_types - Custom types
3. test_template_with_pointer_types - T*
4. test_template_with_reference_types - T&
5. test_template_partial_specialization - template<> for specific type
6. test_template_full_specialization - Completely specialized
7. test_template_variadic - template<typename... Args>
8. test_template_non_type_param - template<int N>
9. test_template_nested - Template inside struct
10. test_template_dependent_types - typename T::value_type
11. test_template_sfinae - Enable_if patterns
12. test_template_concepts - C++20 concepts

---

## Prioritization

### P0 (Critical - Implement Now)
- FR-1.1.2: Member Reordering (10 tests)
- FR-1.1.3: Source Transformation (8 tests)
- FR-1.1.4: Dependencies (8 tests)

### P1 (Important - Next Sprint)
- FR-1.2.x: User Directives (15 tests)
- FR-1.7: Templates (12 tests)
- FR-1.8: Preprocessor (15 tests)

### P2 (Nice to Have - Future)
- FR-1.4.x: Filtering (10 tests)
- FR-1.9.x: Reporting (15 tests)
- FR-1.9: Complex C++ (20 tests)

---

## Implementation Strategy

### Approach 1: Expand Existing Test Files
- Add tests to existing test_e2e_*.py files
- Group by requirement
- Maintain file organization

### Approach 2: Create Test Family Files
- test_e2e_member_reordering_family.py (10 tests for FR-1.1.2)
- test_e2e_transformation_family.py (8 tests for FR-1.1.3)
- More granular organization

### Recommendation: Approach 1
- Keep existing file structure
- Add tests to appropriate files
- Use descriptive test names
- Group with comments

---

## Example: Expanded Test File

```python
# tests/end_to_end/test_e2e_member_reordering.py

class TestMemberReordering(BaseE2ETest):
    \"\"\"Test family for FR-1.1.2 (Member Reordering).\"\"\"
    
    # Basic cases
    @pytest.mark.e2e
    def test_reorder_two_members(self, tmp_path):
        \"\"\"Minimal case: 2 members.
        
        Verifies: FR-1.1.2 (Member Reordering - Basic)
        \"\"\"
        ...
    
    @pytest.mark.e2e
    def test_reorder_three_members(self, tmp_path):
        \"\"\"Simple case: 3 members.
        
        Verifies: FR-1.1.2 (Member Reordering - Basic)
        \"\"\"
        ...
    
    # Type variations
    @pytest.mark.e2e
    def test_reorder_with_arrays(self, tmp_path):
        \"\"\"Array members.
        
        Verifies: FR-1.1.2 (Member Reordering - Arrays)
        \"\"\"
        ...
    
    # Strategy variations
    @pytest.mark.e2e
    def test_reorder_preserve_strategy(self, tmp_path):
        \"\"\"Preserve access modifiers.
        
        Verifies: FR-1.1.2 (Member Reordering - Preserve Strategy)
        \"\"\"
        ...
    
    # Edge cases
    @pytest.mark.e2e
    def test_reorder_already_optimal(self, tmp_path):
        \"\"\"No change when optimal.
        
        Verifies: FR-1.1.2 (Member Reordering - Edge Case)
        \"\"\"
        ...
```

---

## Summary

**Current**: 40 tests, baseline coverage (1-2 per requirement)  
**Needed**: 110 more tests for exhaustive coverage (3-10 per requirement)  
**Approach**: Test families grouped by requirement  
**Priority**: Core functionality first (P0), then advanced features (P1, P2)

Each requirement should have a **test family** that covers:
- Happy path
- Edge cases
- Error cases
- Variations

This ensures **robust, reliable, comprehensive** testing.
