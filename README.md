# Grow
[![Build Status](https://api.travis-ci.org/grow/grow.svg)](https://travis-ci.org/grow/grow) [![Downloads](https://img.shields.io/github/downloads/grow/grow/total.svg)](https://github.com/grow/grow/releases) [![PyPi](https://img.shields.io/pypi/v/grow.svg)](https://pypi.python.org/pypi/grow)
[![Gitter](https://badges.gitter.im/grow/grow.svg)](https://gitter.im/grow/grow)
[![Coverage Status](https://coveralls.io/repos/github/grow/grow/badge.svg?branch=master)](https://coveralls.io/github/grow/grow?branch=master)

Grow is a declarative tool for rapidly building, launching, and maintaining high-quality websites.

- Easy installation
- Jinja template engine
- Data-binding between YAML and views
- Data-driven site architecture
- Easy URL changes
- Flexible internationalization and translation
- Integration with external CMSes
- Fast builds

## Quick start

Run the commands below to start a server. The install script explains what
it does and pauses before each action.

```bash
curl https://install.grow.io | bash
grow init base base
cd base
grow run
```

- [Read quick start documentation](https://grow.io/docs/).

You can alternatively `pip install grow` if you like.

## Developing Grow itself

Set up a development environment:

```
git clone git@github.com:grow/grow.git
make develop
```

Once your development environment is set up, run Grow:

```bash
./scripts/grow
```

Then run tests:

```bash
make test
```

We try to set everything up for you automatically (including a `virtualenv`) in
the `make` commands, but if you are using Linux and something is not working,
you might try:

```bash
make develop-linux
make test
```
