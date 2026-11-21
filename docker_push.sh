#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
GROW_VERSION="$(uv run python -c "import importlib.metadata; print(importlib.metadata.version('grow'))")"

case "$TARGET" in
  gcr.io)
    echo "Building and pushing Grow ${GROW_VERSION} to gcr.io"
    echo "  To build and push to Docker Hub run './docker_push.sh'"
    echo "  To build and push to both run './docker_push.sh all'"
    ;;
  "")
    echo "Building and pushing Grow ${GROW_VERSION} to Docker Hub"
    echo "  To build and push to gcr.io run './docker_push.sh gcr.io'"
    echo "  To build and push to both run './docker_push.sh all'"
    ;;
  all)
    echo "Building and pushing Grow ${GROW_VERSION} to Docker Hub and gcr.io"
    ;;
  *)
    echo "Usage: $0 [gcr.io|all]" >&2
    exit 1
    ;;
esac

docker build \
  --no-cache \
  --build-arg "grow_version=grow==${GROW_VERSION}" \
  -t "grow/base:${GROW_VERSION}" -t "grow/base:latest" \
  -t "gcr.io/grow-prod/base:${GROW_VERSION}" -t "gcr.io/grow-prod/base:latest" \
  .

docker run \
  --rm \
  --workdir=/tmp \
  -i "grow/base:${GROW_VERSION}" \
  bash -ec "git clone https://github.com/grow/grow.dev.git && cd grow.dev/ && grow install && grow build"

if [[ "$TARGET" == "gcr.io" || "$TARGET" == "all" ]]; then
  docker push "gcr.io/grow-prod/base:${GROW_VERSION}"
  docker push "gcr.io/grow-prod/base:latest"
fi

if [[ "$TARGET" == "" || "$TARGET" == "all" ]]; then
  docker push "grow/base:${GROW_VERSION}"
  docker push "grow/base:latest"
fi
