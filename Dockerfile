FROM ubuntu
MAINTAINER Grow SDK Authors <hello@grow.io>

RUN apt-get update && apt-get install -y python python-pip git curl nodejs npm
RUN npm install -g bower
RUN npm install -g gulp
RUN \
  URL=https://raw.github.com/grow/pygrow/master/install.py \
  && scratch=$(mktemp -d -t tmp.0.0.46.XXXXXXXXX) || exit \
  && script_file=$scratch/install_growsdk.py \
  && curl -fsSL $URL > $script_file || exit \
  && chmod 775 $script_file \
  && python $script_file --force
