FROM ubuntu
MAINTAINER Grow SDK Authors <hello@grow.io>
RUN apt-get update && \
  apt-get install -y \
  python \
  python-pip \
  libyaml-dev \
  git \
  nodejs \
  npm
RUN ln -s /usr/bin/nodejs /usr/bin/node
RUN npm install -g bower
RUN npm install -g gulp
RUN echo "{ \"allow_root\": true }" > $HOME/.bowerrc
RUN pip install git+git://github.com/grow/grow.git
ENTRYPOINT ["grow"]
