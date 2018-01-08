#!/bin/bash
set -e

# Also needs to be updated in Dockerfile when changed.
GROW_VERSION=`cat grow/VERSION`

echo "Building and Pushing Grow $GROW_VERSION to Docker Hub"

docker build --no-cache --build-arg grow_version=$GROW_VERSION \
  -t grow/base:$GROW_VERSION -t grow/base:latest \
  -t grow/baseimage:$GROW_VERSION -t grow/baseimage:latest .

docker run --rm=true --workdir=/tmp -i grow/base:$GROW_VERSION  \
  bash -c "git clone https://github.com/grow/grow.io.git && cd grow.io/ && grow install && grow build"

docker push grow/base:$GROW_VERSION
docker push grow/base:latest
# Old docker image support.
docker push grow/baseimage:$GROW_VERSION
docker push grow/baseimage:latest

docker build --no-cache --build-arg grow_version=$GROW_VERSION \
  -t grow/grow:$GROW_VERSION -t grow/grow:latest \
  -f Dockerfile.exec .

docker run grow/grow:$GROW_VERSION --version

docker push grow/grow:$GROW_VERSION
docker push grow/grow:latest
