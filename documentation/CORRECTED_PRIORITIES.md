# Implementation Priority - Corrected

## P0 (Critical - Core Functionality)

These are needed for the system to actually optimize structs:

### 1. Member Extraction Completion
**Status**: Partially working
**Issue**: MachoExtractor extracts members but may miss some types
**Tests failing**: Some member reordering tests
**Priority**: HIGH

### 2. Planning Stage Enhancement
**Status**: Basic implementation
**Issue**: Creates modifications but may not handle all cases
**Tests failing**: Some transformation tests
**Priority**: HIGH

### 3. Transformation Stage - Struct Definition
**Status**: Needs implementation
**Issue**: LineSwapTransformer doesn't actually reorder members in source
**Tests failing**: Most transformation tests
**Priority**: CRITICAL

---

## P1 (Important - Enhanced Functionality)

### 4. Constructor Initializer List Reordering
**What**: Reorder `Data() : a(x), b(y) {}` to match new member order
**Why P1**: Doesn't break compilation, just a warning
**Tests failing**: Constructor transformation tests

### 5. Aggregate Initialization Reordering
**What**: Reorder `Data d = {1, 2, 3};` to match new member order
**Why P1**: Breaks compilation but easy to fix manually
**Tests failing**: Aggregate transformation tests

### 6. Advanced Dependency Handling
**What**: 3+ level chains, circular detection, diamond patterns
**Why P1**: Basic 2-level works, advanced is enhancement
**Tests failing**: Dependency family tests

### 7. Atomic File Operations
**What**: Backup creation, rollback on error
**Why P1**: Nice to have for safety
**Tests failing**: Atomicity family tests

### 8. Error Handling
**What**: Graceful degradation, clear error messages
**Why P1**: System works, just needs better errors
**Tests failing**: Error handling family tests

---

## P2 (Nice to Have)

### 9. Advanced Filtering
**What**: Wildcards, multiple patterns, struct name filtering
**Why P2**: Basic filtering works
**Tests failing**: Filtering family tests

### 10. Reporting
**What**: Progress bars, summary stats, verbosity
**Why P2**: System works, reporting is polish
**Tests failing**: Reporting family tests

### 11. Advanced Templates/Preprocessor
**What**: SFINAE, concepts, nested #ifdef
**Why P2**: Basic cases work
**Tests failing**: Extended template/preprocessor tests

---

## Actual P0 for Basic Functionality

**To make the system actually optimize structs**:

1. ✅ Extraction - DONE (MachoExtractor works)
2. ✅ Analysis - DONE (padding calculation works)
3. ✅ Planning - DONE (creates modifications)
4. ❌ **Transformation - CRITICAL** (doesn't actually modify source)
5. ✅ Output - DONE (generates patches)

**The ONE critical missing piece**: LineSwapTransformer needs to actually reorder members in the source file.

---

## Recommendation

**Start with**: Fix LineSwapTransformer to actually reorder struct members in source code.

**This will make**:
- ~30 transformation tests pass
- System actually functional end-to-end
- Real optimization happening

**Then**: Move to P1 features (constructor/aggregate rewriting, advanced dependencies, etc.)
