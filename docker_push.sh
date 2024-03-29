#!/bin/bash
set -e

# Also needs to be updated in Dockerfile when changed.
GROW_VERSION=`python -c "import pkg_resources;print(pkg_resources.get_distribution('grow').version)"`

if [ "$1" == "gcr.io" ]; then
  echo "Building and Pushing Grow $GROW_VERSION to gcr.io"
  echo "  To build and push to Docker hub run './docker_push.sh'"
  echo "  To build and push to both run './docker_push.sh all'"
fi

if [ "$1" == "" ]; then
  echo "Building and Pushing Grow $GROW_VERSION to Docker Hub"
  echo "  To build and push to gcr.io run './docker_push.sh gcr.io'"
  echo "  To build and push to both run './docker_push.sh all'"
fi

# Ubuntu Base.
docker build \
  --no-cache \
  --build-arg grow_version=$GROW_VERSION \
  -t grow/base:$GROW_VERSION -t grow/base:latest \
  -t gcr.io/grow-prod/base:$GROW_VERSION -t gcr.io/grow-prod/base:latest \
  - < Dockerfile

docker run \
  --rm=true \
  --workdir=/tmp \
  -i grow/base:$GROW_VERSION  \
  bash -ec "git clone https://github.com/grow/grow.dev.git && cd grow.dev/ && grow install && grow build"

if [ "$1" == "gcr.io" ] || [ "$1" == "all" ]; then
  # Google cloud registry.
  docker push gcr.io/grow-prod/base:$GROW_VERSION
  docker push gcr.io/grow-prod/base:latest
fi

if [ "$1" == "" ] || [ "$1" == "all" ]; then
  # Docker Hub.
  docker push grow/base:$GROW_VERSION
  docker push grow/base:latest
fi
