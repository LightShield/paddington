# Proper E2E Test Structure

## Problem with Current E2E Tests

Current tests only check:
```python
result = self.run_optimize(obj_file)
self.assert_success(result)  # Only checks exit code == 0
```

This is a **false positive** - tests pass even when:
- ❌ No structs extracted
- ❌ No optimization performed
- ❌ No patches generated
- ❌ No source modified

## Proper E2E Test Structure

### 1. Define Complete Test Case

```python
test_case = E2ETestCase(
    name="simple_struct_optimization",
    
    # INPUT: C++ code
    cpp_code="""
    struct Simple {
        char a;      // 1 byte
        int b;       // 4 bytes
        char c;      // 1 byte
    };
    int main() { return 0; }
    """,
    
    # FLAGS: paddingTON options
    flags={
        'apply': True,
        'output': 'file',
        'extractor': 'dwarf',
        'transformer': 'line-swap'
    },
    
    # EXPECTED: What should happen
    expected_structs=[
        StructExpectation(
            name="Simple",
            size_before=12,              # Measured from DWARF
            size_after=8,                # After optimization
            member_order_before=['a', 'b', 'c'],
            member_order_after=['b', 'a', 'c'],  # int first
            padding_saved=4,
            should_optimize=True
        )
    ],
    
    should_succeed=True,
    expected_output_contains=["APPLYING CHANGES"],
    expected_patches_count=None
)
```

### 2. Test Execution Flow

```python
def run_test_case(self, test_case, tmp_path):
    # Step 1: Compile C++ code
    cpp_file = tmp_path / "test.cpp"
    cpp_file.write_text(test_case.cpp_code)
    obj_file = self.compile_cpp(cpp_file)
    
    # Step 2: Extract structs from DWARF (BEFORE optimization)
    structs_before = self.extract_structs_from_dwarf(obj_file)
    
    # Step 3: VERIFY expected structs exist with correct sizes
    for expected in test_case.expected_structs:
        struct_info = structs_before.get(expected.name)
        assert struct_info is not None, f"Struct {expected.name} not found"
        assert struct_info['size'] == expected.size_before, \
            f"Size mismatch: expected {expected.size_before}, got {struct_info['size']}"
    
    # Step 4: Run paddingTON
    result = self.run_optimize(obj_file, **test_case.flags)
    
    # Step 5: VERIFY command succeeded
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    # Step 6: VERIFY output contains expected text
    for text in test_case.expected_output_contains:
        assert text in result.stdout
    
    # Step 7: If --apply, VERIFY source was modified
    if test_case.flags.get('apply'):
        modified_content = cpp_file.read_text()
        
        # VERIFY member order changed
        for expected in test_case.expected_structs:
            if expected.should_optimize:
                order_correct = self.verify_member_order_in_source(
                    modified_content,
                    expected.name,
                    expected.member_order_after
                )
                assert order_correct, f"Member order incorrect for {expected.name}"
        
        # Step 8: Recompile and VERIFY size changed
        obj_file_after = self.compile_cpp(cpp_file, "test_after.o")
        structs_after = self.extract_structs_from_dwarf(obj_file_after)
        
        for expected in test_case.expected_structs:
            if expected.should_optimize:
                struct_info = structs_after.get(expected.name)
                assert struct_info['size'] == expected.size_after, \
                    f"Size after: expected {expected.size_after}, got {struct_info['size']}"
    
    # Step 9: VERIFY patches generated (if patch mode)
    if test_case.flags.get('output') == 'patch':
        patch_dir = Path(test_case.flags['patch_dir'])
        if patch_dir.exists():
            patches = list(patch_dir.glob("*.patch"))
            assert len(patches) == test_case.expected_patches_count
```

## What Gets Verified

### Before Optimization
- ✅ Struct exists in DWARF
- ✅ Struct size matches expected (e.g., 12 bytes)
- ✅ Member order in source matches expected

### During Optimization
- ✅ Command runs successfully
- ✅ Output contains expected text ("DRY-RUN" or "APPLYING CHANGES")
- ✅ Correct number of structs processed

### After Optimization (if --apply)
- ✅ Source file was modified
- ✅ Member order changed to expected order
- ✅ Recompiled struct has expected new size (e.g., 8 bytes)
- ✅ Padding was actually reduced (12 → 8 = 4 bytes saved)

### Patch Mode
- ✅ Correct number of patches generated
- ✅ Patches contain expected changes
- ✅ APPLY_ORDER.txt created

## Example Test Case

### Input
```cpp
struct Simple {
    char a;      // 1 byte
    int b;       // 4 bytes
    char c;      // 1 byte
};
// Size: 12 bytes (6 bytes padding)
```

### Expected Output
```cpp
struct Simple {
    int b;       // 4 bytes (largest first)
    char a;      // 1 byte
    char c;      // 1 byte
};
// Size: 8 bytes (2 bytes padding)
// Saved: 4 bytes
```

### Verification
- ✅ Size before: 12 bytes (from DWARF)
- ✅ Size after: 8 bytes (from DWARF after recompile)
- ✅ Member order: ['b', 'a', 'c'] (verified in source)
- ✅ Padding saved: 4 bytes (12 - 8)

## Current Status

**Problem**: DwarfExtractor returns 0 structs, so no optimization happens.

**Current tests**: Pass because they only check "command runs", not "optimization works".

**Proper tests**: Would FAIL because they verify actual optimization results.

## Next Steps

1. Fix DwarfExtractor to actually extract structs
2. Replace current weak e2e tests with proper verification tests
3. All tests should use E2ETestCase with StructExpectation
4. Verify sizes, member order, padding reduction

This ensures tests actually verify the system works, not just that it doesn't crash.
