# Build and Patch Application Instructions

## Current Situation (Jan 27, 2026)

### Paddington Status
- **Version**: v1.0-590patches (tagged)
- **Location**: `/scratch/sim_reg7/users/ormagen/paddington/tool_git_clone/paddington`
- **Branch**: `architecture-redesign`
- **Tests**: 510 passing, 1 skipped

### Model Repository
- **Location**: `/rdata/dub/verif/ormagen/model_4/model`
- **Branches**:
  - `paddington_2`: Clean baseline (no optimizations)
  - `paddington_apply_196`: 196 patches (old, without trivial preprocessor handling)
  - `paddington_fresh`: **369 patches (latest, template-safe)** ← Use this

### Latest Patches
- **Count**: 369 patches
- **Location**: `/tmp/patches_v2/`
- **Applied to**: `paddington_fresh` branch
- **Status**: Applied but build not verified due to build system issues

## What Works

### Paddington Features
✅ Template definition optimization (optimize `Foo` not `Foo<int>`)
✅ Trivial preprocessor handling (535 structs recovered)
✅ Static const member preservation
✅ Using statement handling (typedefs before usage)
✅ Constructor dependency detection
✅ Aggregate initialization detection
✅ Compilation data preservation (8453 structs with .cpp mappings)
✅ Workspace caching (14.5 min with cache vs 31 min without)
✅ Template instantiation deduplication (4858 duplicates eliminated)

### Optimizations Applied
- 369 patches generated
- 397 files modified
- ~30KB padding saved
- 89% transformation success rate
- 366 structs with static members safely skipped
- Templates with constructors skipped (avoid -Werror=reorder)

## Known Issues

### Build System
❌ `build_branch storm paddington_fresh` fails with git clone errors
- Error: "fatal: unable to parse commit"
- Likely caused by git gc running during commit
- Workaround attempted: Manual snapshot copy, but makefile paths incorrect

### Constructor Reordering
⚠️ Template classes with constructors cause -Werror=reorder warnings
- Different instantiations may need different member orders
- But they share the same constructor code
- Solution: Skip templates with constructors (implemented)

### Remaining Work
- Verify build passes with 369 patches
- Test performance improvement
- Fix remaining 52 transformation failures (11% failure rate)

## Build Command (Correct)

The proper build command is:
```tcsh
cd /scratch/sim_reg7/users/ormagen/paddington/optimized_builds/kiro_build_location
setsource 4
build_branch storm paddington_fresh
```

**What it does:**
1. Sets up environment with `setsource 4`
2. Clones model repo branch to `snapshot/` directory
3. Builds from snapshot
4. Creates output in `output/` directory

**Do NOT**:
- Manually create snapshot (build system does this)
- Use `--snapshot` flag (handled by build_branch alias)
- Use `--only-make` (skips necessary setup)

## Next Steps for Agent

1. **Verify build passes**:
   ```tcsh
   cd /scratch/sim_reg7/users/ormagen/paddington/optimized_builds/kiro_build_location
   rm -rf snapshot  # Clean old snapshot
   setsource 4
   build_branch storm paddington_fresh
   ```

2. **If build fails**:
   - Check error log in compile.log files
   - Create test that reproduces the issue
   - Fix in paddington
   - Regenerate patches
   - Reapply to paddington_fresh
   - Rebuild

3. **If build passes**:
   - Tag as v1.1-369patches-build-verified
   - Compare performance with baseline (paddington_2)
   - Document results

## Verification Checklist

After successful build, verify:
- [ ] Build completes with EXIT STATUS 0
- [ ] Snapshot contains optimized code (check al_counter.h members reordered)
- [ ] No -Werror=reorder warnings
- [ ] Pahole on built .o files shows optimized layouts
- [ ] Performance test shows improvement

## Summary for Next Agent

**Goal**: Get paddington_fresh branch to build successfully

**Current state**: 
- 369 patches generated and applied
- Optimizations verified in source
- Build system has git clone issues

**Action needed**:
- Fix build command or environment
- Verify build passes
- Document performance improvement
