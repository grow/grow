FROM ubuntu:jammy

ARG grow_version=grow

ENV DEBIAN_FRONTEND=noninteractive \
    TERM=xterm \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    NVM_DIR=/root/.nvm

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]

# Install base tools and configure APT repositories with signed-by keyrings.
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
  && install -m 0755 -d /etc/apt/keyrings \
  && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
  && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" \
    > /etc/apt/sources.list.d/nodesource.list \
  && curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg \
    | gpg --dearmor -o /etc/apt/keyrings/yarn.gpg \
  && echo "deb [signed-by=/etc/apt/keyrings/yarn.gpg] https://dl.yarnpkg.com/debian/ stable main" \
    > /etc/apt/sources.list.d/yarn.list \
  && curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /etc/apt/keyrings/google-cloud.gpg \
  && echo "deb [signed-by=/etc/apt/keyrings/google-cloud.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    google-cloud-cli \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    libyaml-dev \
    nodejs \
    openssh-client \
    python3 \
    python3-dev \
    python3-pip \
    ruby \
    ruby-dev \
    yarn \
    zip \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install nvm, global Node tools, and Ruby bundler.
RUN NVM_VERSION="$(curl -fsSL https://api.github.com/repos/nvm-sh/nvm/releases/latest | grep -oP '"tag_name": "\K[^"]+')" \
  && curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh" | bash \
  && npm install -g npm@latest \
  && yarn global add gulp \
  && yarn cache clean \
  && gem install --no-document bundler

# Install Grow.
RUN python3 -m pip install --no-cache-dir --upgrade pip wheel \
  && python3 -m pip install --no-cache-dir "${grow_version}"

# Confirm installed tool versions.
RUN source "${NVM_DIR}/nvm.sh" \
  && echo "Grow: $(grow --version)" \
  && echo "Python: $(python3 --version)" \
  && echo "Node: $(node -v)" \
  && echo "NPM: $(npm -v)" \
  && echo "NVM: $(nvm --version)" \
  && echo "Yarn: $(yarn --version)" \
  && echo "Gulp: $(gulp -v)" \
  && echo "GCloud: $(gcloud -v)" \
  && echo "Ruby: $(ruby -v)"
