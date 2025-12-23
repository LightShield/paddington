#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_ROOT="/scratch/sim_reg7/users/ormagen/paddington/build_storm"

cd "$SCRIPT_DIR"

python3 -m paddington optimize \
  "$BUILD_ROOT" \
  --patch-dir ./patches_trace \
  --use-pahole \
  --include "*/al_spis_pasw.o" \
  -vvvv
