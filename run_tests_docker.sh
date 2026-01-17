#!/bin/bash
# Run tests in Docker (for macOS compatibility)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
IMAGE_NAME="paddington-test"

# Build image if it doesn't exist
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "Building Docker image for testing..."
    docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
fi

# Run tests in container
echo "Running tests in Docker container..."
docker run --rm \
    -v "$SCRIPT_DIR:/paddington" \
    -w /paddington \
    "$IMAGE_NAME" \
    python3 -m pytest tests/ "$@"
