#!/bin/bash
# Test paddington on a small scope

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_ROOT="/scratch/sim_reg7/users/ormagen/paddington/build_storm"
CACHE_DIR="$SCRIPT_DIR/.paddington_cache"
PATCH_DIR="$SCRIPT_DIR/patches_test"

echo "Testing paddington on small scope..."
rm -rf "$PATCH_DIR"

cd "$SCRIPT_DIR"

# Test on just a few files
python3 -m paddington optimize \
  "$BUILD_ROOT" \
  --patch-dir "$PATCH_DIR" \
  --cache-dir "$CACHE_DIR" \
  --use-pahole \
  --include "*/al_bitvec*.o" \
  --include "*/al_gdma*.o" \
  -vvv

echo ""
echo "Patches in $PATCH_DIR:"
ls -lh "$PATCH_DIR"/ 2>/dev/null || echo "No patches generated"
