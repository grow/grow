# Grow
[![Build Status](https://api.travis-ci.org/grow/grow.svg)](https://travis-ci.org/grow/grow) [![Downloads](https://img.shields.io/github/downloads/grow/grow/total.svg)](https://github.com/grow/grow/releases) [![https://img.shields.io/pypi/v/grow.svg](https://pypi.python.org/pypi/grow)] [![Slack](https://growsdk.herokuapp.com/badge.svg)](https://growsdk.herokuapp.com)

Grow is a declarative tool for rapidly building high-quality, maintainable
websites.

## Quick start

Install Grow quickly by downloading a version built for your system using the
commands below. [See docs from the documentation site](https://grow.io/docs/)
for full instructions.

```
curl https://install.growsdk.org | bash
grow init base base
cd base
grow run
```

You can alternatively `pip install grow` if you like.

## Developing Grow itself

Set up a development environment:

```
git clone git@github.com:grow/grow.git
make develop
```

Once your development environment is set up, run Grow:

```
./scripts/grow
```

Run tests:

```
make develop
make test
```

We try to set everything up for you automatically (including a `virtualenv`) in
the `make` commands, but if you are using Linux and something is not working,
you might try:

```
make develop-linux
make test
```
