# Grow

[![Circle CI](https://circleci.com/gh/grow/grow.png?style=shield)](https://circleci.com/gh/grow/grow)
[![Downloads](https://img.shields.io/github/downloads/grow/grow/total.svg)](https://github.com/grow/grow/releases)
[![PyPi](https://img.shields.io/pypi/v/grow.svg)](https://pypi.python.org/pypi/grow)
[![Code Coverage](https://codecov.io/gh/grow/grow/branch/master/graph/badge.svg)](https://codecov.io/gh/grow/grow)

Grow is a declarative tool for rapidly building, launching, and maintaining high-quality static HTML.

- Easy installation
- Jinja template engine
- Content managed in YAML and JSON files
- Data-binding between content and templates
- Configuration-based site architecture
- Easy URL changes
- Flexible internationalization and translation
- Integration with external CMSes
- Integration with Google Sheets
- Fast builds

## Quick start

One time only: install `Pipenv` and `libyaml`.

```bash
# On Mac with Homebrew (https://brew.sh/).
brew install pipenv libyaml

# On Ubuntu.
sudo apt install -y pipenv libyaml-dev

# On other distributions.
sudo apt install python-pip; pip install pipenv
```

Next: install and run Grow using a starter.

```bash
git clone https://github.com/grow/starter
cd starter
pipenv install
pipenv run grow install
pipenv run grow run
```

## Documentation

Visit https://grow.dev to read the documentation.
