#!/bin/bash
# Helper script to run pahole in Docker

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
IMAGE_NAME="paddington-pahole"

# Build image if it doesn't exist
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "Building Docker image with pahole..."
    docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
fi

# Run pahole in container
docker run --rm \
    -v "$SCRIPT_DIR:/paddington" \
    "$IMAGE_NAME" \
    pahole "$@"
