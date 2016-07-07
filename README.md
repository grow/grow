# Grow
[![Build Status](https://api.travis-ci.org/grow/grow.svg)](https://travis-ci.org/grow/grow) [![Downloads](https://img.shields.io/github/downloads/grow/grow/total.svg)](https://github.com/grow/grow/releases) [![PyPi](https://img.shields.io/pypi/v/grow.svg)](https://pypi.python.org/pypi/grow)] [![Slack](https://growsdk.herokuapp.com/badge.svg)](https://growsdk.herokuapp.com)

Grow is a declarative tool for rapidly building high-quality, maintainable
websites.

## Quick start

Run the commands below to start a server. The install script explains what
it does and pauses before each action.

```
curl https://install.growsdk.org | bash
grow init base base
cd base
grow run
```

- [Read quick start documentation](https://grow.io/docs/).
- You can alternatively `pip install grow` if you like.

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

Then run tests:

```
make test
```

We try to set everything up for you automatically (including a `virtualenv`) in
the `make` commands, but if you are using Linux and something is not working,
you might try:

```
make develop-linux
make test
```
