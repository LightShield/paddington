#!/bin/bash
# Run paddington on storm build (for remote execution)

BUILD_ROOT="/scratch/sim_reg7/users/ormagen/paddington/build_storm"

echo "Running paddington on storm build..."
echo "Build root: $BUILD_ROOT"
echo ""

python3 -m paddington optimize \
  "$BUILD_ROOT" \
  --patch-dir ./patches \
  --exclude "*/regs/*" \
  --exclude "*/third-party/*" \
  --exclude "*/tools/*" \
  --exclude "*/include/c++/*" \
  -vv

echo ""
echo "Patches generated in ./patches/"
echo "Review and apply with: git apply patches/*.patch"
