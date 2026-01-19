# Pahole Parser Patches - Application Instructions

## Location
`/scratch/sim_reg7/users/ormagen/paddington/pahole_patches/`

## Patches (5 total)

1. **0001-fix-Complete-pahole-parser-implementation-with-edge-.patch** (17KB)
   - Fix double-escaped regex patterns
   - Handle complex types with spaces
   - Handle inheritance, typedef, arrays
   - Add 15 comprehensive edge case tests

2. **0002-fix-Handle-multiple-structs-in-single-pahole-output.patch** (1.3KB)
   - Fix loop control to parse all structs in output
   - Was skipping every other struct

3. **0003-test-Verify-pahole-extractor-completeness-on-real-da.patch** (45KB)
   - Validation on real build_storm data
   - Test results and verification

4. **0004-fix-Distinguish-scope-from-inheritance-in-templates.patch** (2.3KB)
   - Fix false positive: std::pair detected as inheritance
   - Check for ' : ' (with spaces) not just ':'

5. **0005-feat-Add-union-support-with-automatic-ignore-marking.patch** (4.6KB)
   - Parse unions and mark with ignore=True
   - Handle unions without explicit size line

## To Apply

```bash
cd <paddington_repository>
git am /scratch/sim_reg7/users/ormagen/paddington/pahole_patches/*.patch
```

Or copy patches to another machine and apply:

```bash
scp -r /scratch/sim_reg7/users/ormagen/paddington/pahole_patches/ <destination>
cd <paddington_repo>
git am <path_to_patches>/*.patch
```

## Results After Applying

- ✅ 100% extraction rate (3960/3960 parseable structs on 100 files)
- ✅ All 16 edge case tests pass
- ✅ All 425 full test suite tests pass
- ✅ Unions correctly identified and marked
- ✅ al_report: 20/21 members extracted (vtable skipped - correct)
- ✅ Performance: ~6 minutes for 6822 files

## Validation Command

```bash
cd tool_git_clone/paddington
python3 -m pytest tests/pipeline/extraction/test_pahole_edge_cases.py -v
```

Expected: 16 passed
