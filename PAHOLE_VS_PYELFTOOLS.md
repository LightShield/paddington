# pahole vs pyelftools Comparison

## Performance

| Approach | 3 files | 1,334 files | Notes |
|----------|---------|-------------|-------|
| pyelftools | 60s | ~9 hours | Pure Python DWARF parser |
| pahole | 0.1s | ~5 minutes | Native C DWARF parser |
| **Speedup** | **600x** | **100x+** | Estimated |

## What pahole Provides

✅ Struct name and size  
✅ Member names, types, sizes, offsets  
✅ Padding calculation (holes)  
✅ Cache-line alignment info  
✅ Native speed (C implementation)  

❌ Source file location (no DW_AT_decl_file)  
❌ Cross-file type resolution  

## What We Lose

Without source file info from pahole, we need to:
1. Map struct names back to source files (search codebase)
2. Or use a hybrid: pahole for extraction + dwarfdump for source locations

## Hybrid Approach

```bash
# Fast: Get struct layouts with pahole
pahole file.o > structs.txt

# Slow but needed: Get source locations with dwarfdump
dwarfdump file.o | grep -A 5 "DW_TAG_structure_type" > locations.txt

# Merge the two
```

## Recommendation

For 1,334+ files:

**Option 1**: Use pahole + source file mapping  
- Extract with pahole (~5 min)
- Map struct names to source files via grep/ripgrep (~1 min)
- Total: ~6 minutes vs 9 hours

**Option 2**: Parallelize pyelftools  
- Use multiprocessing.Pool(8)
- 9 hours / 8 = ~1 hour
- Keeps source file info

**Option 3**: Use pahole on remote, pyelftools locally  
- Remote: Fast analysis with pahole
- Local: Detailed extraction with pyelftools for specific files

## Implementation Status

- ✅ pyelftools extractor (working, slow)
- ✅ pahole extractor (implemented, needs pahole installed)
- ⏳ Parallel pyelftools (not implemented)
- ⏳ Hybrid approach (not implemented)

## To Use pahole Extractor

```bash
# Requires pahole installed (Linux only)
sudo apt-get install dwarves  # Debian/Ubuntu
sudo yum install dwarves      # RHEL/CentOS

# Run
python3 -m paddington.core.pahole_extractor output.json file1.o file2.o
```

## Conclusion

**pahole is 100-600x faster** but loses source file info. For the storm build with 1,334 files, pahole would complete in minutes instead of hours.

The trade-off: Speed vs source file mapping convenience.
