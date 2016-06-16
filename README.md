# Grow SDK [![Build Status](https://api.travis-ci.org/grow/grow.svg)](https://travis-ci.org/grow/grow) [![Downloads](https://img.shields.io/github/downloads/grow/grow/total.svg)](https://github.com/grow/grow/releases) [![Slack](https://growsdk.herokuapp.com/badge.svg)](https://growsdk.herokuapp.com)

A declarative, file-based tool for rapidly building maintainable websites.

## Quick start

```
# Download the packaged app to install.
curl https://install.growsdk.org | bash

# Initialize a site.
grow init codelab codelab
cd codelab

# Run the development server.
grow run
```

By using the installer from `install.growsdk.org`, you can leverage the autoupdater. If you'd prefer to build from source, see [installation alternatives](#installation-alternatives).

## Getting the code

For contributors, Grow includes a setup script to help set up development environment for running the tests and executing the command line tools. The setup script installs `pip`, `virtualenv`, and all of the required libraries.

    git clone git@github.com:grow/grow.git         # Clones this repo.
    cd grow
    ./scripts/setup                                # Runs setup script.

Once installed, you can:

    ./scripts/test                                 # Runs tests.
    ./scripts/grow                                 # Runs `grow` command line program.

#### Installation alternatives

    # Installs Grow in Python's site-packages directory.
    sudo pip install grow

    # Or, install Grow for a single user.
    pip install --user grow

    # If you have Grow already, upgrade it.
    pip install --upgrade [--user] grow

    # Or, build from source.
    git clone git@github.com:grow/grow.git
    cd grow
    pip install -r requirements.txt
    python setup.py install

#### Gotchas

`libyaml` must be installed on your system before installing PyYAML. On Mac, you can install libyaml using the following steps.

1. Install brew
2. `brew install libyaml`
3. From the virtualenv created in your repository, run `python -m easy_install pyyaml`

#### Linux gotchas (Ubuntu)

From a fresh system, you may need a few things to build a Grow release from scratch:

```bash
sudo apt-get install python python-pip build-essential python-all-dev zip \
  libc6 libyaml-dev libffi-dev libxml2-dev libxslt-dev libssl-dev zip
sudo pip install --upgrade pip
sudo pip install --upgrade six

sudo pip install grow
```

### Running tests

To run Grow's unit tests, run from the project's root directory:

    ./scripts/test                                # Runs unit tests.

## License

The Grow SDK is released under the MIT License and it is lovingly maintained by the [core team](https://github.com/grow/grow/blob/master/LICENSE). Our mission is to bring joy to building and launching high-quality web sites.
