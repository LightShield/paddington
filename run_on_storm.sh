#!/bin/bash
# Run paddington on storm build with path remapping

BUILD_ROOT="/scratch/sim_reg7/users/ormagen/paddington/build_storm"
SOURCE_ROOT="/Volumes/ANPA/model"

echo "Running paddington on storm build..."
echo "Build root: $BUILD_ROOT"
echo "Source root: $SOURCE_ROOT"
echo ""

python3 -m paddington optimize \
  "$BUILD_ROOT" \
  --remap-from "/scratch/sim_reg7/users/ormagen/paddington/build_storm/snapshot" \
  --remap-to "$SOURCE_ROOT" \
  --patch-dir ./patches \
  --exclude "*/regs/*" \
  -vv

echo ""
echo "Patches generated in ./patches/"
echo "Review and apply with: git apply patches/*.patch"
