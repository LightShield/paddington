#!/bin/bash
# Run paddington on storm build (for remote execution)

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_ROOT="/scratch/sim_reg7/users/ormagen/paddington/build_storm"
CACHE_DIR="$SCRIPT_DIR/.paddington_cache"

echo "Running paddington on storm build..."
echo "Paddington dir: $SCRIPT_DIR"
echo "Build root: $BUILD_ROOT"
echo "Cache dir: $CACHE_DIR"
echo ""

cd "$SCRIPT_DIR"

python3 -m paddington optimize \
  "$BUILD_ROOT" \
  --patch-dir ./patches \
  --cache-dir "$CACHE_DIR" \
  --deduplicate \
  --exclude "*/regs/*" \
  --exclude "*/third-party/*" \
  --exclude "*/tools/*" \
  --exclude "*/include/c++/*" \
  -vvv

echo ""
echo "Patches generated in $SCRIPT_DIR/patches/"
echo "Review and apply with: git apply patches/*.patch"
echo ""
echo "Note: Cached data in $CACHE_DIR for faster re-runs"
