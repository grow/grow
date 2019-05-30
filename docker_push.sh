#!/bin/bash
set -e

# Also needs to be updated in Dockerfile when changed.
GROW_VERSION=`cat grow/VERSION`

echo "Building and Pushing Grow $GROW_VERSION to Docker Hub"

# Ubuntu Base.
docker build --no-cache --build-arg grow_version=$GROW_VERSION \
  -t grow/base:$GROW_VERSION -t grow/base:latest \
  -t gcr.io/grow-prod/base:$GROW_VERSION -t gcr.io/grow-prod/base:latest \
  -t grow/baseimage:$GROW_VERSION -t grow/baseimage:latest .

docker run --rm=true --workdir=/tmp -i grow/base:$GROW_VERSION  \
  bash -c "git clone https://github.com/grow/grow.io.git && cd grow.io/ && grow install && grow build"

docker push grow/base:$GROW_VERSION
docker push grow/base:latest

# Legacy docker image support.
docker push grow/baseimage:$GROW_VERSION
docker push grow/baseimage:latest

# Google cloud registry.
docker push gcr.io/grow-prod/base:$GROW_VERSION
docker push gcr.io/grow-prod/base:latest

# Ubuntu Command.
docker build --no-cache --build-arg grow_version=$GROW_VERSION \
  -t grow/grow:$GROW_VERSION -t grow/grow:latest \
  -t gcr.io/grow-prod/grow:$GROW_VERSION -t gcr.io/grow-prod/grow:latest \
  -f Dockerfile.exec .

docker run grow/grow:$GROW_VERSION --version

docker push grow/grow:$GROW_VERSION
docker push grow/grow:latest

# Google cloud registry.
docker push gcr.io/grow-prod/grow:$GROW_VERSION
docker push gcr.io/grow-prod/grow:latest

# Alpine Base.
docker build --no-cache --build-arg grow_version=$GROW_VERSION \
  -t grow/base:$GROW_VERSION-alpine -t grow/base:alpine-latest \
  -f Dockerfile.alpine .

docker run --rm=true --workdir=/tmp -i grow/base:$GROW_VERSION-alpine  \
  bash -c "git clone https://github.com/grow/grow.io.git && cd grow.io/ && grow install && grow build"

docker push grow/base:$GROW_VERSION-alpine
docker push grow/base:alpine-latest

# Alpine Command.
docker build --no-cache --build-arg grow_version=$GROW_VERSION \
  -t grow/grow:$GROW_VERSION-alpine -t grow/grow:alpine-latest \
  -f Dockerfile.exec .

docker run grow/grow:$GROW_VERSION-alpine --version

docker push grow/grow:$GROW_VERSION-alpine
docker push grow/grow:alpine-latest
