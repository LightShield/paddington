#!/bin/bash
# Run paddington on storm build (for remote execution)

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_ROOT="/scratch/sim_reg7/users/ormagen/paddington/build_storm"

echo "Running paddington on storm build..."
echo "Paddington dir: $SCRIPT_DIR"
echo "Build root: $BUILD_ROOT"
echo ""

cd "$SCRIPT_DIR"

python3 -m paddington optimize \
  "$BUILD_ROOT" \
  --patch-dir ./patches \
  --exclude "*/regs/*" \
  --exclude "*/third-party/*" \
  --exclude "*/tools/*" \
  --exclude "*/include/c++/*" \
  -vv

echo ""
echo "Patches generated in $SCRIPT_DIR/patches/"
echo "Review and apply with: git apply patches/*.patch"
